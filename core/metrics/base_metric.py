"""
Base metric class for extensible analysis metrics.

All custom metrics should inherit from BaseMetric and implement
the required abstract methods.
"""

from abc import ABC, abstractmethod
import pandas as pd


class BaseMetric(ABC):
    """Abstract base class for analysis metrics."""

    def __init__(self):
        """Initialize metric with name and description."""
        self.name = self.get_name()
        self.description = self.get_description()

    @abstractmethod
    def get_name(self) -> str:
        """
        Return metric name for CSV column header.

        Returns:
            str: Short name without spaces (e.g., "Sum_Abs_Difference")
        """
        pass

    @abstractmethod
    def get_description(self) -> str:
        """
        Return human-readable description of the metric.

        Returns:
            str: Description of what the metric calculates
        """
        pass

    @abstractmethod
    def calculate(self, data_df: pd.DataFrame, ref_data_df: pd.DataFrame) -> float:
        """
        Calculate the metric value for given data against reference.

        Args:
            data_df: Test data DataFrame with columns: Potential_V, Current_A
            ref_data_df: Reference data DataFrame with columns: Potential_V, Current_A

        Returns:
            float: Calculated metric value
        """
        pass

    def requires_interpolation(self) -> bool:
        """
        Indicate whether this metric requires reference interpolation.

        Override this method if your metric doesn't need interpolation.

        Returns:
            bool: True if metric needs interpolation (default), False otherwise
        """
        return True
