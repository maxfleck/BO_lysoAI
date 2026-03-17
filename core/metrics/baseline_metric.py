"""
CV Baseline metric.

Fits a linear capacitive baseline to the forward and backward sweeps of a
cyclic voltammetry curve using a wide-stencil derivative approach (from analyze3).

Returns 4 values (2 per sub-curve):
  Forward_Area, Backward_Area  — area between curve and baseline
  Forward_Peak, Backward_Peak  — max(curve - baseline)

Also plots the two baseline lines via get_plot_data().
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import integrate
import config
from core.metrics.base_metric import BaseMetric


class BaselineMetric(BaseMetric):
    """Capacitive baseline fitting for forward and backward CV sweeps."""

    def __init__(self, k=0.1, thresh_frac=0.3, offset=0.3, skip_frac=0.1,
                 fwd_color='darkgrey', bwd_color='darkgrey', zorder=-1):
        self.k = k
        self.thresh_frac = thresh_frac
        self.offset = offset
        self.skip_frac = skip_frac
        self.fwd_color = fwd_color
        self.bwd_color = bwd_color
        self.zorder = zorder
        super().__init__()

    def get_name(self) -> str:
        return "Baseline"

    def get_column_names(self) -> list:
        u, v = config.CURRENT_UNIT, config.POTENTIAL_UNIT
        return [
            self._with_unit('Forward_Area',  u, v),
            self._with_unit('Backward_Area', u, v),
            self._with_unit('Forward_Peak',  u),
            self._with_unit('Backward_Peak', u),
        ]

    def get_description(self) -> str:
        return "Capacitive baseline fit — area and peak distance for forward and backward sweeps"

    def _split(self, x, y):
        """Split CV curve into forward and backward sweeps at max potential."""
        max_idx = int(np.argmax(x))
        x_f = x[:max_idx + 1]
        y_f = y[:max_idx + 1]
        x_b = x[max_idx:]
        y_b = -y[max_idx:]  # negate for baseline analysis
        return x_f, y_f, x_b, y_b

    def _find_linear_end(self, x0, y0):
        """Find mean slope of the flat (linear) region before Faradaic onset.

        Returns (mean_slope, onset_idx, mid_idx).
        """
        x_norm = np.max(x0) - np.min(x0)
        y_norm = np.max(y0) - np.min(y0)
        x = x0 / x_norm if x_norm > 0 else x0
        y = y0 / y_norm if y_norm > 0 else y0

        thresh_frac = self.thresh_frac

        dx = abs(x[1] - x[0])
        N = len(y)
        k = max(1, int(self.k * N))
        y = y

        # Wide-stencil 2nd derivative
        d2y = np.array([(y[i + k] - 2 * y[i] + y[i - k]) / (k * dx) ** 2
                        for i in range(k, N - k)])

        # Skip the first skip_frac of the curve to avoid transients at the start
        skip_d2y = max(0, int(self.skip_frac * N) - k)
        d2y_search = d2y[skip_d2y:]
        d2y_max = np.max(d2y_search) if len(d2y_search) > 0 else 0
        if d2y_max > 0:
            above = np.where(d2y_search > thresh_frac * d2y_max)[0]
            onset_idx = k + skip_d2y + above[0] if len(above) > 0 else N // 4
        else:
            onset_idx = N // 4

        onset_idx = max(k, min(onset_idx, N - k - 1))

        # Convert relative offset to absolute index count
        abs_offset = max(1, int(self.offset * onset_idx))

        flat_end = max(k + 1, onset_idx - abs_offset)

        # Wide-stencil 1st derivative
        d1y = np.array([(y[i + k] - y[i - k]) / (2 * k * dx) for i in range(k, N - k)])

        win_end = flat_end - k
        win_start = max(0, win_end - abs_offset)
        mean_slope = float(np.mean(d1y[win_start:win_end]))
        mid_idx = k + (win_start + win_end) // 2

        x_norm_val = x_norm if x_norm > 0 else 1.0
        return mean_slope * y_norm / x_norm_val, onset_idx, mid_idx  # slope in A/V

    def _baselines(self, x, y):
        """Compute baselines for both sweeps.

        Returns (a0f, a1f, x_f, y_f, a0b, a1b, x_b, y_b_orig) where
        y_f and y_b_orig are in original (un-negated) coordinates.
        """
        x_f, y_f, x_b, y_b = self._split(x, y)

        a1f, _, mid_f = self._find_linear_end(x_f, y_f)
        a0f = float(y_f[mid_f] - a1f * x_f[mid_f])

        a1b, _, mid_b = self._find_linear_end(x_b, y_b)
        # y_b is negated; original y = -y_b → anchor in original coords
        a0b = float(-y_b[mid_b] - a1b * x_b[mid_b])

        y_b_orig = -y_b  # back to original sign
        return a0f, a1f, x_f, y_f, a0b, a1b, x_b, y_b_orig

    def calculate(self, data_df: pd.DataFrame, ref_data_df: pd.DataFrame) -> dict:
        x = data_df[config.POTENTIAL_COLUMN].values
        y = data_df[config.CURRENT_COLUMN].values

        a0f, a1f, x_f, y_f, a0b, a1b, x_b, y_b_orig = self._baselines(x, y)

        baseline_f = a0f + a1f * x_f
        diff_f = y_f - baseline_f

        baseline_b = a0b + a1b * x_b
        diff_b = y_b_orig - baseline_b

        u, v = config.CURRENT_UNIT, config.POTENTIAL_UNIT
        return {
            self._with_unit('Forward_Area',  u, v): float(integrate.trapezoid(np.abs(diff_f), x_f)),
            self._with_unit('Backward_Area', u, v): float(integrate.trapezoid(np.abs(diff_b), x_b)),
            self._with_unit('Forward_Peak',  u):    float(np.max(diff_f)),
            self._with_unit('Backward_Peak', u):    float(-np.min(diff_b)),
        }

    def get_plot_data(self, data_df: pd.DataFrame, ref_data_df: pd.DataFrame) -> list:
        x = data_df[config.POTENTIAL_COLUMN].values
        y = data_df[config.CURRENT_COLUMN].values

        a0f, a1f, x_f, y_f, a0b, a1b, x_b, y_b_orig = self._baselines(x, y)

        # Peak positions (same logic as calculate())
        diff_f = y_f - (a0f + a1f * x_f)
        diff_b = y_b_orig - (a0b + a1b * x_b)
        x_peak_f = x_f[int(np.argmax(diff_f))]
        x_peak_b = x_b[int(np.argmin(diff_b))]

        hover = f'<b>%{{text}}</b><br>Potential: %{{x:.4f}} {config.POTENTIAL_UNIT}<br>Current: %{{y:.2e}} {config.CURRENT_UNIT}<extra></extra>'
        return [
            go.Scatter(
                x=x, y=a0f + a1f * x,
                mode='lines',
                line=dict(color=self.fwd_color, width=1.5),
                opacity=0.5,
                zorder=self.zorder,
                showlegend=False,
                text=['Fwd baseline'] * len(x),
                hovertemplate=hover,
            ),
            go.Scatter(
                x=x, y=a0b + a1b * x,
                mode='lines',
                line=dict(color=self.bwd_color, width=1.5),
                opacity=0.5,
                zorder=self.zorder,
                showlegend=False,
                text=['Bwd baseline'] * len(x),
                hovertemplate=hover,
            ),
            go.Scatter(
                x=[x_peak_f], y=[a0f + a1f * x_peak_f],
                mode='markers',
                marker=dict(color=self.fwd_color, size=8, symbol='circle'),
                opacity=0.8,
                zorder=self.zorder,
                showlegend=False,
                hovertemplate=f'<b>Fwd peak</b><br>Potential: %{{x:.4f}} {config.POTENTIAL_UNIT}<br>Current: %{{y:.2e}} {config.CURRENT_UNIT}<extra></extra>',
            ),
            go.Scatter(
                x=[x_peak_b], y=[a0b + a1b * x_peak_b],
                mode='markers',
                marker=dict(color=self.bwd_color, size=8, symbol='circle'),
                opacity=0.8,
                zorder=self.zorder,
                showlegend=False,
                hovertemplate=f'<b>Bwd peak</b><br>Potential: %{{x:.4f}} {config.POTENTIAL_UNIT}<br>Current: %{{y:.2e}} {config.CURRENT_UNIT}<extra></extra>',
            ),
        ]
