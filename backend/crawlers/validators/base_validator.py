"""
Base validator abstract class for AfCFTA data validation.

This module provides the foundation for all data validators in the system.
All specific validators should inherit from BaseValidator and implement
the validate() method.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationIssue(BaseModel):
    """Individual validation issue"""
    severity: ValidationSeverity
    message: str
    field: Optional[str] = None
    value: Optional[Any] = None
    expected: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationResult(BaseModel):
    """Result of a validation operation"""
    
    validator_name: str = Field(..., description="Name of the validator")
    score: float = Field(..., ge=0.0, le=100.0, description="Validation score (0-100)")
    passed: int = Field(..., ge=0, description="Number of checks passed")
    total: int = Field(..., ge=0, description="Total number of checks performed")
    errors: List[str] = Field(default_factory=list, description="List of error messages")
    warnings: List[str] = Field(default_factory=list, description="List of warning messages")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional validation details")
    issues: List[ValidationIssue] = Field(default_factory=list, description="Detailed issues")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration_ms: Optional[float] = None
    
    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)"""
        return len(self.errors) == 0
    
    @property
    def pass_rate(self) -> float:
        """Calculate pass rate percentage"""
        if self.total == 0:
            return 100.0
        return (self.passed / self.total) * 100.0


class BaseValidator(ABC):
    """
    Abstract base class for all validators.
    
    Provides common validation utilities and defines the interface
    that all validators must implement.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the validator.
        
        Args:
            config: Optional configuration dictionary for the validator
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self._validation_checks: List[str] = []
        self._passed_checks: Set[str] = set()
        self._failed_checks: Set[str] = set()
        self._issues: List[ValidationIssue] = []
    
    @abstractmethod
    async def validate(self, data: Any) -> ValidationResult:
        """
        Validate the provided data.
        
        Args:
            data: Data to validate (type depends on validator)
        
        Returns:
            ValidationResult with validation details
        """
        pass
    
    def _reset_state(self):
        """Reset validation state for a new validation run"""
        self._validation_checks = []
        self._passed_checks = set()
        self._failed_checks = set()
        self._issues = []
    
    def _add_check(self, check_name: str):
        """Register a validation check"""
        self._validation_checks.append(check_name)
    
    def _mark_passed(self, check_name: str):
        """Mark a check as passed"""
        if check_name in self._validation_checks:
            self._passed_checks.add(check_name)
    
    def _mark_failed(self, check_name: str):
        """Mark a check as failed"""
        if check_name in self._validation_checks:
            self._failed_checks.add(check_name)
    
    def _add_issue(
        self,
        severity: ValidationSeverity,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        expected: Optional[Any] = None
    ):
        """Add a validation issue"""
        issue = ValidationIssue(
            severity=severity,
            message=message,
            field=field,
            value=value,
            expected=expected
        )
        self._issues.append(issue)
    
    def _add_error(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        expected: Optional[Any] = None
    ):
        """Add an error issue"""
        self._add_issue(ValidationSeverity.ERROR, message, field, value, expected)
    
    def _add_warning(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        expected: Optional[Any] = None
    ):
        """Add a warning issue"""
        self._add_issue(ValidationSeverity.WARNING, message, field, value, expected)
    
    def _calculate_score(self) -> float:
        """
        Calculate validation score based on passed/failed checks.
        
        Returns:
            Score from 0-100
        """
        total = len(self._validation_checks)
        if total == 0:
            return 100.0
        
        passed = len(self._passed_checks)
        return (passed / total) * 100.0
    
    def _build_result(
        self,
        validator_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None
    ) -> ValidationResult:
        """
        Build a validation result from current state.
        
        Args:
            validator_name: Name of the validator (defaults to class name)
            details: Additional details to include
            duration_ms: Duration of validation in milliseconds
        
        Returns:
            ValidationResult instance
        """
        errors = [
            issue.message for issue in self._issues 
            if issue.severity == ValidationSeverity.ERROR
        ]
        warnings = [
            issue.message for issue in self._issues 
            if issue.severity == ValidationSeverity.WARNING
        ]
        
        return ValidationResult(
            validator_name=validator_name or self.__class__.__name__,
            score=self._calculate_score(),
            passed=len(self._passed_checks),
            total=len(self._validation_checks),
            errors=errors,
            warnings=warnings,
            details=details or {},
            issues=self._issues,
            duration_ms=duration_ms
        )
    
    # Common validation utilities
    
    @staticmethod
    def is_valid_string(value: Any, min_length: int = 1, max_length: Optional[int] = None) -> bool:
        """Check if value is a valid string"""
        if not isinstance(value, str):
            return False
        if len(value) < min_length:
            return False
        if max_length and len(value) > max_length:
            return False
        return True
    
    @staticmethod
    def is_valid_number(
        value: Any,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        allow_float: bool = True
    ) -> bool:
        """Check if value is a valid number within range"""
        if allow_float:
            if not isinstance(value, (int, float)):
                return False
        else:
            if not isinstance(value, int):
                return False
        
        if min_value is not None and value < min_value:
            return False
        if max_value is not None and value > max_value:
            return False
        
        return True
    
    @staticmethod
    def is_valid_percentage(value: Any) -> bool:
        """Check if value is a valid percentage (0-100)"""
        return BaseValidator.is_valid_number(value, min_value=0.0, max_value=100.0)
    
    @staticmethod
    def check_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """
        Check for missing required fields.
        
        Args:
            data: Dictionary to check
            required_fields: List of required field names
        
        Returns:
            List of missing field names
        """
        missing = []
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == "":
                missing.append(field)
        return missing
    
    @staticmethod
    def check_field_types(data: Dict[str, Any], type_map: Dict[str, type]) -> Dict[str, str]:
        """
        Check if fields have correct types.
        
        Args:
            data: Dictionary to check
            type_map: Mapping of field names to expected types
        
        Returns:
            Dictionary of field_name -> error_message for type mismatches
        """
        errors = {}
        for field, expected_type in type_map.items():
            if field in data and data[field] is not None:
                if not isinstance(data[field], expected_type):
                    errors[field] = f"Expected {expected_type.__name__}, got {type(data[field]).__name__}"
        return errors
    
    @staticmethod
    def check_duplicates(items: List[Any], key_func=None) -> List[Any]:
        """
        Find duplicate items in a list.
        
        Args:
            items: List of items to check
            key_func: Optional function to extract key from item
        
        Returns:
            List of duplicate items
        """
        seen = set()
        duplicates = []
        
        for item in items:
            key = key_func(item) if key_func else item
            if key in seen:
                duplicates.append(item)
            else:
                seen.add(key)
        
        return duplicates
    
    @staticmethod
    def calculate_completeness(data: Dict[str, Any], all_fields: List[str]) -> float:
        """
        Calculate data completeness percentage.
        
        Args:
            data: Dictionary to check
            all_fields: List of all expected fields
        
        Returns:
            Completeness percentage (0-100)
        """
        if not all_fields:
            return 100.0
        
        filled = sum(
            1 for field in all_fields 
            if field in data and data[field] is not None and data[field] != ""
        )
        return (filled / len(all_fields)) * 100.0
