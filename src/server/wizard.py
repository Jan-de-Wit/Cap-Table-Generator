import streamlit as st
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# Initialize session state
if "holders" not in st.session_state:
    st.session_state.holders = []
if "rounds" not in st.session_state:
    st.session_state.rounds = []
if "current_step" not in st.session_state:
    st.session_state.current_step = 1
if "editing_holder_idx" not in st.session_state:
    st.session_state.editing_holder_idx = None
if "editing_round_idx" not in st.session_state:
    st.session_state.editing_round_idx = None
if "adding_instrument" not in st.session_state:
    st.session_state.adding_instrument = {}
if "editing_instrument" not in st.session_state:
    st.session_state.editing_instrument = {}
if "adding_pro_rata" not in st.session_state:
    st.session_state.adding_pro_rata = {}
if "editing_pro_rata" not in st.session_state:
    st.session_state.editing_pro_rata = {}

# Calculation types and their required fields
CALCULATION_TYPES = {
    "fixed_shares": "Fixed Shares",
    "target_percentage": "Target Percentage",
    "valuation_based": "Valuation Based",
    "convertible": "Convertible Note",
    "safe": "SAFE"
}

INTEREST_TYPES = ["simple", "compound_yearly",
    "compound_monthly", "compound_daily", "no_interest"]
VALUATION_BASIS_OPTIONS = ["pre_money", "post_money"]
PRO_RATA_TYPES = ["standard", "super"]


def get_holder_names() -> List[str]:
    """Get list of all holder names."""
    return [h["name"] for h in st.session_state.holders]


def get_class_names_for_round(round_idx: int) -> List[str]:
    """Get list of class names used in a specific round."""
    if round_idx >= len(st.session_state.rounds):
        return []
    round_data = st.session_state.rounds[round_idx]
    class_names = set()
    for instrument in round_data.get("instruments", []):
        if "class_name" in instrument:
            class_names.add(instrument["class_name"])
    return sorted(list(class_names))


def render_holder_form(holder: Optional[Dict[str, Any]] = None, idx: Optional[int] = None):
    """Render form for adding/editing a holder."""
    is_edit = holder is not None

    with st.form(key=f"holder_form_{idx if idx is not None else 'new'}"):
        name = st.text_input("Name *", value=holder.get("name", "")
                             if holder else "", key=f"holder_name_{idx}")
        group = st.text_input("Group (optional)", value=holder.get(
            "group", "") if holder else "", key=f"holder_group_{idx}")
        description = st.text_area("Description (optional)", value=holder.get(
            "description", "") if holder else "", key=f"holder_desc_{idx}")

        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Save", use_container_width=True):
                if not name:
                    st.error("Name is required")
                elif not is_edit and any(h["name"] == name for h in st.session_state.holders):
                    st.error("Holder with this name already exists")
                else:
                    holder_data = {"name": name}
                    if group:
                        holder_data["group"] = group
                    if description:
                        holder_data["description"] = description

                    if is_edit and idx is not None:
                        st.session_state.holders[idx] = holder_data
                        st.session_state.editing_holder_idx = None
                    else:
                        st.session_state.holders.append(holder_data)
                    st.rerun()
        with col2:
            if is_edit and st.form_submit_button("Cancel", use_container_width=True):
                st.session_state.editing_holder_idx = None
                st.rerun()


