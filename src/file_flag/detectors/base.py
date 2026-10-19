"""Base types shared by all detectors."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Finding:
    """A single sensitive item located inside a document."""

    detector: str            # e.g. "tfn"
    kind: str                # e.g. "tfn", "email", "medicare"
    raw_value: str           # the actual matched value (sensitive!)
    page: int = 0            # 1-based page number, 0 if unknown
    context: str = ""        # surrounding text snippet
    confidence: float = 1.0  # 0..1
    redacted: bool = False   # value sits under a redaction mark but is still readable
    via_ocr: bool = False    # value was recovered through OCR of a scanned page

    def masked_value(self) -> str:
        """Return the value with the middle obscured for safe reporting."""
        v = self.raw_value
        if len(v) <= 4:
            return "*" * len(v)
        keep = 2
        return v[:keep] + ("*" * (len(v) - 2 * keep)) + v[-keep:]

    def to_dict(self, mask: bool = True) -> dict[str, Any]:
        d = asdict(self)
        d["value"] = self.masked_value() if mask else self.raw_value
        d.pop("raw_value")
        if mask:
            # Context can repeat this value or contain other sensitive records.
            d["context"] = "[REDACTED]" if self.context else ""
        return d


@dataclass
class Detector(ABC):
    """A detector inspects extracted text and yields :class:`Finding` objects.

    Detectors are deliberately stateless with respect to a single document so
    each worker process can reuse one detector set.
    """

    name: str = "detector"
    options: dict[str, Any] = field(default_factory=dict)

    @abstractmethod
    def detect(self, text: str, page: int = 0) -> list[Finding]:
        """Return findings for a block of text belonging to ``page``."""
        raise NotImplementedError
