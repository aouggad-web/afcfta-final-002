"""
Tariff data validator for AfCFTA customs data.

Validates tariff records including HS codes, rates, and required fields.
Ensures data quality and consistency for tariff information.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from .base_validator import BaseValidator, ValidationResult, ValidationSeverity


logger = logging.getLogger(__name__)


class TariffValidator(BaseValidator):
    """
    Validator for tariff data records.
    
    Validates:
    - HS code format and validity
    - Tariff rates (range, format)
    - Required fields
    - Data types
    - Duplicates
    - Business logic rules
    """
    
    # HS code validation patterns
    HS2_PATTERN = re.compile(r'^\d{2}$')
    HS4_PATTERN = re.compile(r'^\d{4}$')
    HS6_PATTERN = re.compile(r'^\d{6}$')
    HS8_PATTERN = re.compile(r'^\d{8}$')
    HS10_PATTERN = re.compile(r'^\d{10}$')
    HS12_PATTERN = re.compile(r'^\d{12}$')
    
    # Valid HS chapter range (01-99)
    VALID_HS_CHAPTER_MIN = 1
    VALID_HS_CHAPTER_MAX = 99
    
    # Reasonable tariff rate limits
    MIN_TARIFF_RATE = 0.0
    MAX_TARIFF_RATE = 100.0
    SUSPICIOUS_TARIFF_RATE = 50.0  # Warning threshold
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize tariff validator.
        
        Args:
            config: Optional configuration with:
                - strict_hs_validation: bool (default True) - Strict HS code validation
                - allow_zero_rates: bool (default True) - Allow 0% tariff rates
                - max_rate: float (default 100.0) - Maximum allowed tariff rate
                - required_fields: List[str] - Override default required fields
        """
        super().__init__(config)
        self.strict_hs_validation = config.get('strict_hs_validation', True) if config else True
        self.allow_zero_rates = config.get('allow_zero_rates', True) if config else True
        self.max_rate = config.get('max_rate', self.MAX_TARIFF_RATE) if config else self.MAX_TARIFF_RATE
        self.required_fields = config.get('required_fields', [
            'hs_code', 'rate', 'description'
        ]) if config else ['hs_code', 'rate', 'description']
    
    async def validate(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> ValidationResult:
        """
        Validate tariff data.
        
        Args:
            data: Single tariff record (dict) or list of records
        
        Returns:
            ValidationResult with validation details
        """
        start_time = datetime.utcnow()
        self._reset_state()
        
        # Handle both single record and list of records
        if isinstance(data, dict):
            records = [data]
            single_record = True
        elif isinstance(data, list):
            records = data
            single_record = False
        else:
            self._add_check("data_type")
            self._mark_failed("data_type")
            self._add_error("Invalid data type: expected dict or list", value=type(data).__name__)
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            return self._build_result(details={"records_count": 0}, duration_ms=duration_ms)
        
        # Validate each record
        valid_records = 0
        for idx, record in enumerate(records):
            if self._validate_record(record, idx):
                valid_records += 1
        
        # Check for duplicates across all records
        if len(records) > 1:
            self._check_duplicates(records)
        
        # Calculate statistics
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        details = {
            "records_count": len(records),
            "valid_records": valid_records,
            "invalid_records": len(records) - valid_records,
            "single_record": single_record,
            "validation_timestamp": datetime.utcnow().isoformat()
        }
        
        return self._build_result(details=details, duration_ms=duration_ms)
    
    def _validate_record(self, record: Dict[str, Any], index: int) -> bool:
        """
        Validate a single tariff record.
        
        Args:
            record: Tariff record to validate
            index: Index of record in batch
        
        Returns:
            True if record is valid (no errors)
        """
        record_valid = True
        prefix = f"record_{index}"
        
        # Check 1: Validate data structure
        check_name = f"{prefix}_structure"
        self._add_check(check_name)
        if not isinstance(record, dict):
            self._mark_failed(check_name)
            self._add_error(f"Record {index}: Not a dictionary", value=type(record).__name__)
            return False
        self._mark_passed(check_name)
        
        # Check 2: Required fields
        check_name = f"{prefix}_required_fields"
        self._add_check(check_name)
        missing = self.check_required_fields(record, self.required_fields)
        if missing:
            self._mark_failed(check_name)
            self._add_error(
                f"Record {index}: Missing required fields: {', '.join(missing)}",
                field="required_fields"
            )
            record_valid = False
        else:
            self._mark_passed(check_name)
        
        # Check 3: HS code validation
        if 'hs_code' in record and record['hs_code']:
            check_name = f"{prefix}_hs_code"
            self._add_check(check_name)
            hs_valid, hs_message = self._validate_hs_code(record['hs_code'])
            if not hs_valid:
                self._mark_failed(check_name)
                self._add_error(
                    f"Record {index}: {hs_message}",
                    field="hs_code",
                    value=record['hs_code']
                )
                record_valid = False
            else:
                self._mark_passed(check_name)
                if hs_message:  # Warning message
                    self._add_warning(f"Record {index}: {hs_message}", field="hs_code")
        
        # Check 4: Tariff rate validation
        if 'rate' in record:
            check_name = f"{prefix}_rate"
            self._add_check(check_name)
            rate_valid, rate_message = self._validate_tariff_rate(record['rate'])
            if not rate_valid:
                self._mark_failed(check_name)
                self._add_error(
                    f"Record {index}: {rate_message}",
                    field="rate",
                    value=record['rate']
                )
                record_valid = False
            else:
                self._mark_passed(check_name)
                if rate_message:  # Warning message
                    self._add_warning(f"Record {index}: {rate_message}", field="rate")
        
        # Check 5: Description validation
        if 'description' in record and record['description']:
            check_name = f"{prefix}_description"
            self._add_check(check_name)
            if not self.is_valid_string(record['description'], min_length=3, max_length=1000):
                self._mark_failed(check_name)
                self._add_error(
                    f"Record {index}: Invalid description (must be 3-1000 chars)",
                    field="description"
                )
                record_valid = False
            else:
                self._mark_passed(check_name)
        
        # Check 6: Data type validation
        check_name = f"{prefix}_types"
        self._add_check(check_name)
        type_errors = self._validate_field_types(record)
        if type_errors:
            self._mark_failed(check_name)
            for field, error in type_errors.items():
                self._add_error(f"Record {index}: {field} - {error}", field=field)
            record_valid = False
        else:
            self._mark_passed(check_name)
        
        # Check 7: Optional field validations
        if 'currency' in record and record['currency']:
            check_name = f"{prefix}_currency"
            self._add_check(check_name)
            if not self._validate_currency(record['currency']):
                self._mark_failed(check_name)
                self._add_warning(
                    f"Record {index}: Invalid currency code",
                    field="currency",
                    value=record['currency']
                )
            else:
                self._mark_passed(check_name)
        
        # Check 8: Unit of measurement
        if 'unit' in record and record['unit']:
            check_name = f"{prefix}_unit"
            self._add_check(check_name)
            if not self.is_valid_string(record['unit'], min_length=1, max_length=50):
                self._mark_failed(check_name)
                self._add_warning(
                    f"Record {index}: Invalid unit of measurement",
                    field="unit"
                )
            else:
                self._mark_passed(check_name)
        
        return record_valid
    
    def _validate_hs_code(self, hs_code: Any) -> tuple[bool, Optional[str]]:
        """
        Validate HS code format and range.
        
        Args:
            hs_code: HS code to validate
        
        Returns:
            Tuple of (is_valid, message)
        """
        # Check type
        if not isinstance(hs_code, str):
            if isinstance(hs_code, (int, float)):
                hs_code = str(int(hs_code))
            else:
                return False, f"Invalid HS code type: {type(hs_code).__name__}"
        
        # Remove spaces and dots
        hs_code = hs_code.replace(" ", "").replace(".", "")
        
        # Check if it's all digits
        if not hs_code.isdigit():
            return False, f"HS code must contain only digits: {hs_code}"
        
        # Check length
        hs_length = len(hs_code)
        if hs_length not in [2, 4, 6, 8, 10, 12]:
            if self.strict_hs_validation:
                return False, f"HS code must be 2, 4, 6, 8, 10, or 12 digits: {hs_code}"
            else:
                return True, f"Non-standard HS code length ({hs_length}): {hs_code}"
        
        # Validate chapter (first 2 digits)
        chapter = int(hs_code[:2])
        if chapter < self.VALID_HS_CHAPTER_MIN or chapter > self.VALID_HS_CHAPTER_MAX:
            return False, f"Invalid HS chapter {chapter}: must be between 01-99"
        
        # Special reserved chapters check
        reserved_chapters = [77]  # Reserved for future use
        if chapter in reserved_chapters:
            return True, f"HS chapter {chapter:02d} is reserved"
        
        return True, None
    
    def _validate_tariff_rate(self, rate: Any) -> tuple[bool, Optional[str]]:
        """
        Validate tariff rate value.
        
        Args:
            rate: Tariff rate to validate
        
        Returns:
            Tuple of (is_valid, message)
        """
        # Check type and convert
        try:
            if isinstance(rate, str):
                # Remove percentage sign if present
                rate = rate.replace("%", "").strip()
                rate = float(rate)
            elif isinstance(rate, (int, float)):
                rate = float(rate)
            else:
                return False, f"Invalid rate type: {type(rate).__name__}"
        except (ValueError, TypeError):
            return False, f"Cannot convert rate to number: {rate}"
        
        # Check range
        if rate < self.MIN_TARIFF_RATE:
            return False, f"Tariff rate cannot be negative: {rate}%"
        
        if rate > self.max_rate:
            return False, f"Tariff rate exceeds maximum ({self.max_rate}%): {rate}%"
        
        # Check for zero rate
        if rate == 0.0 and not self.allow_zero_rates:
            return False, "Zero tariff rate not allowed"
        
        # Warning for suspicious rates
        if rate > self.SUSPICIOUS_TARIFF_RATE:
            return True, f"High tariff rate detected: {rate}% (threshold: {self.SUSPICIOUS_TARIFF_RATE}%)"
        
        return True, None
    
    def _validate_field_types(self, record: Dict[str, Any]) -> Dict[str, str]:
        """
        Validate data types of common fields.
        
        Args:
            record: Record to validate
        
        Returns:
            Dictionary of field -> error message
        """
        errors = {}
        
        # HS code should be string or numeric
        if 'hs_code' in record and record['hs_code'] is not None:
            if not isinstance(record['hs_code'], (str, int, float)):
                errors['hs_code'] = f"Expected str/int/float, got {type(record['hs_code']).__name__}"
        
        # Rate should be numeric
        if 'rate' in record and record['rate'] is not None:
            if not isinstance(record['rate'], (int, float, str)):
                errors['rate'] = f"Expected numeric type, got {type(record['rate']).__name__}"
        
        # Description should be string
        if 'description' in record and record['description'] is not None:
            if not isinstance(record['description'], str):
                errors['description'] = f"Expected string, got {type(record['description']).__name__}"
        
        return errors
    
    def _validate_currency(self, currency: str) -> bool:
        """
        Validate currency code (basic check).
        
        Args:
            currency: Currency code to validate
        
        Returns:
            True if valid
        """
        if not isinstance(currency, str):
            return False
        
        # Should be 3 uppercase letters
        if len(currency) != 3:
            return False
        
        return currency.isupper() and currency.isalpha()
    
    def _check_duplicates(self, records: List[Dict[str, Any]]):
        """
        Check for duplicate HS codes in records.
        
        Args:
            records: List of tariff records
        """
        check_name = "duplicates"
        self._add_check(check_name)
        
        # Extract HS codes
        hs_codes = [
            str(r.get('hs_code', '')).replace(" ", "").replace(".", "")
            for r in records if r.get('hs_code')
        ]
        
        # Find duplicates
        duplicates = self.check_duplicates(hs_codes)
        
        if duplicates:
            self._mark_failed(check_name)
            unique_dupes = list(set(duplicates))
            self._add_warning(
                f"Found {len(duplicates)} duplicate HS code(s): {', '.join(unique_dupes[:5])}"
                + (f" and {len(unique_dupes) - 5} more" if len(unique_dupes) > 5 else ""),
                field="hs_code"
            )
        else:
            self._mark_passed(check_name)


async def validate_tariff_data(
    data: Union[Dict[str, Any], List[Dict[str, Any]]],
    config: Optional[Dict[str, Any]] = None
) -> ValidationResult:
    """
    Convenience function to validate tariff data.
    
    Args:
        data: Tariff data to validate (single record or list)
        config: Optional validator configuration
    
    Returns:
        ValidationResult
    """
    validator = TariffValidator(config)
    return await validator.validate(data)