def render_instrument_form(round_idx: int, instrument_idx: Optional[int] = None, instrument: Optional[Dict[str, Any]] = None):
    """Render form for adding/editing an instrument."""
    is_edit = instrument is not None
    round_data = st.session_state.rounds[round_idx]
    calculation_type = round_data.get("calculation_type")

    with st.form(key=f"instrument_form_{round_idx}_{instrument_idx if instrument_idx is not None else 'new'}"):
        holder_names = get_holder_names()
        if not holder_names:
            st.warning("Please add holders first before adding instruments.")
            st.form_submit_button("Close", use_container_width=True)
            return

        holder_name = st.selectbox(
            "Holder *",
            holder_names,
            index=holder_names.index(instrument.get("holder_name")) if instrument and instrument.get(
                "holder_name") in holder_names else 0,
            key=f"instrument_holder_{round_idx}_{instrument_idx}"
        )

        class_name = st.text_input(
            "Class Name *",
            value=instrument.get("class_name", "") if instrument else "",
            key=f"instrument_class_{round_idx}_{instrument_idx}"
        )

        # Fields based on calculation type
        if calculation_type == "fixed_shares":
            initial_quantity = st.number_input(
                "Initial Quantity *",
                min_value=0.0,
                value=float(instrument.get("initial_quantity", 0)
                            ) if instrument else 0.0,
                key=f"instrument_quantity_{round_idx}_{instrument_idx}"
            )
        elif calculation_type == "target_percentage":
            target_percentage = st.number_input(
                "Target Percentage *",
                min_value=0.0,
                max_value=1.0,
                value=float(instrument.get("target_percentage", 0)
                            ) if instrument else 0.0,
                step=0.01,
                format="%.2f",
                key=f"instrument_target_{round_idx}_{instrument_idx}"
            )
        elif calculation_type == "valuation_based":
            investment_amount = st.number_input(
                "Investment Amount *",
                min_value=0.0,
                value=float(instrument.get("investment_amount", 0)
                            ) if instrument else 0.0,
                key=f"instrument_investment_{round_idx}_{instrument_idx}"
            )
        elif calculation_type == "convertible":
            investment_amount = st.number_input(
                "Investment Amount *",
                min_value=0.0,
                value=float(instrument.get("investment_amount", 0)
                            ) if instrument else 0.0,
                key=f"instrument_investment_{round_idx}_{instrument_idx}"
            )
            interest_rate = st.number_input(
                "Interest Rate *",
                min_value=0.0,
                max_value=1.0,
                value=float(instrument.get("interest_rate", 0)
                            ) if instrument else 0.0,
                step=0.01,
                format="%.2f",
                key=f"instrument_interest_rate_{round_idx}_{instrument_idx}"
            )
            interest_type = st.selectbox(
                "Interest Type *",
                INTEREST_TYPES,
                index=INTEREST_TYPES.index(instrument.get("interest_type", "simple")) if instrument and instrument.get(
                    "interest_type") in INTEREST_TYPES else 0,
                key=f"instrument_interest_type_{round_idx}_{instrument_idx}"
            )
            payment_date = st.date_input(
                "Payment Date *",
                value=datetime.strptime(instrument.get("payment_date", "2024-01-01"), "%Y-%m-%d").date(
                ) if instrument and instrument.get("payment_date") else datetime.now().date(),
                key=f"instrument_payment_date_{round_idx}_{instrument_idx}"
            )
            expected_conversion_date = st.date_input(
                "Expected Conversion Date *",
                value=datetime.strptime(instrument.get("expected_conversion_date", "2024-12-31"), "%Y-%m-%d").date(
                ) if instrument and instrument.get("expected_conversion_date") else datetime.now().date(),
                key=f"instrument_conversion_date_{round_idx}_{instrument_idx}"
            )
            discount_rate = st.number_input(
                "Discount Rate *",
                min_value=0.0,
                max_value=1.0,
                value=float(instrument.get("discount_rate", 0)
                            ) if instrument else 0.0,
                step=0.01,
                format="%.2f",
                key=f"instrument_discount_{round_idx}_{instrument_idx}"
            )
            valuation_cap = st.number_input(
                "Valuation Cap (optional)",
                min_value=0.0,
                value=float(instrument.get("valuation_cap", 0)) if instrument and instrument.get(
                    "valuation_cap") else 0.0,
                key=f"instrument_valuation_cap_{round_idx}_{instrument_idx}"
            )
            if valuation_cap > 0:
                valuation_cap_type = st.selectbox(
                    "Valuation Cap Type",
                    ["default", "pre_conversion",
                        "post_conversion_own", "post_conversion_total"],
                    index=["default", "pre_conversion", "post_conversion_own", "post_conversion_total"].index(instrument.get("valuation_cap_type", "default")) if instrument and instrument.get(
                        "valuation_cap_type") in ["default", "pre_conversion", "post_conversion_own", "post_conversion_total"] else 0,
                    key=f"instrument_valuation_cap_type_{round_idx}_{instrument_idx}"
                )
        elif calculation_type == "safe":
            investment_amount = st.number_input(
                "Investment Amount *",
                min_value=0.0,
                value=float(instrument.get("investment_amount", 0)
                            ) if instrument else 0.0,
                key=f"instrument_investment_{round_idx}_{instrument_idx}"
            )
            expected_conversion_date = st.date_input(
                "Expected Conversion Date *",
                value=datetime.strptime(instrument.get("expected_conversion_date", "2024-12-31"), "%Y-%m-%d").date(
                ) if instrument and instrument.get("expected_conversion_date") else datetime.now().date(),
                key=f"instrument_conversion_date_{round_idx}_{instrument_idx}"
            )
            discount_rate = st.number_input(
                "Discount Rate *",
                min_value=0.0,
                max_value=1.0,
                value=float(instrument.get("discount_rate", 0)
                            ) if instrument else 0.0,
                step=0.01,
                format="%.2f",
                key=f"instrument_discount_{round_idx}_{instrument_idx}"
            )
            valuation_cap = st.number_input(
                "Valuation Cap (optional)",
                min_value=0.0,
                value=float(instrument.get("valuation_cap", 0)) if instrument and instrument.get(
                    "valuation_cap") else 0.0,
                key=f"instrument_valuation_cap_{round_idx}_{instrument_idx}"
            )
            if valuation_cap > 0:
                valuation_cap_type = st.selectbox(
                    "Valuation Cap Type",
                    ["default", "pre_conversion",
                        "post_conversion_own", "post_conversion_total"],
                    index=["default", "pre_conversion", "post_conversion_own", "post_conversion_total"].index(instrument.get("valuation_cap_type", "default")) if instrument and instrument.get(
                        "valuation_cap_type") in ["default", "pre_conversion", "post_conversion_own", "post_conversion_total"] else 0,
                    key=f"instrument_valuation_cap_type_{round_idx}_{instrument_idx}"
                )

        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Save", use_container_width=True):
                if not class_name:
                    st.error("Class name is required")
                else:
                    instrument_data = {
                        "holder_name": holder_name,
                        "class_name": class_name
                    }

                    if calculation_type == "fixed_shares":
                        if initial_quantity <= 0:
                            st.error("Initial quantity must be greater than 0")
                            return
                        instrument_data["initial_quantity"] = int(
                            initial_quantity)
                    elif calculation_type == "target_percentage":
                        if target_percentage <= 0 or target_percentage > 1:
                            st.error(
                                "Target percentage must be between 0 and 1")
                            return
                        instrument_data["target_percentage"] = target_percentage
                    elif calculation_type == "valuation_based":
                        if investment_amount <= 0:
                            st.error(
                                "Investment amount must be greater than 0")
                            return
                        instrument_data["investment_amount"] = investment_amount
                    elif calculation_type == "convertible":
                        if investment_amount <= 0:
                            st.error(
                                "Investment amount must be greater than 0")
                            return
                        instrument_data["investment_amount"] = investment_amount
                        instrument_data["interest_rate"] = interest_rate
                        instrument_data["interest_type"] = interest_type
                        instrument_data["payment_date"] = payment_date.strftime(
                            "%Y-%m-%d")
                        instrument_data["expected_conversion_date"] = expected_conversion_date.strftime(
                            "%Y-%m-%d")
                        instrument_data["discount_rate"] = discount_rate
                        if valuation_cap > 0:
                            instrument_data["valuation_cap"] = valuation_cap
                            instrument_data["valuation_cap_type"] = valuation_cap_type
                    elif calculation_type == "safe":
                        if investment_amount <= 0:
                            st.error(
                                "Investment amount must be greater than 0")
                            return
                        instrument_data["investment_amount"] = investment_amount
                        instrument_data["expected_conversion_date"] = expected_conversion_date.strftime(
                            "%Y-%m-%d")
                        instrument_data["discount_rate"] = discount_rate
                        if valuation_cap > 0:
                            instrument_data["valuation_cap"] = valuation_cap
                            instrument_data["valuation_cap_type"] = valuation_cap_type

                    if is_edit and instrument_idx is not None:
                        st.session_state.rounds[round_idx]["instruments"][instrument_idx] = instrument_data
                        # Clear editing state
                        key = f"{round_idx}_{instrument_idx}"
                        if key in st.session_state.editing_instrument:
                            del st.session_state.editing_instrument[key]
                    else:
                        if "instruments" not in st.session_state.rounds[round_idx]:
                            st.session_state.rounds[round_idx]["instruments"] = [
                                ]
                        st.session_state.rounds[round_idx]["instruments"].append(
                            instrument_data)
                        # Clear adding state
                        if f"{round_idx}" in st.session_state.adding_instrument:
                            del st.session_state.adding_instrument[f"{round_idx}"]
                    st.rerun()
        with col2:
            if st.form_submit_button("Cancel", use_container_width=True):
                st.rerun()


