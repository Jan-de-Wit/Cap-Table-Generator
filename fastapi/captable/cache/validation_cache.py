"""
Validation Cache

Cache validation results for performance.
"""

from typing import Dict, Optional, Tuple, Any
import hashlib
import json


class ValidationCache:
    """Cache for validation results."""
    
    def __init__(self, max_size: int = 100):
        """
        Initialize validation cache.
        
        Args:
            max_size: Maximum number of cached results
        """
        self.cache: Dict[str, Tuple[bool, list[str]]] = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def _generate_key(self, data: Dict[str, Any]) -> str:
        """
        Generate cache key from data.
        
        Args:
            data: Cap table data
            
        Returns:
            Cache key string
        """
        # Create deterministic key (simplified - in production might want to hash only relevant parts)
        key_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, data: Dict[str, Any]) -> Optional[Tuple[bool, list[str]]]:
        """
        Get cached validation result.
        
        Args:
            data: Cap table data
            
        Returns:
            Tuple of (is_valid, errors) or None if not found
        """
        key = self._generate_key(data)
        if key in self.cache:
            self.hits += 1
            return self.cache[key]
        self.misses += 1
        return None
    
    def set(
        self,
        data: Dict[str, Any],
        is_valid: bool,
        errors: list[str]
    ) -> None:
        """
        Cache validation result.
        
        Args:
            data: Cap table data
            is_valid: Validation result
            errors: List of error messages
        """
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            first_key = next(iter(self.cache))
            del self.cache[first_key]
        
        key = self._generate_key(data)
        self.cache[key] = (is_valid, errors)
    
    def clear(self) -> None:
        """Clear cache."""
        self.cache.clear()
        self.hits = 0
        self.misses += 1
    
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




