"""Command line entry point for file_flag."""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

from .config import Config
from . import sampler
from . import pipeline
from . import reporting


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="file_flag",
        description="Sample a document repository and flag PDFs containing "
                    "valid TFNs / PII / government identifiers.",
    )
    p.add_argument("repository", help="Root folder of the document repository")
    p.add_argument("-c", "--config", help="Path to YAML config", default=None)
    p.add_argument("--percent", type=float, default=None,
                   help="Override sampling.percent")
    p.add_argument("--threads", type=int, default=None,
                   help="Worker process count (legacy processing.threads setting)")
    p.add_argument("--flagged-dir", default=None,
                   help="Override output.flagged_dir")
    p.add_argument("--report", default=None, help="Override output.report path")
    p.add_argument("--dry-run", action="store_true",
                   help="Only print the sampling plan; do not scan")
    p.add_argument("--no-mask", action="store_true",
                   help="Write raw (unmasked) values into the report")
    p.add_argument("-v", "--verbose", action="store_true")
    return p


def _apply_overrides(cfg: Config, args) -> None:
    if args.percent is not None:
        cfg.sampling["percent"] = args.percent
    if args.threads is not None:
        cfg.processing["threads"] = args.threads
    if args.flagged_dir is not None:
        cfg.output["flagged_dir"] = args.flagged_dir
    if args.report is not None:
        cfg.output["report"] = args.report
    if args.no_mask:
        cfg.output["mask_values"] = False


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    cfg = Config.load(args.config)
    _apply_overrides(cfg, args)

    repo_root = Path(args.repository)
    files, stats = sampler.plan(
        repo_root,
        percent=cfg.sampling["percent"],
        strategy=cfg.sampling["strategy"],
        seed=cfg.sampling["seed"],
        min_per_folder=cfg.sampling["min_per_folder"],
    )

    print(f"Discovered {stats['total_files']} PDFs across {stats['folders']} "
          f"folders; sampling {stats['sampled_files']} "
          f"({stats['percent']}%, {stats['strategy']}).")

    if args.dry_run:
        for f in files:
            print(f"  {f}")
        return 0

    if not files:
        print("No files to scan.")
        return 0

    start = time.time()

    def progress(done, total, result):
        flag = "FLAG" if result.flagged else "ok  "
        print(f"[{done}/{total}] {flag} {result.path}")

    results = pipeline.run(files, repo_root, cfg, progress=progress)

    reporting.print_summary(results, stats)
    report_path = cfg.output["report"]
    reporting.write_report(results, report_path,
                           mask=cfg.output.get("mask_values", True),
                           extra=stats)
    print(f"\nReport written to {report_path}")
    print(f"Flagged files copied to {cfg.output['flagged_dir']} "
          f"(mode={cfg.output['copy_mode']})")
    print(f"Elapsed: {time.time() - start:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
