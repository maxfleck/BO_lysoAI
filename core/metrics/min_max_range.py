"""
Min-Max range metric.

Calculates the range (max - min) of differences between test and reference curves.
"""

import numpy as np
import pandas as pd
from core.metrics.base_metric import BaseMetric


class MinMaxDifferenceMetric(BaseMetric):
    """Metric that calculates the range of differences between curves."""

    def get_name(self) -> str:
        """Return metric name for CSV column."""
        return "Min_Max_Range"

    def get_description(self) -> str:
        """Return human-readable description."""
        return "Range (max - min) of differences between test and reference curves"

    def calculate(self, data_df: pd.DataFrame, ref_data_df: pd.DataFrame) -> float:
        """
        Calculate min-max range of differences.

        Interpolates reference current values at test potentials,
        then calculates the range (max - min) of differences.

        Args:
            data_df: Test data with Potential_V and Current_A columns
            ref_data_df: Reference data with Potential_V and Current_A columns

        Returns:
            float: Range of differences (max - min)
        """
        # Interpolate reference current at same potentials as test data
        interp_ref_current = np.interp(
            data_df["Potential_V"],
            ref_data_df["Potential_V"],
            ref_data_df["Current_A"]
        )

        # Calculate difference
        diff = data_df["Current_A"] - interp_ref_current

        # Return range (max - min)
        return diff.max() - diff.min()
