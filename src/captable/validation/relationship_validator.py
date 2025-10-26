"""
Relationship Validation Module

Validates foreign key relationships between entities in round-based architecture.
"""

from typing import Dict, List, Any


class RelationshipValidator:
    """
    Validates foreign key relationships between entities in round-based architecture.
    
    In the new architecture, instruments are nested within rounds, so round_name
    foreign key validation is no longer needed. This validator ensures:
    - Holder and class name references are consistent (if holders/classes are defined)
    - No orphaned references exist
    """
    
    def validate(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate all foreign key relationships.
        
        Args:
            data: Cap table JSON data
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # With nested instruments, no round_name validation needed
        # Instruments are automatically associated with their containing round
        
        # Validate holder_name and class_name references if holders/classes arrays exist
        holder_names = {h.get("name") for h in data.get("holders", []) if h.get("name")}
        class_names = {c.get("name") for c in data.get("classes", []) if c.get("name")}
        
        # Only validate if holders or classes arrays are present
        if holder_names or class_names:
            rounds = data.get("rounds", [])
            for round_idx, round_data in enumerate(rounds):
                round_name = round_data.get("name", f"Round {round_idx}")
                instruments = round_data.get("instruments", [])
                
                for inst_idx, instrument in enumerate(instruments):
                    # Validate holder_name if holders array exists
                    if holder_names:
                        holder_name = instrument.get("holder_name")
                        if holder_name and holder_name not in holder_names:
                            errors.append(
                                f"Round '{round_name}', Instrument {inst_idx}: "
                                f"holder_name '{holder_name}' not found in holders"
                            )
                    
                    # Validate class_name if classes array exists
                    if class_names:
                        class_name = instrument.get("class_name")
                        if class_name and class_name not in class_names:
                            errors.append(
                                f"Round '{round_name}', Instrument {inst_idx}: "
                                f"class_name '{class_name}' not found in classes"
                            )
        
        return errors

