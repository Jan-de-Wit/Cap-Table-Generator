"""
Formula Cache

Cache generated Excel formulas for performance.
"""

from typing import Dict, Optional, Any
import hashlib
import json


class FormulaCache:
    """Cache for Excel formulas."""
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize formula cache.
        
        Args:
            max_size: Maximum number of cached formulas
        """
        self.cache: Dict[str, str] = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def _generate_key(self, calculation_type: str, params: Dict[str, Any]) -> str:
        """
        Generate cache key from parameters.
        
        Args:
            calculation_type: Type of calculation
            params: Calculation parameters
            
        Returns:
            Cache key string
        """
        # Create deterministic key from parameters
        key_data = {
            "type": calculation_type,
            "params": params
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(
        self,
        calculation_type: str,
        params: Dict[str, Any]
    ) -> Optional[str]:
        """
        Get cached formula.
        
        Args:
            calculation_type: Type of calculation
            params: Calculation parameters
            
        Returns:
            Cached formula or None if not found
        """
        key = self._generate_key(calculation_type, params)
        if key in self.cache:
            self.hits += 1
            return self.cache[key]
        self.misses += 1
        return None
    
    def set(
        self,
        calculation_type: str,
        params: Dict[str, Any],
        formula: str
    ) -> None:
        """
        Cache formula.
        
        Args:
            calculation_type: Type of calculation
            params: Calculation parameters
            formula: Formula to cache
        """
        if len(self.cache) >= self.max_size:
            # Remove oldest entry (simple FIFO)
            first_key = next(iter(self.cache))
            del self.cache[first_key]
        
        key = self._generate_key(calculation_type, params)
        self.cache[key] = formula
    
    def clear(self) -> None:
        """Clear cache."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0.0
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate
        }

