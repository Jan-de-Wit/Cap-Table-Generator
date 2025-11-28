"""
Performance Tracker

Track generation time and performance metrics.
"""

import time
from typing import Dict, Any, Optional
from contextlib import contextmanager
from .metrics import Metrics, MetricType


class PerformanceTracker:
    """Track performance metrics."""
    
    def __init__(self):
        """Initialize performance tracker."""
        self.metrics = Metrics()
        self.active_timers: Dict[str, float] = {}
    
    @contextmanager
    def track(self, operation_name: str):
        """
        Context manager to track operation time.
        
        Args:
            operation_name: Name of operation to track
            
        Example:
            with tracker.track("excel_generation"):
                generate_excel(...)
        """
        start_time = time.time()
        try:
            yield
        finally:
            elapsed = time.time() - start_time
            self.metrics.record(operation_name, elapsed, MetricType.TIMING)
    
    def start_timer(self, timer_name: str) -> None:
        """
        Start a named timer.
        
        Args:
            timer_name: Name of timer
        """
        self.active_timers[timer_name] = time.time()
    
    def stop_timer(self, timer_name: str) -> float:
        """
        Stop a named timer and return elapsed time.
        
        Args:
            timer_name: Name of timer
            
        Returns:
            Elapsed time in seconds
        """
        if timer_name not in self.active_timers:
            raise ValueError(f"Timer '{timer_name}' not started")
        
        elapsed = time.time() - self.active_timers[timer_name]
        del self.active_timers[timer_name]
        self.metrics.record(timer_name, elapsed, MetricType.TIMING)
        return elapsed
    
    def record_metric(self, name: str, value: float, metric_type: MetricType = MetricType.TIMING) -> None:
        """
        Record a metric.
        
        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
        """
        self.metrics.record(name, value, metric_type)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        return self.metrics.get_summary()
    
    def reset(self) -> None:
        """Reset all metrics."""
        self.metrics.reset()
        self.active_timers.clear()

