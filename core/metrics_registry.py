"""
Metrics registry for managing and calculating analysis metrics.

Uses singleton pattern to ensure only one registry instance exists.
"""

import numpy as np
import pandas as pd
from typing import Dict
from core.metrics.base_metric import BaseMetric


class MetricsRegistry:
    """Singleton registry for extensible metrics."""

    _instance = None

    def __new__(cls):
        """Create singleton instance if it doesn't exist."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.metrics = {}
        return cls._instance

    def register(self, metric: BaseMetric) -> None:
        """
        Register a new metric.

        Args:
            metric: Instance of a class inheriting from BaseMetric
        """
        self.metrics[metric.name] = metric

    def get_all(self) -> Dict[str, BaseMetric]:
        """
        Get all registered metrics.

        Returns:
            dict: Dictionary of metric name -> metric instance
        """
        return self.metrics.copy()

    def get_metric_names(self) -> list:
        """
        Get list of all registered metric names.

        Returns:
            list: List of metric names
        """
        return list(self.metrics.keys())

    def calculate_all(self, data_df: pd.DataFrame, ref_data_df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate all registered metrics.

        Args:
            data_df: Test data DataFrame with columns: Potential_V, Current_A
            ref_data_df: Reference data DataFrame with columns: Potential_V, Current_A

        Returns:
            dict: Dictionary of metric name -> calculated value
        """
        results = {}
        for name, metric in self.metrics.items():
            try:
                results[name] = metric.calculate(data_df, ref_data_df)
            except Exception as e:
                # Log error and store NaN for failed calculations
                print(f"Error calculating {name}: {str(e)}")
                results[name] = np.nan
        return results

    def clear(self) -> None:
        """Clear all registered metrics (useful for testing)."""
        self.metrics = {}