def render_pro_rata_form(round_idx: int, pro_rata_idx: Optional[int] = None, pro_rata: Optional[Dict[str, Any]] = None):
    """Render form for adding/editing a pro rata allocation."""
    is_edit = pro_rata is not None
    round_data = st.session_state.rounds[round_idx]

    with st.form(key=f"pro_rata_form_{round_idx}_{pro_rata_idx if pro_rata_idx is not None else 'new'}"):
        holder_names = get_holder_names()
        if not holder_names:
            st.warning(
                "Please add holders first before adding pro rata allocations.")
            st.form_submit_button("Close", use_container_width=True)
            return

        class_names = get_class_names_for_round(round_idx)
        if not class_names:
            st.warning(
                "Please add instruments with class names first before adding pro rata allocations.")
            st.form_submit_button("Close", use_container_width=True)
            return

        holder_name = st.selectbox(
            "Holder *",
            holder_names,
            index=holder_names.index(pro_rata.get("holder_name")) if pro_rata and pro_rata.get(
                "holder_name") in holder_names else 0,
            key=f"pro_rata_holder_{round_idx}_{pro_rata_idx}"
        )

        class_name = st.selectbox(
            "Class Name *",
            class_names,
            index=class_names.index(pro_rata.get("class_name")) if pro_rata and pro_rata.get(
                "class_name") in class_names else 0,
            key=f"pro_rata_class_{round_idx}_{pro_rata_idx}"
        )

        pro_rata_type = st.selectbox(
            "Pro Rata Type *",
            PRO_RATA_TYPES,
            index=PRO_RATA_TYPES.index(pro_rata.get("pro_rata_type", "standard")) if pro_rata and pro_rata.get(
                "pro_rata_type") in PRO_RATA_TYPES else 0,
            key=f"pro_rata_type_{round_idx}_{pro_rata_idx}"
        )

        pro_rata_percentage = None
        if pro_rata_type == "super":
            pro_rata_percentage = st.number_input(
                "Pro Rata Percentage *",
                min_value=0.0,
                max_value=1.0,
                value=float(pro_rata.get("pro_rata_percentage", 0)) if pro_rata and pro_rata.get(
                    "pro_rata_percentage") else 0.0,
                step=0.01,
                format="%.2f",
                key=f"pro_rata_percentage_{round_idx}_{pro_rata_idx}"
            )

        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Save", use_container_width=True):
                pro_rata_data = {
                    "holder_name": holder_name,
                    "class_name": class_name,
                    "pro_rata_type": pro_rata_type
                }
                if pro_rata_type == "super":
                    if pro_rata_percentage is None or pro_rata_percentage <= 0 or pro_rata_percentage > 1:
                        st.error(
                            "Pro rata percentage must be between 0 and 1 for super pro rata")
                        return
                    pro_rata_data["pro_rata_percentage"] = pro_rata_percentage

                if is_edit and pro_rata_idx is not None:
                    st.session_state.rounds[round_idx]["instruments"][pro_rata_idx] = pro_rata_data
                    # Clear editing state
                    key = f"{round_idx}_{pro_rata_idx}"
                    if key in st.session_state.editing_pro_rata:
                        del st.session_state.editing_pro_rata[key]
                else:
                    if "instruments" not in st.session_state.rounds[round_idx]:
                        st.session_state.rounds[round_idx]["instruments"] = []
                    st.session_state.rounds[round_idx]["instruments"].append(
                        pro_rata_data)
                    # Clear adding state
                    if f"{round_idx}" in st.session_state.adding_pro_rata:
                        del st.session_state.adding_pro_rata[f"{round_idx}"]
                st.rerun()
        with col2:
            if st.form_submit_button("Cancel", use_container_width=True):
                st.rerun()


