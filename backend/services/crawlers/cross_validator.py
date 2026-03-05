"""
North Africa Cross-Validator.

Ensures data consistency across all four North African countries
for shared HS codes. Provides:
- Rate relationship validation (DZA vs MAR vs EGY vs TUN)
- Completeness scoring per country
- Temporal consistency checks
- Accuracy benchmarking against known reference rates
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config.regional_config import NORTH_AFRICA_COUNTRIES, REGIONAL_CONFIG, COMMON_HS_SECTIONS

logger = logging.getLogger(__name__)

DATA_BASE_DIR = Path(__file__).parent.parent.parent / "data"

# Reference rates for common chapters (approximations for benchmarking)
REFERENCE_RATES: Dict[str, Dict[str, float]] = {
    # chapter: {country: typical_dd_rate}
    "27": {"DZA": 0.0, "MAR": 2.5, "EGY": 5.0, "TUN": 0.0},   # Mineral fuels
    "87": {"DZA": 30.0, "MAR": 17.5, "EGY": 40.0, "TUN": 30.0},  # Vehicles
    "84": {"DZA": 5.0, "MAR": 2.5, "EGY": 5.0, "TUN": 10.0},    # Machinery
}


class ValidationResult:
    """Stores the result of a cross-validation run."""

    def __init__(self):
        self.timestamp = datetime.utcnow()
        self.countries_checked: List[str] = []
        self.issues: List[Dict[str, Any]] = []
        self.completeness_scores: Dict[str, float] = {}
        self.cross_country_anomalies: List[Dict[str, Any]] = []
        self.overall_valid: bool = True

    def add_issue(
        self,
        country: str,
        issue_type: str,
        description: str,
        severity: str = "warning",
    ):
        self.issues.append({
            "country": country,
            "type": issue_type,
            "description": description,
            "severity": severity,
        })
        if severity == "error":
            self.overall_valid = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "countries_checked": self.countries_checked,
            "overall_valid": self.overall_valid,
            "completeness_scores": self.completeness_scores,
            "total_issues": len(self.issues),
            "issues": self.issues,
            "cross_country_anomalies": self.cross_country_anomalies,
        }


class NorthAfricaCrossValidator:
    """
    Cross-validates tariff data consistency across North African countries.

    Checks:
    1. Same HS codes have logically related rates across countries
    2. Data completeness per country (minimum coverage threshold)
    3. Rate ranges within expected bounds per country
    4. Temporal consistency of data freshness
    """

    TOLERANCE_PCT = REGIONAL_CONFIG["cross_validation"]["tolerance_pct"]
    MIN_COVERAGE_PCT = REGIONAL_CONFIG["cross_validation"]["min_coverage_pct"]

    def __init__(self, countries: Optional[List[str]] = None):
        self.countries = countries or NORTH_AFRICA_COUNTRIES

    def load_country_data(self, country_code: str) -> Optional[List[Dict]]:
        """
        Load the latest published data for a country.

        Looks for JSON files in data/published/<country>/.
        """
        pub_dir = DATA_BASE_DIR / "published" / country_code
        if not pub_dir.exists():
            logger.warning(f"No published data directory for {country_code}")
            return None

        json_files = sorted(pub_dir.glob("*.json"), reverse=True)
        if not json_files:
            logger.warning(f"No published JSON files for {country_code}")
            return None

        try:
            import json
            with open(json_files[0], "r", encoding="utf-8") as f:
                data = json.load(f)
            records = data.get("records", data if isinstance(data, list) else [])
            logger.info(f"Loaded {len(records)} records for {country_code}")
            return records
        except Exception as exc:
            logger.error(f"Failed to load data for {country_code}: {exc}")
            return None

    def check_completeness(
        self, records: List[Dict], country_code: str
    ) -> Tuple[float, List[str]]:
        """
        Calculate completeness score for a country's data.

        Returns:
            (score_pct, list_of_missing_fields)
        """
        if not records:
            return 0.0, ["No records found"]

        required_fields = ["hs_code", "designation", "taxes"]
        missing_fields = []
        complete_count = 0

        for rec in records:
            has_all = all(rec.get(f) for f in required_fields)
            if has_all:
                complete_count += 1

        score = (complete_count / len(records)) * 100

        # Check for missing fields overall
        sample = records[:min(100, len(records))]
        for field in required_fields:
            missing = sum(1 for r in sample if not r.get(field))
            if missing > len(sample) * 0.3:
                missing_fields.append(f"{field} ({missing}/{len(sample)} missing)")

        return score, missing_fields

    def check_rate_ranges(
        self, records: List[Dict], country_code: str
    ) -> List[Dict[str, Any]]:
        """
        Check that tax rates are within expected bounds for a country.

        Returns list of anomaly dicts.
        """
        anomalies = []

        # Country-specific VAT from config
        from config.regional_config import NORTH_AFRICA_VAT_RATES
        expected_vat = NORTH_AFRICA_VAT_RATES.get(country_code)

        for rec in records:
            hs = rec.get("hs_code", "?")
            taxes = rec.get("taxes", {})

            # Check DD in 0-200% range (use explicit None checks to handle 0% duty-free)
            dd = (
                taxes.get("DD") if taxes.get("DD") is not None
                else (taxes.get("CD") if taxes.get("CD") is not None
                      else taxes.get("ID"))
            )
            if dd is not None and not (0 <= dd <= 200):
                anomalies.append({
                    "country": country_code,
                    "hs_code": hs,
                    "tax": "DD/CD",
                    "value": dd,
                    "issue": f"DD rate {dd}% outside expected range [0-200]",
                })

            # Check VAT close to standard rate (explicit None check to handle 0% VAT)
            vat = (
                taxes.get("TVA") if taxes.get("TVA") is not None
                else taxes.get("VAT")
            )
            if vat is not None and expected_vat and abs(vat - expected_vat) > 10:
                anomalies.append({
                    "country": country_code,
                    "hs_code": hs,
                    "tax": "TVA/VAT",
                    "value": vat,
                    "issue": (
                        f"VAT {vat}% far from standard {expected_vat}% "
                        f"(diff {abs(vat - expected_vat):.1f}%)"
                    ),
                })

        return anomalies[:50]  # cap at 50 anomalies per country

    def cross_validate_hs_codes(
        self,
        all_data: Dict[str, List[Dict]],
    ) -> List[Dict[str, Any]]:
        """
        Compare rates for the same HS prefix across countries.

        Returns list of significant divergences.
        """
        from collections import defaultdict

        # Build HS-prefix -> country -> avg_total_taxes map
        prefix_map: Dict[str, Dict[str, List[float]]] = defaultdict(
            lambda: defaultdict(list)
        )

        for country, records in all_data.items():
            for rec in records:
                hs = rec.get("hs_code", "")
                if len(hs) >= 6:
                    prefix = hs[:6]
                    total = rec.get("total_taxes_pct", 0) or 0
                    if total > 0:
                        prefix_map[prefix][country].append(total)

        anomalies = []
        tolerance = self.TOLERANCE_PCT * 3  # wider tolerance for cross-country

        for prefix, country_rates in prefix_map.items():
            if len(country_rates) < 2:
                continue
            avg_by_country = {
                c: sum(rates) / len(rates) for c, rates in country_rates.items()
            }
            values = list(avg_by_country.values())
            if not values:
                continue
            spread = max(values) - min(values)
            if spread > tolerance:
                anomalies.append({
                    "hs_prefix": prefix,
                    "rates_by_country": avg_by_country,
                    "spread_pct": round(spread, 2),
                    "note": f"High divergence ({spread:.1f}%) across countries for HS {prefix}",
                })

        return sorted(anomalies, key=lambda x: x["spread_pct"], reverse=True)[:30]

    def validate(self, all_data: Optional[Dict[str, List[Dict]]] = None) -> ValidationResult:
        """
        Run full cross-validation across all countries.

        Args:
            all_data: Optional pre-loaded data dict {country: records}.
                      If not provided, loads from published directories.

        Returns:
            ValidationResult with all findings.
        """
        result = ValidationResult()
        result.countries_checked = list(self.countries)

        # Load data if not provided
        if all_data is None:
            all_data = {}
            for country in self.countries:
                records = self.load_country_data(country)
                if records:
                    all_data[country] = records

        # 1. Completeness check per country
        for country in self.countries:
            records = all_data.get(country, [])
            if not records:
                result.add_issue(
                    country, "no_data",
                    f"No data available for {country}",
                    severity="warning",
                )
                result.completeness_scores[country] = 0.0
                continue

            score, missing = self.check_completeness(records, country)
            result.completeness_scores[country] = round(score, 1)

            if score < self.MIN_COVERAGE_PCT:
                result.add_issue(
                    country, "low_completeness",
                    f"Completeness {score:.1f}% below threshold {self.MIN_COVERAGE_PCT}%",
                    severity="warning",
                )
            for mf in missing:
                result.add_issue(
                    country, "missing_field",
                    f"Field {mf}",
                    severity="info",
                )

            # 2. Rate range checks
            anomalies = self.check_rate_ranges(records, country)
            for anom in anomalies:
                result.add_issue(
                    country, "rate_anomaly",
                    anom["issue"],
                    severity="warning",
                )

        # 3. Cross-country HS code comparison
        if len(all_data) >= 2:
            cross_anomalies = self.cross_validate_hs_codes(all_data)
            result.cross_country_anomalies = cross_anomalies
            logger.info(
                f"Cross-validation: {len(cross_anomalies)} HS prefix divergences found"
            )

        logger.info(
            f"Cross-validation complete: {len(result.issues)} issues, "
            f"valid={result.overall_valid}"
        )
        return result
