"""
Streamlit wizard for filling in the Cap Table JSON schema.
Provides a step-by-step form interface to build the complete JSON structure.
"""

import streamlit as st
import json
from datetime import datetime
from typing import Dict, Any, List
import os
import sys

# Add parent directory to path to import captable modules
_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from captable.schema import CAP_TABLE_SCHEMA


def initialize_session_state():
    """Initialize session state variables."""
    if "cap_table_data" not in st.session_state:
        st.session_state.cap_table_data = {
            "schema_version": "2.0",
            "holders": [],
            "rounds": []
        }
    if "current_step" not in st.session_state:
        st.session_state.current_step = "holders"
    if "editing_holder_idx" not in st.session_state:
        st.session_state.editing_holder_idx = None
    if "editing_round_idx" not in st.session_state:
        st.session_state.editing_round_idx = None
    if "editing_instrument_idx" not in st.session_state:
        st.session_state.editing_instrument_idx = None
    if "adding_instrument_to_round" not in st.session_state:
        st.session_state.adding_instrument_to_round = None


def render_holder_form(holder: Dict[str, Any] = None, index: int = None):
    """Render form for adding/editing a holder."""
    is_editing = holder is not None and index is not None
    
    st.subheader(f"{'Edit' if is_editing else 'Add'} Holder")
    
    name = st.text_input(
        "Name *",
        value=holder.get("name", "") if holder else "",
        help="Unique holder name (used as reference in instruments)"
    )
    
    description = st.text_input(
        "Description",
        value=holder.get("description", "") if holder else "",
        help="Optional description shown next to the holder name"
    )
    
    group = st.text_input(
        "Group",
        value=holder.get("group", "") if holder else "",
        help="Optional group name (e.g., 'Founders', 'Investors', 'Employees')"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(f"{'Update' if is_editing else 'Add'} Holder", type="primary"):
            if name.strip():
                holder_data = {"name": name.strip()}
                if description.strip():
                    holder_data["description"] = description.strip()
                if group.strip():
                    holder_data["group"] = group.strip()
                
                if is_editing:
                    st.session_state.cap_table_data["holders"][index] = holder_data
                    st.session_state.editing_holder_idx = None
                    st.rerun()
                else:
                    st.session_state.cap_table_data["holders"].append(holder_data)
                    st.rerun()
            else:
                st.error("Name is required")
    
    with col2:
        if is_editing and st.button("Cancel"):
            st.session_state.editing_holder_idx = None
            st.rerun()


def render_holders_step():
    """Render the holders management step."""
    st.header("Step 1: Define Holders")
    st.markdown("Add all holders (founders, investors, employees, etc.) that will appear in your cap table.")
    
    # Add new holder form
    render_holder_form()
    
    st.divider()
    
    # List existing holders
    if st.session_state.cap_table_data["holders"]:
        st.subheader("Existing Holders")
        for idx, holder in enumerate(st.session_state.cap_table_data["holders"]):
            with st.expander(f"Holder: {holder.get('name', 'Unnamed')}"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Name:** {holder.get('name', 'N/A')}")
                    if holder.get('description'):
                        st.write(f"**Description:** {holder.get('description')}")
                    if holder.get('group'):
                        st.write(f"**Group:** {holder.get('group')}")
                with col2:
                    if st.button("Edit", key=f"edit_holder_{idx}"):
                        st.session_state.editing_holder_idx = idx
                        st.rerun()
                    if st.button("Delete", key=f"delete_holder_{idx}"):
                        st.session_state.cap_table_data["holders"].pop(idx)
                        st.rerun()
    
    # Navigation
    st.divider()
    col1, col2 = st.columns([1, 1])
    with col2:
        if st.button("Next: Add Rounds →", type="primary", disabled=len(st.session_state.cap_table_data["holders"]) == 0):
            st.session_state.current_step = "rounds"
            st.rerun()


def render_instrument_form(round_data: Dict[str, Any], instrument: Dict[str, Any] = None, index: int = None):
    """Render form for adding/editing an instrument."""
    is_editing = instrument is not None and index is not None
    calculation_type = round_data.get("calculation_type")
    
    st.subheader(f"{'Edit' if is_editing else 'Add'} Instrument")
    
    # Holder selection
    holder_names = [h["name"] for h in st.session_state.cap_table_data["holders"]]
    if not holder_names:
        st.warning("Please add holders first before adding instruments.")
        return
    
    holder_name = st.selectbox(
        "Holder *",
        options=holder_names,
        index=holder_names.index(instrument.get("holder_name", holder_names[0])) if instrument and instrument.get("holder_name") in holder_names else 0
    )
    
    class_name = st.text_input(
        "Class Name *",
        value=instrument.get("class_name", "") if instrument else "",
        help="Security class name (e.g., 'Common Stock', 'Preferred Stock')"
    )
    
    # Pro rata settings
    pro_rata_type = st.selectbox(
        "Pro Rata Type",
        options=["none", "standard", "super"],
        index=["none", "standard", "super"].index(instrument.get("pro_rata_type", "none")) if instrument else 0
    )
    
    if pro_rata_type == "super":
        pro_rata_percentage = st.number_input(
            "Pro Rata Percentage",
            min_value=0.0,
            max_value=1.0,
            value=float(instrument.get("pro_rata_percentage", 0.0)) if instrument else 0.0,
            step=0.01,
            format="%.2f",
            help="Target ownership percentage for super pro rata rights (as decimal, e.g., 0.20 for 20%)"
        )
    else:
        pro_rata_percentage = None
    
    # Fields based on calculation type
    if calculation_type == "fixed_shares":
        initial_quantity = st.number_input(
            "Initial Quantity *",
            min_value=0.0,
            value=float(instrument.get("initial_quantity", 0.0)) if instrument else 0.0,
            step=1000.0,
            format="%.0f",
            help="Number of shares"
        )
    elif calculation_type == "target_percentage":
        target_percentage = st.number_input(
            "Target Percentage *",
            min_value=0.0,
            max_value=1.0,
            value=float(instrument.get("target_percentage", 0.0)) if instrument else 0.0,
            step=0.01,
            format="%.2f",
            help="Target ownership percentage (as decimal, e.g., 0.20 for 20%)"
        )
    elif calculation_type in ["valuation_based", "convertible", "safe"]:
        investment_amount = st.number_input(
            "Investment Amount",
            min_value=0.0,
            value=float(instrument.get("investment_amount", 0.0)) if instrument else 0.0,
            step=1000.0,
            format="%.0f",
            help="Investment amount"
        )
        
        # Date fields
        if calculation_type == "convertible":
            col1, col2 = st.columns(2)
            with col1:
                # Use payment_date if available, fallback to interest_start_date for backward compatibility
                payment_date_value = instrument.get("payment_date") or instrument.get("interest_start_date", "2024-01-01") if instrument else "2024-01-01"
                payment_date = st.date_input(
                    "Payment Date",
                    value=datetime.strptime(payment_date_value, "%Y-%m-%d").date() if isinstance(payment_date_value, str) else (payment_date_value if isinstance(payment_date_value, datetime.date) else datetime.now().date())
                )
            with col2:
                # Use expected_conversion_date if available, fallback to interest_end_date for backward compatibility
                conversion_date_value = instrument.get("expected_conversion_date") or instrument.get("interest_end_date", "2024-12-31") if instrument else "2024-12-31"
                expected_conversion_date = st.date_input(
                    "Expected Conversion Date",
                    value=datetime.strptime(conversion_date_value, "%Y-%m-%d").date() if isinstance(conversion_date_value, str) else (conversion_date_value if isinstance(conversion_date_value, datetime.date) else datetime.now().date())
                )
        elif calculation_type == "safe":
            # SAFE only needs expected conversion date, no payment date
            expected_conversion_date = st.date_input(
                "Expected Conversion Date",
                value=datetime.strptime(instrument.get("expected_conversion_date", "2024-12-31"), "%Y-%m-%d").date() if instrument and instrument.get("expected_conversion_date") else datetime.now().date()
            )
            payment_date = None
        else:
            payment_date = None
            expected_conversion_date = None
        
        # Interest fields (only for convertible, not for safe)
        if calculation_type == "convertible":
            st.markdown("**Interest Settings**")
            interest_type = st.selectbox(
                "Interest Type",
                options=["simple", "compound_yearly", "compound_monthly", "compound_daily", "no_interest"],
                index=["simple", "compound_yearly", "compound_monthly", "compound_daily", "no_interest"].index(
                    instrument.get("interest_type", "simple")
                ) if instrument else 0
            )
            
            if interest_type != "no_interest":
                interest_rate = st.number_input(
                    "Interest Rate",
                    min_value=0.0,
                    max_value=1.0,
                    value=float(instrument.get("interest_rate", 0.0)) if instrument else 0.0,
                    step=0.01,
                    format="%.2f",
                    help="Annual interest rate (as decimal, e.g., 0.08 for 8%)"
                )
            else:
                interest_rate = None
        else:
            # SAFE and valuation_based don't have interest
            interest_type = None
            interest_rate = None
        
        # Discount rate for convertible and safe
        if calculation_type in ["convertible", "safe"]:
            discount_rate = st.number_input(
                "Discount Rate",
                min_value=0.0,
                max_value=1.0,
                value=float(instrument.get("discount_rate", 0.0)) if instrument else 0.0,
                step=0.01,
                format="%.2f",
                help="Discount rate (as decimal, e.g., 0.20 for 20%)"
            )
        else:
            discount_rate = None
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(f"{'Update' if is_editing else 'Add'} Instrument", type="primary"):
            if not class_name.strip():
                st.error("Class name is required")
            else:
                instrument_data = {
                    "holder_name": holder_name,
                    "class_name": class_name.strip(),
                    "pro_rata_type": pro_rata_type
                }
                
                if pro_rata_type == "super" and pro_rata_percentage is not None:
                    instrument_data["pro_rata_percentage"] = pro_rata_percentage
                
                if calculation_type == "fixed_shares":
                    instrument_data["initial_quantity"] = initial_quantity
                elif calculation_type == "target_percentage":
                    instrument_data["target_percentage"] = target_percentage
                elif calculation_type in ["valuation_based", "convertible", "safe"]:
                    if investment_amount > 0:
                        instrument_data["investment_amount"] = investment_amount
                    if calculation_type == "convertible":
                        if payment_date:
                            instrument_data["payment_date"] = payment_date.strftime("%Y-%m-%d")
                        if expected_conversion_date:
                            instrument_data["expected_conversion_date"] = expected_conversion_date.strftime("%Y-%m-%d")
                    elif calculation_type == "safe":
                        if expected_conversion_date:
                            instrument_data["expected_conversion_date"] = expected_conversion_date.strftime("%Y-%m-%d")
                    if calculation_type == "convertible" and interest_type != "no_interest":
                        instrument_data["interest_type"] = interest_type
                        if interest_rate is not None:
                            instrument_data["interest_rate"] = interest_rate
                    if calculation_type in ["convertible", "safe"] and discount_rate is not None:
                        instrument_data["discount_rate"] = discount_rate
                
                if is_editing:
                    round_data["instruments"][index] = instrument_data
                    st.session_state.editing_instrument_idx = None
                    st.session_state.adding_instrument_to_round = None
                    st.rerun()
                else:
                    if "instruments" not in round_data:
                        round_data["instruments"] = []
                    round_data["instruments"].append(instrument_data)
                    st.session_state.adding_instrument_to_round = None
                    st.rerun()
    
    with col2:
        if is_editing and st.button("Cancel"):
            st.session_state.editing_instrument_idx = None
            st.session_state.adding_instrument_to_round = None
            st.rerun()
        elif not is_editing and st.button("Cancel"):
            st.session_state.adding_instrument_to_round = None
            st.rerun()


def render_round_form(round_data: Dict[str, Any] = None, index: int = None):
    """Render form for adding/editing a round."""
    is_editing = round_data is not None and index is not None
    
    st.subheader(f"{'Edit' if is_editing else 'Add'} Round")
    
    name = st.text_input(
        "Round Name *",
        value=round_data.get("name", "") if round_data else "",
        help="Name of the financing round (e.g., 'Series A', 'Incorporation')"
    )
    
    round_date = st.date_input(
        "Round Date *",
        value=datetime.strptime(round_data.get("round_date", "2024-01-01"), "%Y-%m-%d").date() if round_data and round_data.get("round_date") else datetime.now().date()
    )
    
    calculation_type = st.selectbox(
        "Calculation Type *",
        options=["fixed_shares", "target_percentage", "convertible", "safe", "valuation_based"],
        index=["fixed_shares", "target_percentage", "convertible", "safe", "valuation_based"].index(
            round_data.get("calculation_type", "fixed_shares")
        ) if round_data and round_data.get("calculation_type") in ["fixed_shares", "target_percentage", "convertible", "safe", "valuation_based"] else 0,
        help="Method for calculating shares in this round"
    )
    
    # Fields based on calculation type
    if calculation_type == "valuation_based":
        valuation_basis = st.selectbox(
            "Valuation Basis *",
            options=["pre_money", "post_money"],
            index=["pre_money", "post_money"].index(round_data.get("valuation_basis", "pre_money")) if round_data else 0
        )
    else:
        valuation_basis = None
    
    if calculation_type in ["convertible", "safe"]:
        valuation_cap_basis = st.selectbox(
            "Valuation Cap Basis *",
            options=["pre_money", "post_money", "fixed"],
            index=["pre_money", "post_money", "fixed"].index(round_data.get("valuation_cap_basis", "pre_money")) if round_data and round_data.get("valuation_cap_basis") in ["pre_money", "post_money", "fixed"] else 0
        )
    else:
        valuation_cap_basis = None
    
    # Optional valuation fields
    st.markdown("**Valuation Fields (Optional)**")
    col1, col2, col3 = st.columns(3)
    with col1:
        pre_money_valuation = st.number_input(
            "Pre-Money Valuation",
            min_value=0.0,
            value=float(round_data.get("pre_money_valuation", 0.0)) if round_data else 0.0,
            step=10000.0,
            format="%.0f"
        )
    with col2:
        post_money_valuation = st.number_input(
            "Post-Money Valuation",
            min_value=0.0,
            value=float(round_data.get("post_money_valuation", 0.0)) if round_data else 0.0,
            step=10000.0,
            format="%.0f"
        )
    with col3:
        price_per_share = st.number_input(
            "Price Per Share",
            min_value=0.0,
            value=float(round_data.get("price_per_share", 0.0)) if round_data else 0.0,
            step=0.01,
            format="%.2f"
        )
    
    # Save round button
    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"{'Update' if is_editing else 'Add'} Round", type="primary"):
            if not name.strip():
                st.error("Round name is required")
            elif calculation_type == "valuation_based" and not valuation_basis:
                st.error("Valuation basis is required for valuation_based rounds")
            elif calculation_type in ["convertible", "safe"] and not valuation_cap_basis:
                st.error(f"Valuation cap basis is required for {calculation_type} rounds")
            else:
                new_round = {
                    "name": name.strip(),
                    "round_date": round_date.strftime("%Y-%m-%d"),
                    "calculation_type": calculation_type
                }
                
                if valuation_basis:
                    new_round["valuation_basis"] = valuation_basis
                if valuation_cap_basis:
                    new_round["valuation_cap_basis"] = valuation_cap_basis
                if pre_money_valuation > 0:
                    new_round["pre_money_valuation"] = pre_money_valuation
                if post_money_valuation > 0:
                    new_round["post_money_valuation"] = post_money_valuation
                if price_per_share > 0:
                    new_round["price_per_share"] = price_per_share
                
                # Preserve instruments if editing
                if is_editing and "instruments" in round_data:
                    new_round["instruments"] = round_data["instruments"]
                else:
                    new_round["instruments"] = []
                
                if is_editing:
                    st.session_state.cap_table_data["rounds"][index] = new_round
                    st.session_state.editing_round_idx = None
                    st.session_state.adding_instrument_to_round = None
                    st.rerun()
                else:
                    st.session_state.cap_table_data["rounds"].append(new_round)
                    st.rerun()
    
    with col2:
        if is_editing and st.button("Cancel"):
            st.session_state.editing_round_idx = None
            st.session_state.adding_instrument_to_round = None
            st.rerun()


def render_rounds_step():
    """Render the rounds management step."""
    st.header("Step 2: Define Rounds")
    st.markdown("Add financing rounds and their instruments.")
    
    # Add new round form (only show if not editing a round and not adding instrument)
    if (st.session_state.editing_round_idx is None and 
        st.session_state.adding_instrument_to_round is None):
        render_round_form()
    
    st.divider()
    
    # List existing rounds
    if st.session_state.cap_table_data["rounds"]:
        st.subheader("Existing Rounds")
        for round_idx, round_data in enumerate(st.session_state.cap_table_data["rounds"]):
            with st.expander(f"Round: {round_data.get('name', 'Unnamed')} ({round_data.get('calculation_type', 'N/A')})"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Name:** {round_data.get('name', 'N/A')}")
                    st.write(f"**Date:** {round_data.get('round_date', 'N/A')}")
                    st.write(f"**Type:** {round_data.get('calculation_type', 'N/A')}")
                    if round_data.get('valuation_basis'):
                        st.write(f"**Valuation Basis:** {round_data.get('valuation_basis')}")
                    if round_data.get('valuation_cap_basis'):
                        st.write(f"**Valuation Cap Basis:** {round_data.get('valuation_cap_basis')}")
                    instruments = round_data.get("instruments", [])
                    st.write(f"**Instruments:** {len(instruments)}")
                with col2:
                    if st.button("Edit", key=f"edit_round_{round_idx}"):
                        st.session_state.editing_round_idx = round_idx
                        st.session_state.adding_instrument_to_round = None
                        st.session_state.editing_instrument_idx = None
                        st.rerun()
                    if st.button("Delete", key=f"delete_round_{round_idx}"):
                        st.session_state.cap_table_data["rounds"].pop(round_idx)
                        st.rerun()
                
                # Show round edit form if editing this round
                if st.session_state.editing_round_idx == round_idx and st.session_state.adding_instrument_to_round != round_idx:
                    st.divider()
                    render_round_form(round_data, round_idx)
                    st.divider()
                
                # Instruments for this round
                if instruments:
                    st.markdown("**Instruments:**")
                    for inst_idx, instrument in enumerate(instruments):
                        with st.expander(f"Instrument {inst_idx + 1}: {instrument.get('holder_name', 'N/A')} - {instrument.get('class_name', 'N/A')}"):
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(f"**Holder:** {instrument.get('holder_name', 'N/A')}")
                                st.write(f"**Class:** {instrument.get('class_name', 'N/A')}")
                                st.write(f"**Pro Rata:** {instrument.get('pro_rata_type', 'none')}")
                                if instrument.get('initial_quantity'):
                                    st.write(f"**Initial Quantity:** {instrument.get('initial_quantity'):,.0f}")
                                if instrument.get('target_percentage'):
                                    st.write(f"**Target Percentage:** {instrument.get('target_percentage'):.2%}")
                                if instrument.get('investment_amount'):
                                    st.write(f"**Investment Amount:** ${instrument.get('investment_amount'):,.0f}")
                            with col2:
                                if st.button("Edit", key=f"edit_instrument_{round_idx}_{inst_idx}"):
                                    st.session_state.editing_round_idx = None
                                    st.session_state.adding_instrument_to_round = round_idx
                                    st.session_state.editing_instrument_idx = inst_idx
                                    st.rerun()
                                if st.button("Delete", key=f"delete_instrument_{round_idx}_{inst_idx}"):
                                    st.session_state.cap_table_data["rounds"][round_idx]["instruments"].pop(inst_idx)
                                    st.rerun()
                
                # Show instrument form if adding/editing instrument for this round
                if st.session_state.adding_instrument_to_round == round_idx:
                    st.divider()
                    if st.session_state.editing_instrument_idx is not None:
                        # Editing existing instrument
                        render_instrument_form(
                            round_data,
                            round_data["instruments"][st.session_state.editing_instrument_idx],
                            st.session_state.editing_instrument_idx
                        )
                    else:
                        # Adding new instrument
                        render_instrument_form(round_data)
                elif st.session_state.editing_round_idx != round_idx:
                    # Show add instrument button if not editing round
                    if st.button("Add Instrument", key=f"add_instrument_{round_idx}"):
                        st.session_state.editing_round_idx = None
                        st.session_state.adding_instrument_to_round = round_idx
                        st.session_state.editing_instrument_idx = None
                        st.rerun()
    
    # Navigation
    st.divider()
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("← Back to Holders"):
            st.session_state.current_step = "holders"
            st.rerun()
    with col2:
        if st.button("Review & Export →", type="primary"):
            st.session_state.current_step = "review"
            st.rerun()


def render_review_step():
    """Render the review and export step."""
    st.header("Step 3: Review & Export")
    st.markdown("Review your cap table data and export as JSON.")
    
    # Display summary
    st.subheader("Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Holders", len(st.session_state.cap_table_data["holders"]))
    with col2:
        st.metric("Rounds", len(st.session_state.cap_table_data["rounds"]))
    with col3:
        total_instruments = sum(len(r.get("instruments", [])) for r in st.session_state.cap_table_data["rounds"])
        st.metric("Instruments", total_instruments)
    
    # Display JSON
    st.subheader("Generated JSON")
    json_str = json.dumps(st.session_state.cap_table_data, indent=2)
    st.code(json_str, language="json")
    
    # Download button
    st.download_button(
        label="Download JSON",
        data=json_str,
        file_name="cap_table.json",
        mime="application/json"
    )
    
    # Navigation
    st.divider()
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("← Back to Rounds"):
            st.session_state.current_step = "rounds"
            st.rerun()
    with col2:
        if st.button("Start Over", type="secondary"):
            st.session_state.cap_table_data = {
                "schema_version": "2.0",
                "holders": [],
                "rounds": []
            }
            st.session_state.current_step = "holders"
            st.rerun()


def main():
    """Main Streamlit app."""
    st.set_page_config(
        page_title="Cap Table Generator Wizard",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Cap Table Generator Wizard")
    st.markdown("Fill in the form below to generate your cap table JSON schema.")
    
    initialize_session_state()
    
    # Sidebar navigation
    with st.sidebar:
        st.header("Navigation")
        steps = ["holders", "rounds", "review"]
        step_labels = ["1. Holders", "2. Rounds", "3. Review"]
        current_idx = steps.index(st.session_state.current_step) if st.session_state.current_step in steps else 0
        
        for idx, (step, label) in enumerate(zip(steps, step_labels)):
            if idx == current_idx:
                st.markdown(f"**{label}** ✓")
            elif idx < current_idx:
                st.markdown(f"~~{label}~~ ✓")
            else:
                st.markdown(f"{label}")
        
        st.divider()
        
        # Load from file
        st.subheader("Load from File")
        uploaded_file = st.file_uploader("Upload JSON", type=["json"])
        if uploaded_file is not None:
            try:
                data = json.load(uploaded_file)
                if "schema_version" in data and "holders" in data and "rounds" in data:
                    st.session_state.cap_table_data = data
                    st.success("File loaded successfully!")
                    st.rerun()
                else:
                    st.error("Invalid cap table JSON structure")
            except json.JSONDecodeError:
                st.error("Invalid JSON file")
    
    # Render current step
    if st.session_state.current_step == "holders":
        render_holders_step()
    elif st.session_state.current_step == "rounds":
        render_rounds_step()
    elif st.session_state.current_step == "review":
        render_review_step()


if __name__ == "__main__":
    main()

