"""
Metrics

Performance metrics collection and aggregation.
"""

from enum import Enum
from typing import Dict, List, Any
from collections import defaultdict


class MetricType(Enum):
    """Metric type enumeration."""
    TIMING = "timing"
    COUNTER = "counter"
    GAUGE = "gauge"


class Metrics:
    """Collect and aggregate performance metrics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.timings: Dict[str, List[float]] = defaultdict(list)
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
    
    def record(self, name: str, value: float, metric_type: MetricType = MetricType.TIMING) -> None:
        """
        Record a metric.
        
        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
        """
        if metric_type == MetricType.TIMING:
            self.timings[name].append(value)
        elif metric_type == MetricType.COUNTER:
            self.counters[name] += int(value)
        elif metric_type == MetricType.GAUGE:
            self.gauges[name] = value
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        summary: Dict[str, Any] = {
            "timings": {},
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
        }
        
        # Calculate timing statistics
        for name, values in self.timings.items():
            if values:
                summary["timings"][name] = {
                    "count": len(values),
                    "total": sum(values),
                    "average": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                }
        
        return summary
    
    def reset(self) -> None:
        """Reset all metrics."""
        self.timings.clear()
        self.counters.clear()
        self.gauges.clear()




