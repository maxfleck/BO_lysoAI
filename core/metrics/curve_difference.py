"""
Curve difference metric.

Calculates the sum of absolute differences between test curve and reference curve.
"""

import numpy as np
import pandas as pd
from core.metrics.base_metric import BaseMetric


class CurveDifferenceMetric(BaseMetric):
    """Metric that calculates sum of absolute differences between curves."""

    def get_name(self) -> str:
        """Return metric name for CSV column."""
        return "Sum_Abs_Difference"

    def get_description(self) -> str:
        """Return human-readable description."""
        return "Sum of absolute differences between test and reference curves"

    def calculate(self, data_df: pd.DataFrame, ref_data_df: pd.DataFrame) -> float:
        """
        Calculate sum of absolute differences.

        Interpolates reference current values at test potentials,
        then calculates sum of absolute differences.

        Args:
            data_df: Test data with Potential_V and Current_A columns
            ref_data_df: Reference data with Potential_V and Current_A columns

        Returns:
            float: Sum of absolute differences
        """
        # Interpolate reference current at same potentials as test data
        interp_ref_current = np.interp(
            data_df["Potential_V"],
            ref_data_df["Potential_V"],
            ref_data_df["Current_A"]
        )

        # Calculate difference
        diff = data_df["Current_A"] - interp_ref_current

        # Return sum of absolute differences
        return np.abs(diff).sum()
