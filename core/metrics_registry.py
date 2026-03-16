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
        Get list of all column names produced by registered metrics.

        Multi-value metrics (calculate() returns a dict) contribute multiple names.

        Returns:
            list: Flat list of column names
        """
        names = []
        for metric in self.metrics.values():
            names.extend(metric.get_column_names())
        return names

    def calculate_all(self, data_df: pd.DataFrame, ref_data_df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate all registered metrics.

        Args:
            data_df: Test data DataFrame with columns: Potential_V, Current_A
            ref_data_df: Reference data DataFrame with columns: Potential_V, Current_A

        Returns:
            dict: Dictionary of column name -> calculated value. Multi-value metrics
                  contribute multiple keys when calculate() returns a dict.
        """
        results = {}
        for name, metric in self.metrics.items():
            try:
                value = metric.calculate(data_df, ref_data_df)
                if isinstance(value, dict):
                    results.update(value)
                else:
                    results[name] = value
            except Exception as e:
                print(f"Error calculating {name}: {str(e)}")
                for col in metric.get_column_names():
                    results[col] = np.nan
        return results

    def collect_plot_data(self, data_df: pd.DataFrame, ref_data_df: pd.DataFrame) -> list:
        """
        Collect plot traces from all registered metrics.

        Args:
            data_df: Test data DataFrame
            ref_data_df: Reference data DataFrame

        Returns:
            list: All Plotly traces returned by metrics' get_plot_data()
        """
        traces = []
        for name, metric in self.metrics.items():
            try:
                traces.extend(metric.get_plot_data(data_df, ref_data_df))
            except Exception as e:
                print(f"Error getting plot data from {name}: {e}")
        return traces

    def clear(self) -> None:
        """Clear all registered metrics (useful for testing)."""
        self.metrics = {}
