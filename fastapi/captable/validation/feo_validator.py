"""
FEO (Formula Encoding Object) Validation Module

Validates that FEO objects are well-formed and structurally correct.
"""

from typing import Dict, List, Any


class FEOValidator:
    """
    Validates Formula Encoding Objects (FEOs).
    
    FEOs are special objects that represent calculated Excel formulas.
    They must have:
    - is_calculated: true
    - formula_string: Excel formula with placeholders
    - dependency_refs: Array of dependency references
    - output_type: Type of output value
    """
    
    def validate(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate all FEO objects in the data structure.
        
        Args:
            data: Cap table JSON data
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        self._check_feo(data, "root", errors)
        return errors
    
    def _check_feo(self, obj: Any, path: str, errors: List[str]) -> None:
        """
        Recursively check for FEO objects and validate their structure.
        
        Args:
            obj: Object to check
            path: Current path in the data structure
            errors: List to append errors to
        """
        if isinstance(obj, dict):
            if obj.get("is_calculated") is True:
                # This is an FEO
                self._validate_feo_structure(obj, path, errors)
            else:
                # Recursively check nested objects
                for key, value in obj.items():
                    self._check_feo(value, f"{path}.{key}", errors)
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
                self._check_feo(item, f"{path}[{idx}]", errors)
    
    def _validate_feo_structure(self, feo: Dict[str, Any], path: str, errors: List[str]) -> None:
        """
        Validate an individual FEO structure.
        
        Args:
            feo: FEO object to validate
            path: Path to this FEO in the data structure
            errors: List to append errors to
        """
        if not feo.get("formula_string"):
            errors.append(f"{path}: FEO missing formula_string")
        
        if not isinstance(feo.get("dependency_refs"), list):
            errors.append(f"{path}: FEO dependency_refs must be an array")
        
        if not feo.get("output_type"):
            errors.append(f"{path}: FEO missing output_type")
        
        # Validate dependency_refs structure
        for dep_idx, dep in enumerate(feo.get("dependency_refs", [])):
            if not isinstance(dep, dict):
                errors.append(f"{path}.dependency_refs[{dep_idx}]: must be object")
                continue
            
            if not dep.get("placeholder"):
                errors.append(f"{path}.dependency_refs[{dep_idx}]: missing placeholder")
            
            if not dep.get("path"):
                errors.append(f"{path}.dependency_refs[{dep_idx}]: missing path")

