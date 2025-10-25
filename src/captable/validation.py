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
            errors.extend(self._validate_uuids(data))
            
        return (len(errors) == 0, errors)
    
    def _format_error(self, error: ValidationError) -> str:
        """Format validation error for readability."""
        path = " -> ".join(str(p) for p in error.path) if error.path else "root"
        return f"Validation error at {path}: {error.message}"
    
    def _validate_relationships(self, data: Dict[str, Any]) -> List[str]:
        """Validate foreign key relationships between entities."""
        errors = []
        
        # Collect all IDs
        holder_ids = {h["holder_id"] for h in data.get("holders", [])}
        class_ids = {c["class_id"] for c in data.get("classes", [])}
        terms_ids = {t["terms_id"] for t in data.get("terms", [])}
        round_ids = {r["round_id"] for r in data.get("rounds", [])}
        
        # Validate instrument references
        for idx, instrument in enumerate(data.get("instruments", [])):
            holder_id = instrument.get("holder_id")
            if holder_id and holder_id not in holder_ids:
                errors.append(f"Instrument {idx}: holder_id '{holder_id}' not found in holders")
                
            class_id = instrument.get("class_id")
            if class_id and class_id not in class_ids:
                errors.append(f"Instrument {idx}: class_id '{class_id}' not found in classes")
                
            round_id = instrument.get("round_id")
            if round_id and round_id not in round_ids:
                errors.append(f"Instrument {idx}: round_id '{round_id}' not found in rounds")
        
        # Validate class -> terms references
        for idx, sec_class in enumerate(data.get("classes", [])):
            terms_id = sec_class.get("terms_id")
            if terms_id and terms_id not in terms_ids:
                errors.append(f"SecurityClass {idx}: terms_id '{terms_id}' not found in terms")
        
        # Validate waterfall scenario references
        for idx, scenario in enumerate(data.get("waterfall_scenarios", [])):
            for payout_idx, payout in enumerate(scenario.get("payouts", [])):
                class_id = payout.get("class_id")
                if class_id and class_id not in class_ids:
                    errors.append(
                        f"WaterfallScenario {idx}, payout {payout_idx}: "
                        f"class_id '{class_id}' not found in classes"
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
    
    def _validate_uuids(self, data: Dict[str, Any]) -> List[str]:
        """Validate all UUIDs are properly formatted and unique within entity type."""
        errors = []
        uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
        
        def check_uuid_format(uuid_str: str, entity_type: str, idx: int):
            if not uuid_pattern.match(uuid_str):
                errors.append(f"{entity_type}[{idx}]: Invalid UUID format '{uuid_str}'")
        
        # Check uniqueness within each entity type
        entity_types = [
            ("holders", "holder_id"),
            ("classes", "class_id"),
            ("terms", "terms_id"),
            ("instruments", "instrument_id"),
            ("rounds", "round_id"),
            ("waterfall_scenarios", "scenario_id")
        ]
        
        for entity_key, id_field in entity_types:
            entities = data.get(entity_key, [])
            seen_ids = set()
            
            for idx, entity in enumerate(entities):
                entity_id = entity.get(id_field)
                if entity_id:
                    check_uuid_format(entity_id, entity_key, idx)
                    
                    if entity_id in seen_ids:
                        errors.append(f"{entity_key}[{idx}]: Duplicate {id_field} '{entity_id}'")
                    seen_ids.add(entity_id)
        
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

