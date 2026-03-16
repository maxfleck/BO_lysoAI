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

    def get_column_names(self) -> list:
        """
        Return the CSV column name(s) produced by this metric.

        Override when calculate() returns a dict to declare all column names.
        Single-value metrics don't need to override this.

        Returns:
            list: Column names. Default: [self.name]
        """
        return [self.name]

    def requires_interpolation(self) -> bool:
        """
        Indicate whether this metric requires reference interpolation.

        Override this method if your metric doesn't need interpolation.

        Returns:
            bool: True if metric needs interpolation (default), False otherwise
        """
        return True

    def get_plot_data(self, _data_df: pd.DataFrame, _ref_data_df: pd.DataFrame) -> list:
        """
        Return Plotly traces to overlay on the plot for this file.

        Override this method to draw lines, markers, etc. alongside the CV curve.
        Each item in the returned list should be a plotly.graph_objects trace
        (e.g. go.Scatter(...)) or a dict accepted by fig.add_trace().

        Args:
            data_df: Test data DataFrame with columns: Potential_V, Current_A
            ref_data_df: Reference data DataFrame with columns: Potential_V, Current_A

        Returns:
            list: Plotly traces to add to the figure. Default: empty list.
        """
        return []
