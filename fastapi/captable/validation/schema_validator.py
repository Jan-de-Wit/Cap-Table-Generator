"""
Schema Validation Module

Validates JSON structure against the cap table schema using jsonschema.
"""

from jsonschema import Draft201909Validator, ValidationError
from jsonschema.exceptions import SchemaError
from typing import Dict, List, Any
# Note: We load schema directly from file in __init__ to avoid cached imports


class SchemaValidator:
    """
    Validates JSON data against the cap table schema.

    Uses jsonschema Draft 2019-09 validator to check data structure,
    types, and required fields.
    """

    def __init__(self):
        """Initialize schema validator."""
        # Always reload schema from file to ensure we have the latest version
        # This is critical if the schema file was updated while the server is running
        from ..schema import load_schema_from_file
        self.schema = load_schema_from_file()

        _target_props = self.schema.get("$defs", {}).get(
            "TargetPercentageInstrument", {}).get("properties", {})
        _has_field = "target_is_top_up" in _target_props

        # Verify schema has target_is_top_up field
        if not _has_field:
            import warnings
            warnings.warn(
                "Schema missing target_is_top_up field! This may cause validation failures.")

        self.validator = Draft201909Validator(self.schema)

    def validate(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate data against schema.

        Args:
            data: Cap table JSON data

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        try:
            for error in self.validator.iter_errors(data):
                errors.append(self._format_error(error))
        except SchemaError as e:
            errors.append(f"Schema error: {str(e)}")

        return errors

    def _format_error(self, error: ValidationError) -> str:
        """
        Format validation error for readability.

        Args:
            error: jsonschema ValidationError

        Returns:
            Formatted error message string
        """
        path = " -> ".join(str(p)
                           for p in error.path) if error.path else "root"
        return f"Validation error at {path}: {error.message}"
