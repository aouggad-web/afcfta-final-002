"""
Validators for AfCFTA customs data.

This module provides comprehensive validation for scraped customs data including:
- Base validation framework (BaseValidator, ValidationResult)
- Tariff data validation (TariffValidator)
- Data quality checks (DataQualityValidator)
- Consistency validation (ConsistencyValidator)

Example usage:
    from backend.crawlers.validators import validate_tariff_data, TariffValidator
    
    # Quick validation
    result = await validate_tariff_data(tariff_records)
    
    # Custom validation
    validator = TariffValidator(config={'strict_hs_validation': True})
    result = await validator.validate(tariff_records)
"""

from .base_validator import (
    BaseValidator,
    ValidationResult,
    ValidationIssue,
    ValidationSeverity
)

from .tariff_validator import (
    TariffValidator,
    validate_tariff_data
)

from .data_quality_validator import (
    DataQualityValidator,
    validate_data_quality
)

from .consistency_validator import (
    ConsistencyValidator,
    validate_consistency
)


__all__ = [
    # Base classes and models
    'BaseValidator',
    'ValidationResult',
    'ValidationIssue',
    'ValidationSeverity',
    
    # Tariff validation
    'TariffValidator',
    'validate_tariff_data',
    
    # Data quality validation
    'DataQualityValidator',
    'validate_data_quality',
    
    # Consistency validation
    'ConsistencyValidator',
    'validate_consistency',
]
