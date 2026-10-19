"""Process-isolated orchestration: sample -> scan -> flag -> report."""
from __future__ import annotations

import logging
import shutil
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from pathlib import Path

from .config import Config
from .detectors import build_detectors
from .scanner import ScanResult, scan_file

log = logging.getLogger(__name__)


def _route_flagged(result: ScanResult, repo_root: Path, out_cfg: dict) -> None:
    """Copy or move a flagged file into the output directory."""
    mode = out_cfg.get("copy_mode", "copy")
    if mode == "none":
        return
    dest_dir = Path(out_cfg["flagged_dir"])
    if out_cfg.get("preserve_tree", True):
        try:
            rel = result.path.resolve().relative_to(repo_root.resolve())
            dest = dest_dir / rel
        except ValueError:
            dest = dest_dir / result.path.name
    else:
        dest = dest_dir / result.path.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    if mode == "move":
        shutil.move(str(result.path), str(dest))
    else:
        shutil.copy2(str(result.path), str(dest))


_WORKER_DETECTORS = None


def _init_worker(detector_config: dict) -> None:
    global _WORKER_DETECTORS
    _WORKER_DETECTORS = build_detectors(detector_config)


def _scan_worker(path: Path, ocr_cfg: dict) -> ScanResult:
    return scan_file(path, _WORKER_DETECTORS, ocr_cfg)


def run(files: list[Path], repo_root: Path, config: Config,
        progress=None) -> list[ScanResult]:
    """Scan PDFs in isolated processes; route files and report progress in parent.

    ``processing.threads`` is retained as a compatibility setting for the number
    of worker processes. At most twice that many tasks are pending, avoiding a
    future object for every PDF in large repositories. Results remain in memory.
    """
    workers = int(config.processing.get("threads", 8))
    if workers < 1:
        raise ValueError("processing.threads must be >= 1")
    results: list[ScanResult] = []

    def collect(result):
        if result.flagged:
            try:
                _route_flagged(result, repo_root, config.output)
            except Exception as exc:
                log.warning("Failed to route %s: %s", result.path, exc)
        results.append(result)
        if progress:
            progress(len(results), len(files), result)

    if not files:
        return results
    if workers == 1:
        detectors = build_detectors(config.detectors)
        for path in files:
            collect(scan_file(path, detectors, config.ocr))
        return results

    # Spawn never inherits an open MuPDF document or the parent's native state.
    with ProcessPoolExecutor(max_workers=workers,
            mp_context=multiprocessing.get_context("spawn"),
            initializer=_init_worker, initargs=(config.detectors,)) as pool:
        source = iter(files)
        pending = {}
        def replenish():
            while len(pending) < workers * 2:
                path = next(source, None)
                if path is None:
                    break
                pending[pool.submit(_scan_worker, path, config.ocr)] = path
        replenish()
        while pending:
            completed, _ = wait(pending, return_when=FIRST_COMPLETED)
            for future in completed:
                path = pending.pop(future)
                try:
                    result = future.result()
                except Exception as exc:
                    result = ScanResult(path=Path(path), error=f"worker failed: {exc}")
                collect(result)
            replenish()
    return results
