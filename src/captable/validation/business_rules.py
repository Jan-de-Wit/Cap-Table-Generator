"""
Business Rules Validation Module

Validates business logic rules beyond schema compliance for round-based architecture.
"""

from typing import Dict, List, Any
from datetime import datetime


class BusinessRulesValidator:
    """
    Validates business rules for cap table data with round-based architecture.
    
    Business rules include:
    - Name uniqueness within entity types
    - Round-level calculation type consistency
    - Instrument completeness based on round calculation type
    - Valuation data requirements for calculated rounds
    - Interest date validation
    """
    
    def validate(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate business rules.
        
        Args:
            data: Cap table JSON data
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        errors.extend(self._validate_name_uniqueness(data))
        errors.extend(self._validate_round_calculation_types(data))
        errors.extend(self._validate_instrument_completeness(data))
        errors.extend(self._validate_valuation_requirements(data))
        errors.extend(self._validate_interest_dates(data))
        
        return errors
    
    def _validate_name_uniqueness(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate that all names are unique within their entity type.
        
        Args:
            data: Cap table JSON data
            
        Returns:
            List of error messages
        """
        errors = []
        
        # Define entity types and their name fields
        entity_types = [
            ("rounds", "name"),
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
    
    def _validate_round_calculation_types(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate round-level calculation types and consistency.
        
        Args:
            data: Cap table JSON data
            
        Returns:
            List of error messages
        """
        errors = []
        rounds = data.get("rounds", [])
        
        for round_idx, round_data in enumerate(rounds):
            round_name = round_data.get("name", f"Round {round_idx}")
            calc_type = round_data.get("calculation_type")
            
            if not calc_type:
                errors.append(f"Round '{round_name}': Missing required 'calculation_type'")
                continue
            
            # Validate convertible-specific fields
            if calc_type == "convertible":
                if "valuation_basis" not in round_data:
                    errors.append(
                        f"Round '{round_name}': Convertible rounds must have 'valuation_basis' "
                        f"(pre_money or post_money)"
                    )
            
            # Validate SAFE-specific fields
            if calc_type == "safe":
                if "valuation_basis" not in round_data:
                    errors.append(
                        f"Round '{round_name}': SAFE rounds must have 'valuation_basis' "
                        f"(pre_money or post_money)"
                    )
        
        return errors
    
    def _is_pro_rata_allocation(self, instrument: Dict[str, Any]) -> bool:
        """
        Check if an instrument is a pro rata allocation.
        
        A pro rata allocation is a separate instrument with only holder_name, class_name, and pro_rata_type.
        It may optionally have pro_rata_percentage (required for super type).
        
        Args:
            instrument: Instrument dictionary
            
        Returns:
            True if this is a pro rata allocation, False otherwise
        """
        # Pro rata allocations have pro_rata_type and only basic fields
        if "pro_rata_type" not in instrument:
            return False
        
        # Check that it only has the allowed fields for pro rata allocations
        allowed_fields = {"holder_name", "class_name", "pro_rata_type", "pro_rata_percentage"}
        instrument_fields = set(instrument.keys())
        
        # If the instrument has any fields beyond the allowed ones, it's not just a pro rata allocation
        if instrument_fields - allowed_fields:
            return False
        
        return True
    
    def _validate_instrument_completeness(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate that instruments have necessary data based on their round's calculation type.
        
        Calculation types and required fields:
        1. fixed_shares: Requires initial_quantity
        2. target_percentage: Requires target_percentage
        3. valuation_based: Requires investment_amount
        4. convertible: Requires investment_amount, interest_rate, payment_date, expected_conversion_date, interest_type, discount_rate
        5. safe: Requires investment_amount, expected_conversion_date, discount_rate
        
        Note: Pro rata allocations (holder_name, class_name, pro_rata_type) are valid
        for any round type and skip the above validation.
        
        Args:
            data: Cap table JSON data
            
        Returns:
            List of error messages
        """
        errors = []
        rounds = data.get("rounds", [])
        
        for round_idx, round_data in enumerate(rounds):
            round_name = round_data.get("name", f"Round {round_idx}")
            calc_type = round_data.get("calculation_type")
            instruments = round_data.get("instruments", [])
            
            if not calc_type:
                continue  # Already caught in _validate_round_calculation_types
            
            for inst_idx, instrument in enumerate(instruments):
                holder_name = instrument.get("holder_name", "Unknown")
                class_name = instrument.get("class_name", "Unknown")
                
                # Skip validation for pro rata allocations
                if self._is_pro_rata_allocation(instrument):
                    continue
                
                # Validate based on calculation type
                if calc_type == "fixed_shares":
                    if "initial_quantity" not in instrument:
                        errors.append(
                            f"Round '{round_name}', Instrument {inst_idx} ({holder_name}/{class_name}): "
                            f"fixed_shares type requires 'initial_quantity'"
                        )
                
                elif calc_type == "target_percentage":
                    if "target_percentage" not in instrument:
                        errors.append(
                            f"Round '{round_name}', Instrument {inst_idx} ({holder_name}/{class_name}): "
                            f"target_percentage type requires 'target_percentage'"
                        )
                
                elif calc_type == "valuation_based":
                    if "investment_amount" not in instrument:
                        errors.append(
                            f"Round '{round_name}', Instrument {inst_idx} ({holder_name}/{class_name}): "
                            f"valuation_based type requires 'investment_amount'"
                        )
                
                elif calc_type == "convertible":
                    # ConvertibleInstrument requires: investment_amount, interest_rate, payment_date, expected_conversion_date, interest_type, discount_rate
                    required_fields = ["investment_amount", "interest_rate", "payment_date", "expected_conversion_date", "interest_type", "discount_rate"]
                    # Support backward compatibility with old field names
                    if "payment_date" not in instrument and "interest_start_date" in instrument:
                        # Old format - allow but prefer new
                        pass
                    if "expected_conversion_date" not in instrument and "interest_end_date" in instrument:
                        # Old format - allow but prefer new
                        pass
                    missing_fields = [f for f in required_fields if f not in instrument]
                    
                    if missing_fields:
                        errors.append(
                            f"Round '{round_name}', Instrument {inst_idx} ({holder_name}/{class_name}): "
                            f"convertible type requires: {', '.join(missing_fields)}"
                        )
                
                elif calc_type == "safe":
                    # SafeInstrument requires: investment_amount, expected_conversion_date, discount_rate
                    required_fields = ["investment_amount", "expected_conversion_date", "discount_rate"]
                    missing_fields = [f for f in required_fields if f not in instrument]
                    
                    if missing_fields:
                        errors.append(
                            f"Round '{round_name}', Instrument {inst_idx} ({holder_name}/{class_name}): "
                            f"safe type requires: {', '.join(missing_fields)}"
                        )
        
        return errors
    
    def _validate_valuation_requirements(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate that rounds have necessary valuation data for their calculation type.
        
        Args:
            data: Cap table JSON data
            
        Returns:
            List of error messages
        """
        errors = []
        rounds = data.get("rounds", [])
        
        for idx, round_data in enumerate(rounds):
            round_name = round_data.get("name", f"Round {idx}")
            calc_type = round_data.get("calculation_type")
            
            if not calc_type:
                continue  # Already caught in _validate_round_calculation_types
            
            # valuation_based, convertible, and safe types need valuation data
            if calc_type in ["valuation_based", "convertible", "safe"]:
                has_valuation = "valuation" in round_data
                has_price_per_share = "price_per_share" in round_data
                
                if not (has_valuation or has_price_per_share):
                    errors.append(
                        f"Round '{round_name}': {calc_type} type requires either 'valuation' or 'price_per_share'"
                    )
        
        return errors
    
    def _validate_interest_dates(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate that interest_end_date is after interest_start_date for convertible instruments.
        (SAFE instruments do not require interest dates.)
        
        Args:
            data: Cap table JSON data
            
        Returns:
            List of error messages
        """
        errors = []
        rounds = data.get("rounds", [])
        
        for round_idx, round_data in enumerate(rounds):
            round_name = round_data.get("name", f"Round {round_idx}")
            calc_type = round_data.get("calculation_type")
            instruments = round_data.get("instruments", [])
            
            if calc_type == "convertible":
                for inst_idx, instrument in enumerate(instruments):
                    holder_name = instrument.get("holder_name", "Unknown")
                    # Support both new and old field names
                    start_date_str = instrument.get("payment_date") or instrument.get("interest_start_date")
                    end_date_str = instrument.get("expected_conversion_date") or instrument.get("interest_end_date")
                    
                    if start_date_str and end_date_str:
                        try:
                            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
                            
                            if end_date <= start_date:
                                errors.append(
                                    f"Round '{round_name}', Instrument {inst_idx} ({holder_name}): "
                                    f"expected_conversion_date (or interest_end_date) must be after payment_date (or interest_start_date)"
                                )
                        except ValueError:
                            # Date format errors will be caught by schema validation
                            pass
        
        return errors