def render_round_form(round_data: Optional[Dict[str, Any]] = None, idx: Optional[int] = None):
    """Render form for adding/editing a round."""
    is_edit = round_data is not None

    with st.form(key=f"round_form_{idx if idx is not None else 'new'}"):
        name = st.text_input("Round Name *", value=round_data.get("name", "")
                             if round_data else "", key=f"round_name_{idx}")
        round_date = st.date_input(
            "Round Date *",
            value=datetime.strptime(round_data.get("round_date", "2024-01-01"), "%Y-%m-%d").date(
            ) if round_data and round_data.get("round_date") else datetime.now().date(),
            key=f"round_date_{idx}"
        )
        calculation_type = st.selectbox(
            "Calculation Type *",
            list(CALCULATION_TYPES.keys()),
            format_func=lambda x: CALCULATION_TYPES[x],
            index=list(CALCULATION_TYPES.keys()).index(round_data.get("calculation_type", "fixed_shares")
                       ) if round_data and round_data.get("calculation_type") in CALCULATION_TYPES else 0,
            key=f"round_calc_type_{idx}"
        )

        valuation_basis = None
        valuation = None
        price_per_share = None
        conversion_round_ref = None

        if calculation_type in ["valuation_based", "convertible", "safe"]:
            valuation_basis = st.selectbox(
                "Valuation Basis *",
                VALUATION_BASIS_OPTIONS,
                index=VALUATION_BASIS_OPTIONS.index(round_data.get("valuation_basis", "pre_money")) if round_data and round_data.get(
                    "valuation_basis") in VALUATION_BASIS_OPTIONS else 0,
                key=f"round_valuation_basis_{idx}"
            )
            valuation = st.number_input(
                "Valuation",
                min_value=0.0,
                value=float(round_data.get("valuation", 0)) if round_data and round_data.get(
                    "valuation") else 0.0,
                key=f"round_valuation_{idx}"
            )

        if calculation_type in ["convertible", "safe"]:
            conversion_round_ref = st.text_input(
                "Conversion Round Reference (optional)",
                value=round_data.get("conversion_round_ref",
                                     "") if round_data else "",
                key=f"round_conversion_ref_{idx}"
            )

        if calculation_type == "valuation_based":
            price_per_share = st.number_input(
                "Price Per Share (optional)",
                min_value=0.0,
                value=float(round_data.get("price_per_share", 0)) if round_data and round_data.get(
                    "price_per_share") else 0.0,
                key=f"round_price_per_share_{idx}"
            )

        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Save", use_container_width=True):
                if not name:
                    st.error("Round name is required")
                else:
                    round_obj = {
                        "name": name,
                        "round_date": round_date.strftime("%Y-%m-%d"),
                        "calculation_type": calculation_type,
                        "instruments": round_data.get("instruments", []) if round_data else []
                    }

                    if valuation_basis:
                        round_obj["valuation_basis"] = valuation_basis
                    if valuation and valuation > 0:
                        round_obj["valuation"] = valuation
                    if price_per_share and price_per_share > 0:
                        round_obj["price_per_share"] = price_per_share
                    if conversion_round_ref:
                        round_obj["conversion_round_ref"] = conversion_round_ref

                    if is_edit and idx is not None:
                        st.session_state.rounds[idx] = round_obj
                        st.session_state.editing_round_idx = None
                    else:
                        st.session_state.rounds.append(round_obj)
                    st.rerun()
        with col2:
            if is_edit and st.form_submit_button("Cancel", use_container_width=True):
                st.session_state.editing_round_idx = None
                st.rerun()


