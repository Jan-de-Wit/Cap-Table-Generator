"""
Cap Table Service - State management and metrics calculation.
Maintains the current cap table state and computes ownership metrics.
"""

from typing import Dict, Any, List, Optional
import copy


class CapTableService:
    """Manages cap table state and computes metrics."""
    
    def __init__(self):
        """Initialize with empty cap table."""
        self.cap_table: Optional[Dict[str, Any]] = None
        self.reset()
    
    def reset(self):
        """Reset to minimal valid cap table."""
        self.cap_table = {
            "schema_version": "1.0",
            "company": {
                "name": "Untitled Company"
            },
            "holders": [],
            "classes": [],
            "instruments": []
        }
    
    def get_cap_table(self) -> Dict[str, Any]:
        """Get current cap table state."""
        return copy.deepcopy(self.cap_table)
    
    def set_cap_table(self, cap_table: Dict[str, Any]):
        """Set cap table state."""
        self.cap_table = copy.deepcopy(cap_table)
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """
        Calculate ownership metrics from current cap table.
        
        Returns:
            Dictionary with totals, ownership breakdown, and pool stats
        """
        if not self.cap_table:
            return self._empty_metrics()
        
        instruments = self.cap_table.get("instruments", [])
        holders = self.cap_table.get("holders", [])
        classes = self.cap_table.get("classes", [])
        
        # Build lookup maps
        holders_map = {h["name"]: h for h in holders}
        classes_map = {c["name"]: c for c in classes}
        
        # Calculate totals
        total_issued = 0
        total_options = 0
        option_granted = 0
        
        for instrument in instruments:
            initial_qty = instrument.get("initial_quantity", 0)
            class_name = instrument.get("class_name")
            sec_class = classes_map.get(class_name, {})
            class_type = sec_class.get("type", "")
            
            if class_type == "option":
                total_options += initial_qty
                # Check if granted (has actual holder, not pool)
                holder_name = instrument.get("holder_name")
                holder = holders_map.get(holder_name, {})
                if holder.get("type") != "option_pool":
                    option_granted += initial_qty
            else:
                # Common or preferred shares
                current_qty = instrument.get("current_quantity", initial_qty)
                if isinstance(current_qty, dict):
                    # Formula - use initial as estimate
                    total_issued += initial_qty
                else:
                    total_issued += current_qty
        
        # Fully diluted = issued + unexercised options
        total_fd = total_issued + total_options
        
        # Calculate per-holder ownership
        ownership = []
        holder_shares = {}  # holder_name -> {issued, fd}
        
        for instrument in instruments:
            holder_name = instrument.get("holder_name")
            initial_qty = instrument.get("initial_quantity", 0)
            current_qty = instrument.get("current_quantity", initial_qty)
            
            if isinstance(current_qty, dict):
                current_qty = initial_qty
            
            class_name = instrument.get("class_name")
            sec_class = classes_map.get(class_name, {})
            class_type = sec_class.get("type", "")
            
            if holder_name not in holder_shares:
                holder_shares[holder_name] = {"issued": 0, "fd": 0}
            
            if class_type == "option":
                # Options count in FD but not issued
                holder_shares[holder_name]["fd"] += initial_qty
            else:
                # Shares count in both
                holder_shares[holder_name]["issued"] += current_qty
                holder_shares[holder_name]["fd"] += current_qty
        
        # Build ownership list
        for holder_name, shares in holder_shares.items():
            holder = holders_map.get(holder_name, {})
            holder_type = holder.get("type", "")
            
            # Skip option pool holder itself
            if holder_type == "option_pool":
                continue
            
            ownership.append({
                "holder_name": holder_name,
                "shares_issued": shares["issued"],
                "percent_issued": (shares["issued"] / total_issued * 100) if total_issued > 0 else 0,
                "shares_fd": shares["fd"],
                "percent_fd": (shares["fd"] / total_fd * 100) if total_fd > 0 else 0
            })
        
        # Sort by FD shares descending
        ownership.sort(key=lambda x: x["shares_fd"], reverse=True)
        
        return {
            "totals": {
                "authorized": total_issued + total_options,  # Simplified
                "issued": total_issued,
                "fullyDiluted": total_fd
            },
            "ownership": ownership,
            "pool": {
                "size": total_options,
                "granted": option_granted,
                "remaining": total_options - option_granted
            }
        }
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure."""
        return {
            "totals": {
                "authorized": 0,
                "issued": 0,
                "fullyDiluted": 0
            },
            "ownership": [],
            "pool": {
                "size": 0,
                "granted": 0,
                "remaining": 0
            }
        }


# Global service instance
cap_table_service = CapTableService()

