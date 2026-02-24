"""
Data quality validator for AfCFTA customs data.

Validates overall data quality including completeness, consistency,
outlier detection, freshness, and coverage metrics.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from statistics import mean, stdev

from .base_validator import BaseValidator, ValidationResult, ValidationSeverity


logger = logging.getLogger(__name__)


class DataQualityValidator(BaseValidator):
    """
    Validator for overall data quality metrics.
    
    Checks:
    - Completeness (% of required fields filled)
    - Consistency (patterns and expected values)
    - Outliers (values far from mean)
    - Freshness (data age)
    - Coverage (minimum record count)
    - Distribution analysis
    """
    
    # Default thresholds
    DEFAULT_MIN_COMPLETENESS = 80.0  # Minimum 80% fields filled
    DEFAULT_MIN_COVERAGE = 100  # Minimum 100 records
    DEFAULT_MAX_AGE_DAYS = 90  # Data should be less than 90 days old
    DEFAULT_OUTLIER_STDDEV = 3.0  # Values beyond 3 standard deviations
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize data quality validator.
        
        Args:
            config: Optional configuration with:
                - min_completeness: float (default 80.0) - Minimum completeness %
                - min_coverage: int (default 100) - Minimum number of records
                - max_age_days: int (default 90) - Maximum data age in days
                - outlier_threshold: float (default 3.0) - Std dev for outliers
                - required_fields: List[str] - Fields to check for completeness
                - numeric_fields: List[str] - Fields to check for outliers
        """
        super().__init__(config)
        self.min_completeness = config.get('min_completeness', self.DEFAULT_MIN_COMPLETENESS) if config else self.DEFAULT_MIN_COMPLETENESS
        self.min_coverage = config.get('min_coverage', self.DEFAULT_MIN_COVERAGE) if config else self.DEFAULT_MIN_COVERAGE
        self.max_age_days = config.get('max_age_days', self.DEFAULT_MAX_AGE_DAYS) if config else self.DEFAULT_MAX_AGE_DAYS
        self.outlier_threshold = config.get('outlier_threshold', self.DEFAULT_OUTLIER_STDDEV) if config else self.DEFAULT_OUTLIER_STDDEV
        self.required_fields = config.get('required_fields', [
            'hs_code', 'rate', 'description', 'country_code'
        ]) if config else ['hs_code', 'rate', 'description', 'country_code']
        self.numeric_fields = config.get('numeric_fields', ['rate']) if config else ['rate']
    
    async def validate(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> ValidationResult:
        """
        Validate data quality.
        
        Args:
            data: Dataset to validate (single record or list)
                  Can also be a dict with 'records' key and metadata
        
        Returns:
            ValidationResult with quality metrics
        """
        start_time = datetime.utcnow()
        self._reset_state()
        
        # Extract records and metadata
        records, metadata = self._extract_data(data)
        
        if not records:
            self._add_check("has_data")
            self._mark_failed("has_data")
            self._add_error("No data provided for validation")
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            return self._build_result(details={"records_count": 0}, duration_ms=duration_ms)
        
        # Run quality checks
        self._check_coverage(records)
        self._check_completeness(records)
        self._check_freshness(metadata)
        self._check_outliers(records)
        self._check_consistency(records)
        self._check_distribution(records)
        
        # Calculate quality score
        quality_metrics = self._calculate_quality_metrics(records, metadata)
        
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        return self._build_result(details=quality_metrics, duration_ms=duration_ms)
    
    def _extract_data(self, data: Any) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Extract records and metadata from input data.
        
        Args:
            data: Input data
        
        Returns:
            Tuple of (records list, metadata dict)
        """
        metadata = {}
        
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict):
            if 'records' in data:
                records = data['records']
                metadata = {k: v for k, v in data.items() if k != 'records'}
            else:
                records = [data]
        else:
            records = []
        
        return records, metadata
    
    def _check_coverage(self, records: List[Dict[str, Any]]):
        """Check if dataset has minimum required records"""
        check_name = "coverage"
        self._add_check(check_name)
        
        record_count = len(records)
        
        if record_count < self.min_coverage:
            self._mark_failed(check_name)
            self._add_error(
                f"Insufficient data coverage: {record_count} records (minimum: {self.min_coverage})",
                expected=self.min_coverage,
                value=record_count
            )
        else:
            self._mark_passed(check_name)
            if record_count < self.min_coverage * 1.2:  # Within 20% of minimum
                self._add_warning(
                    f"Low data coverage: {record_count} records (recommended: >{self.min_coverage * 1.2:.0f})"
                )
    
    def _check_completeness(self, records: List[Dict[str, Any]]):
        """Check field completeness across all records"""
        check_name = "completeness"
        self._add_check(check_name)
        
        if not records:
            self._mark_failed(check_name)
            return
        
        # Calculate completeness for each record
        completeness_scores = []
        incomplete_fields = {}
        
        for record in records:
            score = self.calculate_completeness(record, self.required_fields)
            completeness_scores.append(score)
            
            # Track which fields are commonly missing
            for field in self.required_fields:
                if field not in record or record[field] is None or record[field] == "":
                    incomplete_fields[field] = incomplete_fields.get(field, 0) + 1
        
        # Calculate average completeness
        avg_completeness = mean(completeness_scores)
        
        if avg_completeness < self.min_completeness:
            self._mark_failed(check_name)
            self._add_error(
                f"Data completeness too low: {avg_completeness:.1f}% (minimum: {self.min_completeness}%)",
                expected=f"{self.min_completeness}%",
                value=f"{avg_completeness:.1f}%"
            )
        else:
            self._mark_passed(check_name)
        
        # Add warnings for commonly missing fields
        total_records = len(records)
        for field, count in incomplete_fields.items():
            percentage = (count / total_records) * 100
            if percentage > 20:  # More than 20% missing
                self._add_warning(
                    f"Field '{field}' missing in {percentage:.1f}% of records ({count}/{total_records})",
                    field=field
                )
    
    def _check_freshness(self, metadata: Dict[str, Any]):
        """Check data freshness based on timestamp"""
        check_name = "freshness"
        self._add_check(check_name)
        
        # Look for timestamp in various formats
        timestamp = None
        timestamp_field = None
        
        for field in ['timestamp', 'scraped_at', 'updated_at', 'created_at', 'date']:
            if field in metadata:
                timestamp_field = field
                timestamp_value = metadata[field]
                
                # Try to parse timestamp
                if isinstance(timestamp_value, datetime):
                    timestamp = timestamp_value
                elif isinstance(timestamp_value, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp_value.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        try:
                            timestamp = datetime.strptime(timestamp_value, '%Y-%m-%d')
                        except ValueError:
                            continue
                break
        
        if timestamp is None:
            self._mark_passed(check_name)
            self._add_warning("No timestamp found in metadata, cannot verify data freshness")
            return
        
        # Calculate age
        now = datetime.utcnow()
        if timestamp.tzinfo is not None:
            # Make now timezone-aware
            from datetime import timezone
            now = datetime.now(timezone.utc)
        
        age = now - timestamp
        age_days = age.days
        
        if age_days > self.max_age_days:
            self._mark_failed(check_name)
            self._add_error(
                f"Data is stale: {age_days} days old (maximum: {self.max_age_days} days)",
                field=timestamp_field,
                expected=f"<{self.max_age_days} days",
                value=f"{age_days} days"
            )
        else:
            self._mark_passed(check_name)
            if age_days > self.max_age_days * 0.8:  # Within 80% of max age
                self._add_warning(
                    f"Data is aging: {age_days} days old (maximum: {self.max_age_days} days)"
                )
    
    def _check_outliers(self, records: List[Dict[str, Any]]):
        """Detect outliers in numeric fields"""
        check_name = "outliers"
        self._add_check(check_name)
        
        outliers_found = []
        
        for field in self.numeric_fields:
            # Extract numeric values
            values = []
            for record in records:
                if field in record and record[field] is not None:
                    try:
                        value = float(record[field])
                        values.append(value)
                    except (ValueError, TypeError):
                        continue
            
            if len(values) < 10:  # Need enough data points
                continue
            
            # Calculate statistics
            field_mean = mean(values)
            field_stdev = stdev(values) if len(values) > 1 else 0
            
            if field_stdev == 0:
                continue
            
            # Find outliers
            threshold = self.outlier_threshold * field_stdev
            lower_bound = field_mean - threshold
            upper_bound = field_mean + threshold
            
            field_outliers = [v for v in values if v < lower_bound or v > upper_bound]
            
            if field_outliers:
                outliers_found.extend(field_outliers)
                percentage = (len(field_outliers) / len(values)) * 100
                
                if percentage > 5:  # More than 5% outliers is concerning
                    self._add_warning(
                        f"High percentage of outliers in '{field}': {percentage:.1f}% "
                        f"({len(field_outliers)}/{len(values)}) outside "
                        f"[{lower_bound:.2f}, {upper_bound:.2f}]",
                        field=field
                    )
        
        if outliers_found:
            if len(outliers_found) > len(records) * 0.1:  # More than 10% of records
                self._mark_failed(check_name)
                self._add_error(
                    f"Too many outliers detected: {len(outliers_found)} values"
                )
            else:
                self._mark_passed(check_name)
        else:
            self._mark_passed(check_name)
    
    def _check_consistency(self, records: List[Dict[str, Any]]):
        """Check data consistency patterns"""
        check_name = "consistency"
        self._add_check(check_name)
        
        inconsistencies = []
        
        # Check for consistent field presence
        if records:
            first_record_fields = set(records[0].keys())
            for idx, record in enumerate(records[1:], 1):
                record_fields = set(record.keys())
                if record_fields != first_record_fields:
                    missing = first_record_fields - record_fields
                    extra = record_fields - first_record_fields
                    if missing or extra:
                        inconsistencies.append(f"Record {idx}: field mismatch")
                        if len(inconsistencies) >= 10:  # Limit warnings
                            break
        
        # Check rate consistency (should be percentages)
        if 'rate' in self.numeric_fields:
            for record in records[:100]:  # Sample first 100
                if 'rate' in record and record['rate'] is not None:
                    try:
                        rate = float(record['rate'])
                        # Check if rate looks like it might be in wrong format
                        if rate > 200 and rate < 10000:
                            self._add_warning(
                                "Some rates appear to be in basis points instead of percentage",
                                field="rate"
                            )
                            break
                    except (ValueError, TypeError):
                        pass
        
        if inconsistencies:
            self._mark_failed(check_name)
            self._add_warning(
                f"Schema inconsistencies detected in {len(inconsistencies)} records"
            )
        else:
            self._mark_passed(check_name)
    
    def _check_distribution(self, records: List[Dict[str, Any]]):
        """Analyze data distribution"""
        check_name = "distribution"
        self._add_check(check_name)
        
        # Check rate distribution
        if 'rate' in self.numeric_fields:
            rates = []
            for record in records:
                if 'rate' in record and record['rate'] is not None:
                    try:
                        rates.append(float(record['rate']))
                    except (ValueError, TypeError):
                        continue
            
            if rates:
                # Check if all rates are the same (suspicious)
                unique_rates = len(set(rates))
                if unique_rates == 1:
                    self._mark_failed(check_name)
                    self._add_warning(
                        f"All {len(rates)} tariff rates are identical: {rates[0]}%",
                        field="rate"
                    )
                elif unique_rates < len(rates) * 0.1:  # Less than 10% unique
                    self._add_warning(
                        f"Low rate diversity: only {unique_rates} unique rates among {len(rates)} records",
                        field="rate"
                    )
                    self._mark_passed(check_name)
                else:
                    self._mark_passed(check_name)
            else:
                self._mark_passed(check_name)
        else:
            self._mark_passed(check_name)
    
    def _calculate_quality_metrics(
        self,
        records: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate overall quality metrics.
        
        Args:
            records: List of data records
            metadata: Data metadata
        
        Returns:
            Dictionary with quality metrics
        """
        metrics = {
            "total_records": len(records),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Completeness metrics
        if records:
            completeness_scores = [
                self.calculate_completeness(r, self.required_fields) 
                for r in records
            ]
            metrics["avg_completeness"] = mean(completeness_scores)
            metrics["min_completeness"] = min(completeness_scores)
            metrics["max_completeness"] = max(completeness_scores)
        
        # Coverage metrics
        metrics["coverage_status"] = "sufficient" if len(records) >= self.min_coverage else "insufficient"
        metrics["coverage_percentage"] = (len(records) / self.min_coverage) * 100 if self.min_coverage > 0 else 100
        
        # Freshness metrics
        if 'timestamp' in metadata or 'scraped_at' in metadata:
            ts = metadata.get('timestamp') or metadata.get('scraped_at')
            if isinstance(ts, (str, datetime)):
                metrics["data_timestamp"] = str(ts)
        
        # Field statistics
        if records:
            all_fields = set()
            for record in records:
                all_fields.update(record.keys())
            metrics["total_fields"] = len(all_fields)
            metrics["fields"] = sorted(list(all_fields))
        
        return metrics


async def validate_data_quality(
    data: Union[Dict[str, Any], List[Dict[str, Any]]],
    config: Optional[Dict[str, Any]] = None
) -> ValidationResult:
    """
    Convenience function to validate data quality.
    
    Args:
        data: Data to validate
        config: Optional validator configuration
    
    Returns:
        ValidationResult
    """
    validator = DataQualityValidator(config)
    return await validator.validate(data)
