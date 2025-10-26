"""
Schema Validation for Cap Table JSON Data
Validates structure, types, relationships, and FEO objects.
"""

from jsonschema import Draft201909Validator, ValidationError
from jsonschema.exceptions import SchemaError
import re
from typing import Dict, List, Any, Tuple
from .schema import CAP_TABLE_SCHEMA


class CapTableValidator:
    """Validates cap table JSON data against schema with custom validators."""
    
    def __init__(self):
        self.schema = CAP_TABLE_SCHEMA
        self.validator = Draft201909Validator(self.schema)
        
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate cap table data against schema.
        
        Args:
            data: Cap table JSON data
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Schema validation
        try:
            for error in self.validator.iter_errors(data):
                errors.append(self._format_error(error))
        except SchemaError as e:
            errors.append(f"Schema error: {str(e)}")
            
        # Custom validations
        if not errors:
            errors.extend(self._validate_relationships(data))
            errors.extend(self._validate_feo_objects(data))
            errors.extend(self._validate_name_uniqueness(data))
            
        return (len(errors) == 0, errors)
    
    def _format_error(self, error: ValidationError) -> str:
        """Format validation error for readability."""
        path = " -> ".join(str(p) for p in error.path) if error.path else "root"
        return f"Validation error at {path}: {error.message}"
    
    def _validate_relationships(self, data: Dict[str, Any]) -> List[str]:
        """Validate foreign key relationships between entities."""
        errors = []
        
        # Collect all names
        holder_names = {h["name"] for h in data.get("holders", [])}
        class_names = {c["name"] for c in data.get("classes", [])}
        terms_names = {t["name"] for t in data.get("terms", [])}
        round_names = {r["name"] for r in data.get("rounds", [])}
        
        # Validate instrument references
        for idx, instrument in enumerate(data.get("instruments", [])):
            holder_name = instrument.get("holder_name")
            if holder_name and holder_name not in holder_names:
                errors.append(f"Instrument {idx}: holder_name '{holder_name}' not found in holders")
                
            class_name = instrument.get("class_name")
            if class_name and class_name not in class_names:
                errors.append(f"Instrument {idx}: class_name '{class_name}' not found in classes")
                
            round_name = instrument.get("round_name")
            if round_name and round_name not in round_names:
                errors.append(f"Instrument {idx}: round_name '{round_name}' not found in rounds")
        
        # Validate class -> terms references
        for idx, sec_class in enumerate(data.get("classes", [])):
            terms_name = sec_class.get("terms_name")
            if terms_name and terms_name not in terms_names:
                errors.append(f"SecurityClass {idx}: terms_name '{terms_name}' not found in terms")
        
        # Validate waterfall scenario references
        for idx, scenario in enumerate(data.get("waterfall_scenarios", [])):
            for payout_idx, payout in enumerate(scenario.get("payouts", [])):
                class_name = payout.get("class_name")
                if class_name and class_name not in class_names:
                    errors.append(
                        f"WaterfallScenario {idx}, payout {payout_idx}: "
                        f"class_name '{class_name}' not found in classes"
                    )
        
        return errors
    
    def _validate_feo_objects(self, data: Dict[str, Any]) -> List[str]:
        """Validate Formula Encoding Objects are well-formed."""
        errors = []
        
        def check_feo(obj: Any, path: str):
            """Recursively check for FEO objects."""
            if isinstance(obj, dict):
                if obj.get("is_calculated") is True:
                    # This is an FEO
                    if not obj.get("formula_string"):
                        errors.append(f"{path}: FEO missing formula_string")
                    if not isinstance(obj.get("dependency_refs"), list):
                        errors.append(f"{path}: FEO dependency_refs must be an array")
                    if not obj.get("output_type"):
                        errors.append(f"{path}: FEO missing output_type")
                    
                    # Validate dependency_refs structure
                    for dep_idx, dep in enumerate(obj.get("dependency_refs", [])):
                        if not isinstance(dep, dict):
                            errors.append(f"{path}.dependency_refs[{dep_idx}]: must be object")
                            continue
                        if not dep.get("placeholder"):
                            errors.append(f"{path}.dependency_refs[{dep_idx}]: missing placeholder")
                        if not dep.get("path"):
                            errors.append(f"{path}.dependency_refs[{dep_idx}]: missing path")
                else:
                    # Recursively check nested objects
                    for key, value in obj.items():
                        check_feo(value, f"{path}.{key}")
            elif isinstance(obj, list):
                for idx, item in enumerate(obj):
                    check_feo(item, f"{path}[{idx}]")
        
        check_feo(data, "root")
        return errors
    
    def _validate_name_uniqueness(self, data: Dict[str, Any]) -> List[str]:
        """Validate all names are unique within entity type."""
        errors = []
        
        # Define entity types and their name fields
        entity_types = [
            ("holders", "name"),
            ("classes", "name"),
            ("terms", "name"),
            ("rounds", "name"),
            ("waterfall_scenarios", "name")
        ]
        
        for entity_key, name_field in entity_types:
            entities = data.get(entity_key, [])
            seen_names = set()
            
            for idx, entity in enumerate(entities):
                name = entity.get(name_field)
                if name:
                    if not isinstance(name, str):
                        errors.append(f"{entity_key}[{idx}]: {name_field} must be a string")
                        continue
                        
                    if name in seen_names:
                        errors.append(f"{entity_key}[{idx}]: Duplicate {name_field} '{name}'")
                    seen_names.add(name)
                else:
                    errors.append(f"{entity_key}[{idx}]: Missing required field '{name_field}'")
        
        return errors


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

