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
    - Pro-rata allocation validation (exercise type, partial exercise requirements)
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
        errors.extend(self._validate_pro_rata_allocations(data))
        errors.extend(self._validate_dilution_method(data))

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
                        errors.append(
                            f"{entity_key}[{idx}]: {name_field} must be a string")
                        continue

                    if name in seen_names:
                        errors.append(
                            f"{entity_key}[{idx}]: Duplicate {name_field} '{name}'")
                    seen_names.add(name)
                else:
                    errors.append(
                        f"{entity_key}[{idx}]: Missing required field '{name_field}'")

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
                errors.append(
                    f"Round '{round_name}': Missing required 'calculation_type'")
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
        allowed_fields = {
            "holder_name", "class_name", "pro_rata_type", "pro_rata_percentage",
            "exercise_type", "partial_exercise_amount", "partial_exercise_percentage"
        }
        instrument_fields = set(instrument.keys())

        # If the instrument has any fields beyond the allowed ones, it's not just a pro rata allocation
        if instrument_fields - allowed_fields:
            return False

        return True

    def _is_anti_dilution_allocation(self, instrument: Dict[str, Any]) -> bool:
        """
        Check if an instrument is an anti-dilution allocation.

        An anti-dilution allocation is a separate instrument with only holder_name, class_name, and dilution_method.
        It may optionally have anti_dilution_rounds.

        Args:
            instrument: Instrument dictionary

        Returns:
            True if this is an anti-dilution allocation, False otherwise
        """
        # Anti-dilution allocations have dilution_method and only basic fields
        if "dilution_method" not in instrument:
            return False

        # Check that it only has the allowed fields for anti-dilution allocations
        # Note: If the instrument has other fields like investment_amount, it's a regular instrument
        # with anti-dilution protection, not a standalone anti-dilution allocation
        allowed_fields = {
            "holder_name", "class_name", "dilution_method", "original_investment_round", "anti_dilution_rounds"
        }
        instrument_fields = set(instrument.keys())

        # If the instrument has any fields beyond the allowed ones, it's not just an anti-dilution allocation
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

        Note: Pro rata allocations (holder_name, class_name, pro_rata_type) and
        anti-dilution allocations (holder_name, class_name, dilution_method) are valid
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

                # Skip validation for anti-dilution allocations
                if self._is_anti_dilution_allocation(instrument):
                    continue

                # Validate pro_rata_rights if present on regular instruments
                pro_rata_rights = instrument.get("pro_rata_rights")
                if pro_rata_rights == "super":
                    pro_rata_percentage = instrument.get("pro_rata_percentage")
                    if not pro_rata_percentage or pro_rata_percentage <= 0 or pro_rata_percentage >= 1:
                        errors.append(
                            f"Round '{round_name}', Instrument {inst_idx} ({holder_name}/{class_name}): "
                            f"pro_rata_percentage must be greater than 0 and less than 100% when pro_rata_rights is 'super'"
                        )

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
                    # ConvertibleInstrument requires: investment_amount, interest_rate, payment_date, expected_conversion_date, interest_type
                    # discount_rate is optional (can be 0% or omitted)
                    required_fields = ["investment_amount", "interest_rate", "payment_date",
                                       "expected_conversion_date", "interest_type"]
                    # Support backward compatibility with old field names
                    if "payment_date" not in instrument and "interest_start_date" in instrument:
                        # Old format - allow but prefer new
                        pass
                    if "expected_conversion_date" not in instrument and "interest_end_date" in instrument:
                        # Old format - allow but prefer new
                        pass
                    missing_fields = [
                        f for f in required_fields if f not in instrument]

                    if missing_fields:
                        errors.append(
                            f"Round '{round_name}', Instrument {inst_idx} ({holder_name}/{class_name}): "
                            f"convertible type requires: {', '.join(missing_fields)}"
                        )

                    # Validate valuation_cap and valuation_cap_type consistency
                    valuation_cap = instrument.get('valuation_cap')
                    valuation_cap_type = instrument.get(
                        'valuation_cap_type', 'default')

                    if valuation_cap is not None and valuation_cap_type == 'default':
                        errors.append(
                            f"Round '{round_name}', Instrument {inst_idx} ({holder_name}/{class_name}): "
                            f"valuation_cap cannot be provided when valuation_cap_type is 'default' (use round-level cap)"
                        )

                    if valuation_cap is None and valuation_cap_type != 'default':
                        errors.append(
                            f"Round '{round_name}', Instrument {inst_idx} ({holder_name}/{class_name}): "
                            f"valuation_cap must be provided when valuation_cap_type is '{valuation_cap_type}'"
                        )

                elif calc_type == "safe":
                    # SafeInstrument requires: investment_amount, expected_conversion_date
                    # discount_rate is optional (can be 0% or omitted)
                    required_fields = ["investment_amount",
                                       "expected_conversion_date"]
                    missing_fields = [
                        f for f in required_fields if f not in instrument]

                    if missing_fields:
                        errors.append(
                            f"Round '{round_name}', Instrument {inst_idx} ({holder_name}/{class_name}): "
                            f"safe type requires: {', '.join(missing_fields)}"
                        )

                    # Validate valuation_cap and valuation_cap_type consistency
                    valuation_cap = instrument.get('valuation_cap')
                    valuation_cap_type = instrument.get(
                        'valuation_cap_type', 'default')

                    if valuation_cap is not None and valuation_cap_type == 'default':
                        errors.append(
                            f"Round '{round_name}', Instrument {inst_idx} ({holder_name}/{class_name}): "
                            f"valuation_cap cannot be provided when valuation_cap_type is 'default' (use round-level cap)"
                        )

                    if valuation_cap is None and valuation_cap_type != 'default':
                        errors.append(
                            f"Round '{round_name}', Instrument {inst_idx} ({holder_name}/{class_name}): "
                            f"valuation_cap must be provided when valuation_cap_type is '{valuation_cap_type}'"
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
                    start_date_str = instrument.get(
                        "payment_date") or instrument.get("interest_start_date")
                    end_date_str = instrument.get(
                        "expected_conversion_date") or instrument.get("interest_end_date")

                    if start_date_str and end_date_str:
                        try:
                            start_date = datetime.strptime(
                                start_date_str, "%Y-%m-%d")
                            end_date = datetime.strptime(
                                end_date_str, "%Y-%m-%d")

                            if end_date <= start_date:
                                errors.append(
                                    f"Round '{round_name}', Instrument {inst_idx} ({holder_name}): "
                                    f"expected_conversion_date (or interest_end_date) must be after payment_date (or interest_start_date)"
                                )
                        except ValueError:
                            # Date format errors will be caught by schema validation
                            pass

        return errors

    def _validate_pro_rata_allocations(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate pro-rata allocation fields and exercise type requirements.

        Validates:
        - exercise_type must be "full" or "partial"
        - For "full" exercise: partial_exercise_amount and partial_exercise_percentage should not be provided
        - For "partial" exercise: at least one of partial_exercise_amount or partial_exercise_percentage must be provided
        - If partial_exercise_amount is provided, the round must have a valuation

        Args:
            data: Cap table JSON data

        Returns:
            List of error messages
        """
        errors = []
        rounds = data.get("rounds", [])

        for round_idx, round_data in enumerate(rounds):
            round_name = round_data.get("name", f"Round {round_idx}")
            instruments = round_data.get("instruments", [])
            round_valuation = round_data.get("valuation")

            for inst_idx, instrument in enumerate(instruments):
                # Only validate pro-rata allocations
                if not self._is_pro_rata_allocation(instrument):
                    continue

                holder_name = instrument.get("holder_name", "Unknown")
                exercise_type = instrument.get("exercise_type")
                partial_amount = instrument.get("partial_exercise_amount")
                partial_percentage = instrument.get(
                    "partial_exercise_percentage")

                # Validate exercise_type
                if not exercise_type:
                    errors.append(
                        f"Round '{round_name}', Pro-rata Allocation {inst_idx} ({holder_name}): "
                        f"exercise_type is required and must be 'full' or 'partial'"
                    )
                    continue

                if exercise_type not in ["full", "partial"]:
                    errors.append(
                        f"Round '{round_name}', Pro-rata Allocation {inst_idx} ({holder_name}): "
                        f"exercise_type must be 'full' or 'partial', got '{exercise_type}'"
                    )
                    continue

                # Validate based on exercise type
                if exercise_type == "full":
                    # For full exercise, partial exercise fields should not be provided
                    if partial_amount is not None:
                        errors.append(
                            f"Round '{round_name}', Pro-rata Allocation {inst_idx} ({holder_name}): "
                            f"partial_exercise_amount should not be provided when exercise_type is 'full'"
                        )

                    if partial_percentage is not None:
                        errors.append(
                            f"Round '{round_name}', Pro-rata Allocation {inst_idx} ({holder_name}): "
                            f"partial_exercise_percentage should not be provided when exercise_type is 'full'"
                        )

                elif exercise_type == "partial":
                    # For partial exercise, at least one partial exercise field must be provided
                    if partial_amount is None and partial_percentage is None:
                        errors.append(
                            f"Round '{round_name}', Pro-rata Allocation {inst_idx} ({holder_name}): "
                            f"Either partial_exercise_amount or partial_exercise_percentage must be provided for partial exercise"
                        )

                    # Validate partial_exercise_amount if provided
                    if partial_amount is not None:
                        if partial_amount <= 0:
                            errors.append(
                                f"Round '{round_name}', Pro-rata Allocation {inst_idx} ({holder_name}): "
                                f"partial_exercise_amount must be greater than 0"
                            )

                        # Partial exercise by amount requires a valuation
                        if not round_valuation or round_valuation <= 0:
                            errors.append(
                                f"Round '{round_name}', Pro-rata Allocation {inst_idx} ({holder_name}): "
                                f"Partial exercise by amount requires a valuation to be specified for the round"
                            )

                    # Validate partial_exercise_percentage if provided
                    if partial_percentage is not None:
                        if partial_percentage <= 0 or partial_percentage >= 1:
                            errors.append(
                                f"Round '{round_name}', Pro-rata Allocation {inst_idx} ({holder_name}): "
                                f"partial_exercise_percentage must be greater than 0 and less than 100%"
                            )

                        # For super pro-rata, validate that partial exercise percentage is lower than super pro-rata percentage
                        pro_rata_type = instrument.get("pro_rata_type")
                        pro_rata_percentage = instrument.get(
                            "pro_rata_percentage")
                        if pro_rata_type == "super" and pro_rata_percentage is not None:
                            if partial_percentage >= pro_rata_percentage:
                                errors.append(
                                    f"Round '{round_name}', Pro-rata Allocation {inst_idx} ({holder_name}): "
                                    f"Partial exercise percentage must be lower than super pro-rata percentage"
                                )

        return errors

    def _validate_dilution_method(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate dilution_method field on instruments if provided.

        Valid dilution methods:
        - full_ratchet
        - percentage_based
        - narrow_based_weighted_average
        - broad_based_weighted_average

        Also validates that each holder has only one anti-dilution instrument per round.

        Args:
            data: Cap table JSON data

        Returns:
            List of error messages
        """
        errors = []
        rounds = data.get("rounds", [])
        valid_dilution_methods = {
            "full_ratchet",
            "percentage_based",
            "narrow_based_weighted_average",
            "broad_based_weighted_average",
        }

        for round_idx, round_data in enumerate(rounds):
            round_name = round_data.get("name", f"Round {round_idx}")
            instruments = round_data.get("instruments", [])

            # Track holders with anti-dilution instruments
            holder_anti_dilution_count: Dict[str, List[int]] = {}

            for inst_idx, instrument in enumerate(instruments):
                # Skip pro-rata allocations as they don't have dilution_method
                if "pro_rata_type" in instrument:
                    continue

                dilution_method = instrument.get("dilution_method")

                if dilution_method is not None:
                    if dilution_method not in valid_dilution_methods:
                        holder_name = instrument.get("holder_name", "Unknown")
                        errors.append(
                            f"Round '{round_name}', Instrument '{holder_name}': Invalid dilution_method '{dilution_method}'. "
                            f"Must be one of: {', '.join(sorted(valid_dilution_methods))}"
                        )
                    else:
                        # Validate original_investment_round for anti-dilution allocations
                        if self._is_anti_dilution_allocation(instrument):
                            original_investment_round = instrument.get("original_investment_round")
                            if not original_investment_round:
                                holder_name = instrument.get("holder_name", "Unknown")
                                errors.append(
                                    f"Round '{round_name}', Instrument '{holder_name}': "
                                    f"Anti-dilution allocation requires 'original_investment_round' field"
                                )
                            else:
                                # Check that the original_investment_round exists and is before current round
                                round_names = [r.get("name") for r in rounds]
                                if original_investment_round not in round_names:
                                    holder_name = instrument.get("holder_name", "Unknown")
                                    errors.append(
                                        f"Round '{round_name}', Instrument '{holder_name}': "
                                        f"original_investment_round '{original_investment_round}' does not exist"
                                    )
                                else:
                                    original_round_idx = round_names.index(original_investment_round)
                                    if original_round_idx >= round_idx:
                                        holder_name = instrument.get("holder_name", "Unknown")
                                        errors.append(
                                            f"Round '{round_name}', Instrument '{holder_name}': "
                                            f"original_investment_round '{original_investment_round}' must be before the current round"
                                        )
                        
                        # Track this holder's anti-dilution instrument
                        holder_name = instrument.get("holder_name")
                        if holder_name:
                            if holder_name not in holder_anti_dilution_count:
                                holder_anti_dilution_count[holder_name] = []
                            holder_anti_dilution_count[holder_name].append(inst_idx)

            # Check for multiple anti-dilution instruments per holder
            for holder_name, instrument_indices in holder_anti_dilution_count.items():
                if len(instrument_indices) > 1:
                    errors.append(
                        f"Round '{round_name}', Holder '{holder_name}': "
                        f"Each holder can have only one anti-dilution instrument per round. "
                        f"Found {len(instrument_indices)} anti-dilution instruments at indices: {', '.join(map(str, instrument_indices))}"
                    )

        return errors
