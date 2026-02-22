"""
Consistency validator for AfCFTA customs data.

Performs cross-validation checks including:
- Historical data comparison
- Regional consistency analysis
- Reference data validation
- Change detection
"""

import logging
from typing import Dict, Any, List, Optional, Union, Set
from datetime import datetime, timedelta
from statistics import mean, median, stdev
from collections import defaultdict

from .base_validator import BaseValidator, ValidationResult, ValidationSeverity


logger = logging.getLogger(__name__)


class ConsistencyValidator(BaseValidator):
    """
    Validator for cross-validation and consistency checks.
    
    Performs:
    - Historical data comparison (detect changes over time)
    - Regional consistency (similar countries should have similar rates)
    - Reference data validation (compare against known data)
    - Sudden change detection (rate jumps)
    - Cross-field consistency
    """
    
    # Regional groupings for consistency checks
    REGIONAL_GROUPS = {
        'ECOWAS': ['BEN', 'BFA', 'CIV', 'CPV', 'GMB', 'GHA', 'GIN', 'GNB', 
                   'LBR', 'MLI', 'NER', 'NGA', 'SEN', 'SLE', 'TGO'],
        'EAC': ['BDI', 'KEN', 'RWA', 'SSD', 'TZA', 'UGA'],
        'SADC': ['AGO', 'BWA', 'COM', 'COD', 'LSO', 'MDG', 'MWI', 'MUS', 
                 'MOZ', 'NAM', 'SYC', 'ZAF', 'SWZ', 'TZA', 'ZMB', 'ZWE'],
        'MAGHREB': ['DZA', 'LBY', 'MRT', 'MAR', 'TUN'],
        'CEMAC': ['CMR', 'CAF', 'TCD', 'COG', 'GNQ', 'GAB'],
    }
    
    # Typical tariff rate ranges by region (for reference)
    EXPECTED_RATE_RANGES = {
        'ECOWAS': (0, 35),
        'EAC': (0, 25),
        'SADC': (0, 40),
        'MAGHREB': (0, 45),
        'CEMAC': (0, 30),
        'OTHER': (0, 50),
    }
    
    # Change detection thresholds
    MAX_RATE_CHANGE_PERCENTAGE = 50.0  # Max 50% change from historical
    MAX_ABSOLUTE_RATE_CHANGE = 20.0  # Max 20 percentage point change
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize consistency validator.
        
        Args:
            config: Optional configuration with:
                - historical_data: Dict[str, Any] - Previous data for comparison
                - reference_data: Dict[str, Any] - Known reference data
                - regional_groups: Dict[str, List[str]] - Custom regional groupings
                - max_rate_change: float - Maximum allowed rate change %
                - enable_regional_checks: bool - Enable regional consistency checks
                - enable_historical_checks: bool - Enable historical comparison
        """
        super().__init__(config)
        self.historical_data = config.get('historical_data', {}) if config else {}
        self.reference_data = config.get('reference_data', {}) if config else {}
        self.regional_groups = config.get('regional_groups', self.REGIONAL_GROUPS) if config else self.REGIONAL_GROUPS
        self.max_rate_change = config.get('max_rate_change', self.MAX_RATE_CHANGE_PERCENTAGE) if config else self.MAX_RATE_CHANGE_PERCENTAGE
        self.enable_regional = config.get('enable_regional_checks', True) if config else True
        self.enable_historical = config.get('enable_historical_checks', True) if config else True
    
    async def validate(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> ValidationResult:
        """
        Validate data consistency.
        
        Args:
            data: Data to validate. Can be:
                - List of records
                - Dict with 'records', 'country_code', and metadata
        
        Returns:
            ValidationResult with consistency analysis
        """
        start_time = datetime.utcnow()
        self._reset_state()
        
        # Extract data components
        records, country_code, metadata = self._extract_data_components(data)
        
        if not records:
            self._add_check("has_data")
            self._mark_failed("has_data")
            self._add_error("No data provided for consistency validation")
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            return self._build_result(details={"records_count": 0}, duration_ms=duration_ms)
        
        # Run consistency checks
        self._check_internal_consistency(records)
        
        if self.enable_historical and self.historical_data:
            self._check_historical_consistency(records, country_code, metadata)
        
        if self.enable_regional and country_code:
            self._check_regional_consistency(records, country_code)
        
        if self.reference_data:
            self._check_reference_consistency(records, country_code)
        
        self._detect_sudden_changes(records)
        self._check_cross_field_consistency(records)
        
        # Calculate consistency metrics
        consistency_metrics = self._calculate_consistency_metrics(records, country_code)
        
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        return self._build_result(details=consistency_metrics, duration_ms=duration_ms)
    
    def _extract_data_components(self, data: Any) -> tuple[List[Dict[str, Any]], Optional[str], Dict[str, Any]]:
        """
        Extract records, country code, and metadata from input.
        
        Args:
            data: Input data
        
        Returns:
            Tuple of (records, country_code, metadata)
        """
        country_code = None
        metadata = {}
        
        if isinstance(data, list):
            records = data
            # Try to infer country code from records
            if records and 'country_code' in records[0]:
                country_code = records[0]['country_code']
        elif isinstance(data, dict):
            if 'records' in data:
                records = data['records']
                country_code = data.get('country_code')
                metadata = {k: v for k, v in data.items() if k not in ['records', 'country_code']}
            else:
                records = [data]
                country_code = data.get('country_code')
        else:
            records = []
        
        return records, country_code, metadata
    
    def _check_internal_consistency(self, records: List[Dict[str, Any]]):
        """Check consistency within the dataset"""
        check_name = "internal_consistency"
        self._add_check(check_name)
        
        issues = []
        
        # Check 1: Same HS code should have consistent descriptions
        hs_descriptions = defaultdict(set)
        for record in records:
            if 'hs_code' in record and 'description' in record:
                hs_code = str(record['hs_code']).strip()
                description = str(record['description']).strip().lower()
                if hs_code and description:
                    hs_descriptions[hs_code].add(description)
        
        inconsistent_hs = [
            hs for hs, descs in hs_descriptions.items() 
            if len(descs) > 1
        ]
        
        if inconsistent_hs:
            issues.append(f"Inconsistent descriptions for {len(inconsistent_hs)} HS codes")
            self._add_warning(
                f"Found {len(inconsistent_hs)} HS code(s) with multiple descriptions",
                field="description"
            )
        
        # Check 2: Country code consistency
        country_codes = set()
        for record in records:
            if 'country_code' in record and record['country_code']:
                country_codes.add(record['country_code'])
        
        if len(country_codes) > 1:
            issues.append(f"Multiple country codes: {country_codes}")
            self._add_warning(
                f"Dataset contains multiple country codes: {', '.join(sorted(country_codes))}",
                field="country_code"
            )
        
        # Mark check result
        if issues:
            self._mark_failed(check_name)
        else:
            self._mark_passed(check_name)
    
    def _check_historical_consistency(
        self,
        records: List[Dict[str, Any]],
        country_code: Optional[str],
        metadata: Dict[str, Any]
    ):
        """Compare with historical data to detect changes"""
        check_name = "historical_consistency"
        self._add_check(check_name)
        
        if not country_code or country_code not in self.historical_data:
            self._mark_passed(check_name)
            return
        
        historical = self.historical_data[country_code]
        significant_changes = []
        
        # Build current data lookup
        current_rates = {}
        for record in records:
            if 'hs_code' in record and 'rate' in record:
                hs_code = str(record['hs_code']).strip()
                try:
                    current_rates[hs_code] = float(record['rate'])
                except (ValueError, TypeError):
                    continue
        
        # Compare with historical
        if 'rates' in historical:
            for hs_code, hist_rate in historical['rates'].items():
                if hs_code in current_rates:
                    current_rate = current_rates[hs_code]
                    
                    # Calculate change
                    absolute_change = abs(current_rate - hist_rate)
                    if hist_rate != 0:
                        percent_change = (absolute_change / hist_rate) * 100
                    else:
                        percent_change = 100 if current_rate != 0 else 0
                    
                    # Check if change is significant
                    if (percent_change > self.max_rate_change or 
                        absolute_change > self.MAX_ABSOLUTE_RATE_CHANGE):
                        significant_changes.append({
                            'hs_code': hs_code,
                            'old_rate': hist_rate,
                            'new_rate': current_rate,
                            'absolute_change': absolute_change,
                            'percent_change': percent_change
                        })
        
        if significant_changes:
            self._mark_failed(check_name)
            self._add_warning(
                f"Detected {len(significant_changes)} significant rate changes from historical data",
                field="rate"
            )
            # Add details for top changes
            for change in sorted(significant_changes, 
                               key=lambda x: x['percent_change'], 
                               reverse=True)[:5]:
                self._add_warning(
                    f"HS {change['hs_code']}: {change['old_rate']}% → {change['new_rate']}% "
                    f"({change['percent_change']:.1f}% change)",
                    field="rate",
                    value=change['new_rate']
                )
        else:
            self._mark_passed(check_name)
    
    def _check_regional_consistency(
        self,
        records: List[Dict[str, Any]],
        country_code: str
    ):
        """Check if rates are consistent with regional patterns"""
        check_name = "regional_consistency"
        self._add_check(check_name)
        
        # Determine country's region
        region = self._get_country_region(country_code)
        if not region:
            self._mark_passed(check_name)
            return
        
        # Get expected range for region
        expected_range = self.EXPECTED_RATE_RANGES.get(region, self.EXPECTED_RATE_RANGES['OTHER'])
        
        # Check rates against expected range
        out_of_range = []
        for record in records:
            if 'rate' in record and record['rate'] is not None:
                try:
                    rate = float(record['rate'])
                    if rate < expected_range[0] or rate > expected_range[1]:
                        out_of_range.append({
                            'hs_code': record.get('hs_code', 'unknown'),
                            'rate': rate
                        })
                except (ValueError, TypeError):
                    continue
        
        if out_of_range:
            percentage = (len(out_of_range) / len(records)) * 100
            if percentage > 10:  # More than 10% out of range
                self._mark_failed(check_name)
                self._add_warning(
                    f"{len(out_of_range)} rates ({percentage:.1f}%) outside expected "
                    f"{region} range [{expected_range[0]}-{expected_range[1]}%]",
                    field="rate"
                )
            else:
                self._mark_passed(check_name)
                self._add_warning(
                    f"{len(out_of_range)} rates outside expected regional range",
                    field="rate"
                )
        else:
            self._mark_passed(check_name)
    
    def _check_reference_consistency(
        self,
        records: List[Dict[str, Any]],
        country_code: Optional[str]
    ):
        """Validate against reference data"""
        check_name = "reference_consistency"
        self._add_check(check_name)
        
        if not country_code or country_code not in self.reference_data:
            self._mark_passed(check_name)
            return
        
        reference = self.reference_data[country_code]
        mismatches = []
        
        # Build current data lookup
        current_data = {}
        for record in records:
            if 'hs_code' in record:
                hs_code = str(record['hs_code']).strip()
                current_data[hs_code] = record
        
        # Compare with reference
        if 'rates' in reference:
            for hs_code, ref_rate in reference['rates'].items():
                if hs_code in current_data:
                    record = current_data[hs_code]
                    if 'rate' in record:
                        try:
                            current_rate = float(record['rate'])
                            ref_rate_float = float(ref_rate)
                            
                            # Allow small tolerance (0.1%)
                            if abs(current_rate - ref_rate_float) > 0.1:
                                mismatches.append({
                                    'hs_code': hs_code,
                                    'reference': ref_rate_float,
                                    'current': current_rate
                                })
                        except (ValueError, TypeError):
                            continue
        
        if mismatches:
            percentage = (len(mismatches) / len(records)) * 100
            if percentage > 5:  # More than 5% mismatches
                self._mark_failed(check_name)
                self._add_error(
                    f"High mismatch rate with reference data: {len(mismatches)} "
                    f"records ({percentage:.1f}%)",
                    field="rate"
                )
            else:
                self._mark_passed(check_name)
                self._add_warning(
                    f"{len(mismatches)} records differ from reference data",
                    field="rate"
                )
        else:
            self._mark_passed(check_name)
    
    def _detect_sudden_changes(self, records: List[Dict[str, Any]]):
        """Detect sudden rate changes within the dataset"""
        check_name = "sudden_changes"
        self._add_check(check_name)
        
        # Group by HS chapter (first 2 digits)
        chapter_rates = defaultdict(list)
        for record in records:
            if 'hs_code' in record and 'rate' in record:
                try:
                    hs_code = str(record['hs_code']).strip()
                    if len(hs_code) >= 2:
                        chapter = hs_code[:2]
                        rate = float(record['rate'])
                        chapter_rates[chapter].append(rate)
                except (ValueError, TypeError):
                    continue
        
        # Detect outliers within each chapter
        chapters_with_outliers = []
        for chapter, rates in chapter_rates.items():
            if len(rates) < 5:  # Need enough samples
                continue
            
            chapter_mean = mean(rates)
            chapter_stdev = stdev(rates) if len(rates) > 1 else 0
            
            if chapter_stdev == 0:
                continue
            
            # Find rates more than 3 std devs from mean
            outliers = [r for r in rates if abs(r - chapter_mean) > 3 * chapter_stdev]
            
            if outliers and len(outliers) > len(rates) * 0.1:  # More than 10%
                chapters_with_outliers.append(chapter)
                self._add_warning(
                    f"Chapter {chapter}: {len(outliers)} rates significantly differ "
                    f"from chapter average ({chapter_mean:.1f}%)",
                    field="rate"
                )
        
        if chapters_with_outliers:
            self._mark_failed(check_name)
        else:
            self._mark_passed(check_name)
    
    def _check_cross_field_consistency(self, records: List[Dict[str, Any]]):
        """Check consistency across related fields"""
        check_name = "cross_field_consistency"
        self._add_check(check_name)
        
        issues = []
        
        for idx, record in enumerate(records):
            # Check if HS code and description are both present or both absent
            has_hs = 'hs_code' in record and record['hs_code']
            has_desc = 'description' in record and record['description']
            
            if has_hs != has_desc:
                issues.append(f"Record {idx}: HS code without description or vice versa")
                if len(issues) >= 10:  # Limit warnings
                    break
        
        if issues:
            self._mark_failed(check_name)
            self._add_warning(
                f"Found {len(issues)} records with inconsistent HS code/description pairing"
            )
        else:
            self._mark_passed(check_name)
    
    def _get_country_region(self, country_code: str) -> Optional[str]:
        """Get the regional group for a country"""
        for region, countries in self.regional_groups.items():
            if country_code in countries:
                return region
        return None
    
    def _calculate_consistency_metrics(
        self,
        records: List[Dict[str, Any]],
        country_code: Optional[str]
    ) -> Dict[str, Any]:
        """Calculate consistency metrics"""
        metrics = {
            "total_records": len(records),
            "country_code": country_code,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Rate statistics
        rates = []
        for record in records:
            if 'rate' in record and record['rate'] is not None:
                try:
                    rates.append(float(record['rate']))
                except (ValueError, TypeError):
                    continue
        
        if rates:
            metrics["rate_statistics"] = {
                "mean": mean(rates),
                "median": median(rates),
                "min": min(rates),
                "max": max(rates),
                "stdev": stdev(rates) if len(rates) > 1 else 0,
                "count": len(rates)
            }
        
        # Regional info
        if country_code:
            region = self._get_country_region(country_code)
            if region:
                metrics["region"] = region
                metrics["expected_rate_range"] = self.EXPECTED_RATE_RANGES.get(
                    region, 
                    self.EXPECTED_RATE_RANGES['OTHER']
                )
        
        # Check enablement status
        metrics["checks_enabled"] = {
            "historical": self.enable_historical,
            "regional": self.enable_regional,
            "reference": bool(self.reference_data)
        }
        
        return metrics


async def validate_consistency(
    data: Union[Dict[str, Any], List[Dict[str, Any]]],
    config: Optional[Dict[str, Any]] = None
) -> ValidationResult:
    """
    Convenience function to validate data consistency.
    
    Args:
        data: Data to validate
        config: Optional validator configuration
    
    Returns:
        ValidationResult
    """
    validator = ConsistencyValidator(config)
    return await validator.validate(data)
