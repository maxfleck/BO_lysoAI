"""
Curve difference metric.

Calculates the sum of absolute differences between test curve and reference curve.
"""

import numpy as np
import pandas as pd
from core.metrics.base_metric import BaseMetric
from scipy import integrate

class CurveDifferenceMetric(BaseMetric):
    """Metric that calculates sum of absolute differences between curves."""

    def get_name(self) -> str:
        """Return metric name for CSV column."""
        return "Sum_Abs_Difference"

    def get_description(self) -> str:
        """Return human-readable description."""
        return "Sum of absolute differences between test and reference curves"

    def _split_forward_backward(self, potential, current):
        """
        Split CV data into forward and backward sweeps.

        For standard CV (low → high → low): splits at maximum voltage.
        For inverted CV (high → low → high): splits at minimum voltage.

        Automatically detects inverted scans by checking if max is at
        the edges (first 10% or last 10% of data).

        Args:
            potential: Potential values (can be pandas Series or numpy array)
            current: Current values (can be pandas Series or numpy array)

        Returns:
            Tuple of (forward_potential, forward_current, backward_potential, backward_current)
            Each as numpy arrays.
        
        Example:
            >>> pot = pd.Series([-0.2, 0.0, 0.3, 0.6, 0.3, 0.0, -0.2])
            >>> cur = pd.Series([1e-6, 2e-6, 3e-6, 4e-6, 3e-6, 2e-6, 1e-6])
            >>> fwd_pot, fwd_cur, bwd_pot, bwd_cur = self._split_forward_backward(pot, cur)
            >>> len(fwd_pot)  # indices 0-3 (inclusive)
            4
            >>> len(bwd_pot)  # indices 3-6 (inclusive, with overlap at 3)
            4
        """
        # Convert to numpy arrays if pandas Series
        if hasattr(potential, 'values'):
            potential = potential.values
        if hasattr(current, 'values'):
            current = current.values
        
        # Find maximum and minimum indices
        max_idx = np.argmax(potential)
        min_idx = np.argmin(potential)
        
        # Check if max is near the edges (indicates inverted scan)
        n = len(potential)
        edge_threshold = int(0.1 * n)  # 10% from edges
        
        if max_idx < edge_threshold or max_idx > (n - edge_threshold):
            # Max is at edge → likely inverted scan (high → low → high)
            # Use minimum as transition point
            transition_idx = min_idx
        else:
            # Max is in middle → standard scan (low → high → low)
            # Use maximum as transition point
            transition_idx = max_idx
        
        # Split at transition point (inclusive on both sides)
        # Forward: from start to transition (inclusive)
        forward_potential = potential[:transition_idx + 1]
        forward_current = current[:transition_idx + 1]
        
        # Backward: from transition to end (inclusive)
        backward_potential = potential[transition_idx:]
        backward_current = current[transition_idx:]
        
        return forward_potential, forward_current, backward_potential, backward_current

    def _interpolate_reference_to_test(self, x, x_ref, y_ref):
        """
        Interpolate reference current to test potential values.
        
        This ensures that test and reference have matching potential grids,
        so we can calculate pointwise differences.
        
        Args:
            x: Test potential values (numpy array)
            x_ref: Reference potential values (numpy array)
            y_ref: Reference current values (numpy array)
        
        Returns:
            y_ref_interp: Reference current interpolated at test potential (x) points
        """
        from scipy.interpolate import interp1d
        
        # Create interpolation function
        # kind='linear': linear interpolation (standard for CV)
        # bounds_error=False: don't raise error if test extends beyond ref
        # fill_value='extrapolate': extrapolate at boundaries if needed
        f_interp = interp1d(
            x_ref,
            y_ref,
            kind='linear',
            bounds_error=False,
            fill_value='extrapolate'
        )
        
        # Apply interpolation: get ref current at test potential values
        y_ref_interp = f_interp(x)
        
        return y_ref_interp


    def calculate(self, data_df: pd.DataFrame, ref_data_df: pd.DataFrame) -> float:
        """
        Calculate sum of absolute differences.

        Calculates sum of absolute differences.

        Args:
            data_df: Test data with Potential_V and Current_A columns
            ref_data_df: Reference data with Potential_V and Current_A columns

        Returns:
            float: Sum of absolute differences
        """

        # Split into forward and backward sweeps
        dummy = self._split_forward_backward(  data_df["Potential_V"], 
                                           data_df["Current_A"])
        x , y, xb, yb = dummy
        dummy_ref = self._split_forward_backward(  ref_data_df["Potential_V"], 
                                                    ref_data_df["Current_A"])
        x_ref, y_ref, xb_ref, yb_ref = dummy_ref

        # Interpolate reference to test potentials
        y_ref_interp = self._interpolate_reference_to_test(x, x_ref, y_ref)
        yb_ref_interp = self._interpolate_reference_to_test(xb, xb_ref, yb_ref)

        # Calculate differences
        y_diff = np.abs(y - y_ref_interp)
        yb_diff = np.abs(yb - yb_ref_interp)

        # Integrate using trapezoidal rule
        y_int = integrate.trapezoid(y_diff, x=x)
        yb_int = integrate.trapezoid(yb_diff, x=xb)

        # Return sum of absolute integrated differences
        return np.abs(y_int) + np.abs(yb_int)