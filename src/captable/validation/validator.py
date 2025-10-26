"""
Main Validator - Orchestrates All Validation Steps

Coordinates schema validation, relationship validation, business rules,
and FEO validation into a unified validation pipeline.
"""

from typing import Dict, List, Any, Tuple
from .schema_validator import SchemaValidator
from .relationship_validator import RelationshipValidator
from .business_rules import BusinessRulesValidator
from .feo_validator import FEOValidator


class CapTableValidator:
    """
    Main validator for cap table JSON data.
    
    Coordinates multiple validation steps:
    1. Schema validation (structure and types)
    2. Relationship validation (foreign keys)
    3. Business rules validation (business logic)
    4. FEO validation (formula objects)
    """
    
    def __init__(self):
        """Initialize validator with specialized validators."""
        self.schema_validator = SchemaValidator()
        self.relationship_validator = RelationshipValidator()
        self.business_rules_validator = BusinessRulesValidator()
        self.feo_validator = FEOValidator()
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate cap table data through all validation steps.
        
        Args:
            data: Cap table JSON data
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Step 1: Schema validation
        errors.extend(self.schema_validator.validate(data))
        
        # Only run additional validations if schema is valid
        if not errors:
            # Step 2: Relationship validation
            errors.extend(self.relationship_validator.validate(data))
            
            # Step 3: Business rules validation
            errors.extend(self.business_rules_validator.validate(data))
            
            # Step 4: FEO validation
            errors.extend(self.feo_validator.validate(data))
        
        return (len(errors) == 0, errors)


def validate_cap_table(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Convenience function to validate cap table data.
    
    Args:
        data: Cap table JSON data
        
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    validator = CapTableValidator()
    return validator.validate(data)

