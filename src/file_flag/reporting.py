"""Summarise and persist scan results."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .scanner import ScanResult


def summarise(results: list[ScanResult]) -> dict:
    flagged = [r for r in results if r.flagged]
    errors = [r for r in results if r.error]
    kinds = Counter(f.kind for r in flagged for f in r.findings)
    return {
        "scanned": len(results),
        "flagged": len(flagged),
        "errors": len(errors),
        "used_ocr": sum(1 for r in results if r.used_ocr),
        "findings_by_kind": dict(kinds),
    }


def write_report(results: list[ScanResult], path: str | Path,
                 mask: bool = True, extra: dict | None = None) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "summary": summarise(results),
        "sampling": extra or {},
        "results": [r.to_dict(mask=mask) for r in results if r.flagged or r.error],
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)


def print_summary(results: list[ScanResult], stats: dict | None = None) -> None:
    s = summarise(results)
    print("\n=== Scan summary ===")
    if stats:
        print(f"Repository : {stats.get('total_files')} files in "
              f"{stats.get('folders')} folders")
        print(f"Sampled    : {stats.get('sampled_files')} "
              f"({stats.get('percent')}%, {stats.get('strategy')})")
    print(f"Scanned    : {s['scanned']}")
    print(f"Flagged    : {s['flagged']}")
    print(f"Via OCR    : {s['used_ocr']}")
    print(f"Errors     : {s['errors']}")
    if s["findings_by_kind"]:
        print("Findings by kind:")
        for kind, n in sorted(s["findings_by_kind"].items()):
            print(f"  - {kind}: {n}")
