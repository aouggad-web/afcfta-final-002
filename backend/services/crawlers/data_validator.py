"""
Data Validator – Quality assurance for extracted DZA tariff data.

Responsibilities:
- Validate tariff line schema integrity
- Compute confidence scores
- Detect missing critical components (VAT, national codes)
- Run dataset-level integrity checks
- Export a validation report
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Line-level validation
# ---------------------------------------------------------------------------

_REQUIRED_FIELDS = ("hs6_code", "description_fr")
_CRITICAL_TAXES = ("dd", "tva")


def validate_line(line: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a single tariff line.

    Returns:
        (is_valid, list_of_issues)
    """
    issues: List[str] = []

    for field in _REQUIRED_FIELDS:
        if not line.get(field):
            issues.append(f"Missing required field: {field}")

    taxes = line.get("taxes", {})
    for tax in _CRITICAL_TAXES:
        if taxes.get(tax) is None:
            issues.append(f"Missing critical tax: {tax}")

    # HS6 format
    hs6 = line.get("hs6_code", "")
    if hs6 and (not hs6.isdigit() or len(hs6) != 6):
        issues.append(f"Invalid hs6_code format: {hs6!r}")

    return (len(issues) == 0, issues)


def score_line(line: Dict[str, Any]) -> float:
    """Return a confidence score [0, 1] for a tariff line."""
    score = 0.0
    taxes = line.get("taxes", {})

    if line.get("hs10_code") and len(re.sub(r"\D", "", line["hs10_code"])) >= 10:
        score += 0.30
    elif line.get("hs6_code"):
        score += 0.15

    if taxes.get("dd") is not None:
        score += 0.30
    if taxes.get("tva") is not None:
        score += 0.20
    if line.get("description_fr"):
        score += 0.10
    if taxes.get("prct") is not None or taxes.get("tcs") is not None:
        score += 0.10

    return min(score, 1.0)


# ---------------------------------------------------------------------------
# Dataset-level validation
# ---------------------------------------------------------------------------

class DataValidator:
    """Validates an entire dataset of DZA tariff lines."""

    def __init__(
        self,
        min_confidence_score: float = 0.5,
        min_vat_coverage: float = 0.5,
        min_hs10_coverage: float = 0.3,
        strict_mode: bool = False,
    ) -> None:
        self.min_confidence_score = min_confidence_score
        self.min_vat_coverage = min_vat_coverage
        self.min_hs10_coverage = min_hs10_coverage
        self.strict_mode = strict_mode

    def validate(self, lines: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run full validation on a list of tariff lines.

        Returns a validation report dictionary.
        """
        if not lines:
            return self._empty_report("No tariff lines to validate")

        total = len(lines)
        valid_count = 0
        low_confidence = 0
        missing_vat = 0
        missing_hs10 = 0
        line_issues: List[Dict[str, Any]] = []

        for idx, line in enumerate(lines):
            is_valid, issues = validate_line(line)
            conf = line.get("confidence_score", score_line(line))

            if is_valid:
                valid_count += 1
            else:
                line_issues.append({"index": idx, "hs6": line.get("hs6_code", ""), "issues": issues})

            if conf < self.min_confidence_score:
                low_confidence += 1

            taxes = line.get("taxes", {})
            if taxes.get("tva") is None:
                missing_vat += 1

            hs10 = line.get("hs10_code", "")
            if not hs10 or len(re.sub(r"\D", "", hs10)) < 10:
                missing_hs10 += 1

        vat_coverage = (total - missing_vat) / total
        hs10_coverage = (total - missing_hs10) / total
        valid_pct = valid_count / total

        passed = (
            vat_coverage >= self.min_vat_coverage
            and hs10_coverage >= self.min_hs10_coverage
        )
        if self.strict_mode:
            passed = passed and valid_pct >= 0.9

        report: Dict[str, Any] = {
            "validated_at": datetime.now(timezone.utc).isoformat(),
            "total_lines": total,
            "valid_lines": valid_count,
            "valid_pct": round(valid_pct * 100, 2),
            "low_confidence_lines": low_confidence,
            "vat_coverage_pct": round(vat_coverage * 100, 2),
            "hs10_coverage_pct": round(hs10_coverage * 100, 2),
            "passed": passed,
            "thresholds": {
                "min_vat_coverage_pct": self.min_vat_coverage * 100,
                "min_hs10_coverage_pct": self.min_hs10_coverage * 100,
                "min_confidence_score": self.min_confidence_score,
                "strict_mode": self.strict_mode,
            },
            "sample_issues": line_issues[:20],
        }
        return report

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _empty_report(reason: str) -> Dict[str, Any]:
        return {
            "validated_at": datetime.now(timezone.utc).isoformat(),
            "total_lines": 0,
            "valid_lines": 0,
            "valid_pct": 0.0,
            "low_confidence_lines": 0,
            "vat_coverage_pct": 0.0,
            "hs10_coverage_pct": 0.0,
            "passed": False,
            "reason": reason,
            "thresholds": {},
            "sample_issues": [],
        }