def generate_json() -> Dict[str, Any]:
    """Generate the final JSON structure."""
    return {
        "schema_version": "2.0",
        "holders": st.session_state.holders,
        "rounds": st.session_state.rounds
    }


def main():
    st.set_page_config(page_title="Cap Table Generator Wizard",
                       page_icon="📊", layout="wide")

    st.title("📊 Cap Table Generator Wizard")
    st.markdown("Build your cap table JSON step by step")

    # Step navigation
    steps = ["1. Define Holders", "2. Define Rounds", "3. Review & Copy JSON"]

    # Sidebar for step navigation
    with st.sidebar:
        st.header("Steps")
        for i, step in enumerate(steps, 1):
            if st.button(step, key=f"step_btn_{i}", use_container_width=True,
                       type="primary" if st.session_state.current_step == i else "secondary"):
                st.session_state.current_step = i
                st.rerun()

        st.divider()
        if st.button("🔄 Reset All Data", use_container_width=True):
            st.session_state.holders = []
            st.session_state.rounds = []
            st.session_state.current_step = 1
            st.session_state.editing_holder_idx = None
            st.session_state.editing_round_idx = None
            st.session_state.adding_instrument = {}
            st.session_state.editing_instrument = {}
            st.session_state.adding_pro_rata = {}
            st.session_state.editing_pro_rata = {}
            st.rerun()

    # Step 1: Define Holders
    if st.session_state.current_step == 1:
        st.header("Step 1: Define Holders")
        st.markdown(
            "Add all holders (founders, investors, employees, etc.) that will appear in your cap table.")

        # Add new holder button
        if st.session_state.editing_holder_idx is None:
            if st.button("➕ Add New Holder", type="primary"):
                st.session_state.editing_holder_idx = "new"
                st.rerun()

        # Holder form
        if st.session_state.editing_holder_idx is not None:
            holder = None
            if isinstance(st.session_state.editing_holder_idx, int):
                holder = st.session_state.holders[st.session_state.editing_holder_idx]
            render_holder_form(holder, st.session_state.editing_holder_idx)

        # List of holders
        if st.session_state.holders:
            st.subheader("Current Holders")
            for idx, holder in enumerate(st.session_state.holders):
                with st.expander(f"📌 {holder['name']} {holder.get('group', '') and f"({holder['group']})" or ''}", expanded=False):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.write(f"**Name:** {holder['name']}")
                        if holder.get('group'):
                            st.write(f"**Group:** {holder['group']}")
                        if holder.get('description'):
                            st.write(f"**Description:** {holder['description']}")
                    with col2:
                        if st.button("✏️ Edit", key=f"edit_holder_{idx}", use_container_width=True):
                            st.session_state.editing_holder_idx = idx
                            st.rerun()
                    with col3:
                        if st.button("🗑️ Delete", key=f"delete_holder_{idx}", use_container_width=True):
                            st.session_state.holders.pop(idx)
                            st.rerun()
        else:
            st.info("No holders added yet. Click 'Add New Holder' to get started.")
    
    # Step 2: Define Rounds
    elif st.session_state.current_step == 2:
        st.header("Step 2: Define Rounds")
        st.markdown("Add financing rounds with instruments and pro rata allocations.")
        
        if not st.session_state.holders:
            st.warning("⚠️ Please add holders in Step 1 before defining rounds.")
        else:
            # Add new round button
            if st.session_state.editing_round_idx is None:
                if st.button("➕ Add New Round", type="primary"):
                    st.session_state.editing_round_idx = "new"
                    st.rerun()
            
            # Round form
            if st.session_state.editing_round_idx is not None:
                round_data = None
                if isinstance(st.session_state.editing_round_idx, int):
                    round_data = st.session_state.rounds[st.session_state.editing_round_idx]
                render_round_form(round_data, st.session_state.editing_round_idx)
            
            # List of rounds
            if st.session_state.rounds:
                st.subheader("Current Rounds")
                for round_idx, round_data in enumerate(st.session_state.rounds):
                    with st.expander(f"📅 {round_data['name']} ({round_data.get('round_date', 'N/A')})", expanded=False):
                        # Round info
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**Calculation Type:** {CALCULATION_TYPES.get(round_data.get('calculation_type', ''), round_data.get('calculation_type', ''))}")
                            if round_data.get('valuation_basis'):
                                st.write(f"**Valuation Basis:** {round_data['valuation_basis']}")
                            if round_data.get('valuation'):
                                st.write(f"**Valuation:** ${round_data['valuation']:,.0f}")
                        with col2:
                            if st.button("✏️ Edit Round", key=f"edit_round_{round_idx}", use_container_width=True):
                                st.session_state.editing_round_idx = round_idx
                                st.rerun()
                            if st.button("🗑️ Delete Round", key=f"delete_round_{round_idx}", use_container_width=True):
                                st.session_state.rounds.pop(round_idx)
                                st.rerun()
                        
                        # Instruments section
                        st.markdown("**Instruments:**")
                        instruments = round_data.get("instruments", [])
                        
                        # Check if instrument is pro rata
                        def is_pro_rata(instr):
                            return "pro_rata_type" in instr
                        
                        regular_instruments = [i for i in instruments if not is_pro_rata(i)]
                        pro_rata_allocations = [i for i in instruments if is_pro_rata(i)]
                        
                        if regular_instruments:
                            st.markdown("*Regular Instruments:*")
                            for inst_idx, inst in enumerate(regular_instruments):
                                inst_global_idx = instruments.index(inst)
                                col1, col2, col3 = st.columns([3, 1, 1])
                                with col1:
                                    inst_type = round_data.get("calculation_type", "")
                                    if inst_type == "fixed_shares":
                                        st.write(f"- {inst.get('holder_name')} → {inst.get('class_name')}: {inst.get('initial_quantity', 0):,} shares")
                                    elif inst_type == "target_percentage":
                                        st.write(f"- {inst.get('holder_name')} → {inst.get('class_name')}: {inst.get('target_percentage', 0)*100:.1f}%")
                                    elif inst_type in ["valuation_based", "convertible", "safe"]:
                                        st.write(f"- {inst.get('holder_name')} → {inst.get('class_name')}: ${inst.get('investment_amount', 0):,.0f}")
                                with col2:
                                    if st.button("✏️ Edit", key=f"edit_inst_{round_idx}_{inst_global_idx}", use_container_width=True):
                                        # Store editing state
                                        if "editing_instrument" not in st.session_state:
                                            st.session_state.editing_instrument = {}
                                        st.session_state.editing_instrument[f"{round_idx}_{inst_global_idx}"] = True
                                        st.rerun()
                                with col3:
                                    if st.button("🗑️ Delete", key=f"delete_inst_{round_idx}_{inst_global_idx}", use_container_width=True):
                                        st.session_state.rounds[round_idx]["instruments"].pop(inst_global_idx)
                                        st.rerun()
                        
                        if pro_rata_allocations:
                            st.markdown("*Pro Rata Allocations:*")
                            for pr_idx, pr in enumerate(pro_rata_allocations):
                                pr_global_idx = instruments.index(pr)
                                col1, col2, col3 = st.columns([3, 1, 1])
                                with col1:
                                    pr_type_str = pr.get('pro_rata_type', 'standard')
                                    if pr_type_str == "super":
                                        st.write(f"- {pr.get('holder_name')} → {pr.get('class_name')}: Super Pro Rata ({pr.get('pro_rata_percentage', 0)*100:.1f}%)")
                                    else:
                                        st.write(f"- {pr.get('holder_name')} → {pr.get('class_name')}: Standard Pro Rata")
                                with col2:
                                    if st.button("✏️ Edit", key=f"edit_pr_{round_idx}_{pr_global_idx}", use_container_width=True):
                                        if "editing_pro_rata" not in st.session_state:
                                            st.session_state.editing_pro_rata = {}
                                        st.session_state.editing_pro_rata[f"{round_idx}_{pr_global_idx}"] = True
                                        st.rerun()
                                with col3:
                                    if st.button("🗑️ Delete", key=f"delete_pr_{round_idx}_{pr_global_idx}", use_container_width=True):
                                        st.session_state.rounds[round_idx]["instruments"].pop(pr_global_idx)
                                        st.rerun()
                        
                        # Add instrument buttons
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("➕ Add Instrument", key=f"add_inst_{round_idx}", use_container_width=True):
                                if "adding_instrument" not in st.session_state:
                                    st.session_state.adding_instrument = {}
                                st.session_state.adding_instrument[f"{round_idx}"] = True
                                st.rerun()
                        with col2:
                            if st.button("➕ Add Pro Rata", key=f"add_pr_{round_idx}", use_container_width=True):
                                if "adding_pro_rata" not in st.session_state:
                                    st.session_state.adding_pro_rata = {}
                                st.session_state.adding_pro_rata[f"{round_idx}"] = True
                                st.rerun()
                        
                        # Handle adding/editing instruments
                        if "adding_instrument" in st.session_state and st.session_state.adding_instrument.get(f"{round_idx}"):
                            with st.container():
                                st.markdown("---")
                                st.markdown("**Add New Instrument**")
                                render_instrument_form(round_idx)
                                if st.button("Cancel", key=f"cancel_add_inst_{round_idx}"):
                                    del st.session_state.adding_instrument[f"{round_idx}"]
                                    st.rerun()
                        
                        if "editing_instrument" in st.session_state:
                            for key in list(st.session_state.editing_instrument.keys()):
                                if key.startswith(f"{round_idx}_"):
                                    inst_idx = int(key.split("_")[-1])
                                    with st.container():
                                        st.markdown("---")
                                        st.markdown("**Edit Instrument**")
                                        render_instrument_form(round_idx, inst_idx, instruments[inst_idx])
                                        if st.button("Cancel", key=f"cancel_edit_inst_{round_idx}_{inst_idx}"):
                                            del st.session_state.editing_instrument[key]
                                            st.rerun()
                        
                        # Handle adding/editing pro rata
                        if "adding_pro_rata" in st.session_state and st.session_state.adding_pro_rata.get(f"{round_idx}"):
                            with st.container():
                                st.markdown("---")
                                st.markdown("**Add New Pro Rata Allocation**")
                                render_pro_rata_form(round_idx)
                                if st.button("Cancel", key=f"cancel_add_pr_{round_idx}"):
                                    del st.session_state.adding_pro_rata[f"{round_idx}"]
                                    st.rerun()
                        
                        if "editing_pro_rata" in st.session_state:
                            for key in list(st.session_state.editing_pro_rata.keys()):
                                if key.startswith(f"{round_idx}_"):
                                    pr_idx = int(key.split("_")[-1])
                                    with st.container():
                                        st.markdown("---")
                                        st.markdown("**Edit Pro Rata Allocation**")
                                        render_pro_rata_form(round_idx, pr_idx, instruments[pr_idx])
                                        if st.button("Cancel", key=f"cancel_edit_pr_{round_idx}_{pr_idx}"):
                                            del st.session_state.editing_pro_rata[key]
                                            st.rerun()
            else:
                st.info("No rounds added yet. Click 'Add New Round' to get started.")
    
    # Step 3: Review & Copy JSON
    elif st.session_state.current_step == 3:
        st.header("Step 3: Review & Copy JSON")
        st.markdown("Review your cap table configuration and copy the generated JSON.")
        
        json_data = generate_json()
        json_str = json.dumps(json_data, indent=2)
        
        # Display JSON
        st.subheader("Generated JSON")
        st.code(json_str, language="json")
        
        # Copy button - using text area for easy selection
        st.markdown("**Copy JSON:** Select all text in the code block above (Ctrl+A / Cmd+A) and copy (Ctrl+C / Cmd+C)")
        
        # Download button
        st.download_button(
            label="💾 Download JSON File",
            data=json_str,
            file_name="cap_table.json",
            mime="application/json",
            use_container_width=True
        )
        
        # Summary
        st.subheader("Summary")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Holders", len(st.session_state.holders))
        with col2:
            st.metric("Rounds", len(st.session_state.rounds))


if __name__ == "__main__":
    main()
