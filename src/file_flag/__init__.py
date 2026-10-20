"""file_flag: stratified sampling + process-isolated TFN/PII/GRI detection in PDFs."""
from __future__ import annotations

__version__ = "0.1.2"

from .config import Config
from .scanner import scan_file, ScanResult
from .detectors import build_detectors, Finding

__all__ = ["Config", "scan_file", "ScanResult", "build_detectors", "Finding",
           "__version__"]
