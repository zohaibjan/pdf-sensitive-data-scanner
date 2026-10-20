"""Additional identifier checks (GRI): Medicare numbers and ABNs.

Both carry published checksums so we can flag genuine identifiers and skip
random number sequences.
"""
from __future__ import annotations

import re

from .base import Detector, Finding

# Medicare: 10 (or 11 incl. issue number) digits, commonly grouped 4-5-1.
_MEDICARE = re.compile(r"(?<!\d)(\d{4})[ -]?(\d{5})[ -]?(\d)(?:[ -]?(\d))?(?!\d)")
# ABN: 11 digits, commonly grouped 2-3-3-3.
_ABN = re.compile(r"(?<!\d)(\d{2})[ -]?(\d{3})[ -]?(\d{3})[ -]?(\d{3})(?!\d)")

_MEDICARE_WEIGHTS = (1, 3, 7, 9, 1, 3, 7, 9)
_ABN_WEIGHTS = (10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19)


def is_valid_medicare(digits: str) -> bool:
    if len(digits) < 9 or not digits[:9].isdigit():
        return False
    base, check = digits[:8], int(digits[8])
    return sum(int(d) * w for d, w in zip(base, _MEDICARE_WEIGHTS)) % 10 == check


def is_valid_abn(digits: str) -> bool:
    if len(digits) != 11 or not digits.isdigit():
        return False
    nums = [int(d) for d in digits]
    nums[0] -= 1
    return sum(n * w for n, w in zip(nums, _ABN_WEIGHTS)) % 89 == 0


class GRIDetector(Detector):
    """Detect Medicare numbers and ABNs. ``options['types']`` restricts which run."""

    _VALIDATORS = {"medicare": is_valid_medicare, "abn": is_valid_abn}

    def __init__(self, options: dict | None = None):
        super().__init__(name="gri", options=options or {})
        types = self.options.get("types") or list(self._VALIDATORS)
        self.types = [t for t in types if t in self._VALIDATORS]

    def detect(self, text: str, page: int = 0) -> list[Finding]:
        findings: list[Finding] = []
        if "medicare" in self.types:
            findings += self._scan(text, page, _MEDICARE, "medicare", is_valid_medicare)
        if "abn" in self.types:
            findings += self._scan(text, page, _ABN, "abn", is_valid_abn)
        return findings

    def _scan(self, text, page, pattern, kind, validator):
        out: list[Finding] = []
        for m in pattern.finditer(text):
            digits = "".join(g for g in m.groups() if g)
            if not validator(digits):
                continue
            start, end = m.start(), m.end()
            context = text[max(0, start - 30): end + 30].replace("\n", " ").strip()
            out.append(
                Finding(detector=self.name, kind=kind, raw_value=m.group(0),
                        page=page, context=context)
            )
        return out
