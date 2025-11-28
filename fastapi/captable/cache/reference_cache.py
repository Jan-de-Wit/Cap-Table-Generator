"""
Reference Cache

Cache resolved Excel references for performance.
"""

from typing import Dict, Optional, Any
from ..types import ExcelReference


class ReferenceCache:
    """Cache for Excel references."""
    
    def __init__(self, max_size: int = 500):
        """
        Initialize reference cache.
        
        Args:
            max_size: Maximum number of cached references
        """
        self.cache: Dict[str, ExcelReference] = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def get(self, identifier: str) -> Optional[ExcelReference]:
        """
        Get cached reference.
        
        Args:
            identifier: Reference identifier
            
        Returns:
            Cached reference or None if not found
        """
        if identifier in self.cache:
            self.hits += 1
            return self.cache[identifier]
        self.misses += 1
        return None
    
    def set(self, identifier: str, reference: ExcelReference) -> None:
        """
        Cache reference.
        
        Args:
            identifier: Reference identifier
            reference: Reference to cache
        """
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            first_key = next(iter(self.cache))
            del self.cache[first_key]
        
        self.cache[identifier] = reference
    
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

