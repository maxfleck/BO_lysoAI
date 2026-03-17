"""
Min-Max range metric.

Calculates the range (max - min) of differences between test and reference curves.
"""

import pandas as pd
import plotly.graph_objects as go
import config
from core.metrics.base_metric import BaseMetric


class MinMaxDifferenceMetric(BaseMetric):
    """Metric that calculates the range of differences between curves."""

    def __init__(self, marker_color='orange', marker_symbol='circle', marker_size=10):
        self.marker_color = marker_color
        self.marker_symbol = marker_symbol
        self.marker_size = marker_size
        super().__init__()

    def get_name(self) -> str:
        """Return metric name for CSV column."""
        return "Min_Max_Range"

    def get_column_names(self) -> list:
        return [self._with_unit('Min_Max_Range', config.CURRENT_UNIT)]

    def get_description(self) -> str:
        """Return human-readable description."""
        return "Range (max - min) of differences between test and reference curves"

    def calculate(self, data_df: pd.DataFrame, ref_data_df: pd.DataFrame) -> dict:
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

        # Calculate difference
        diff = data_df[config.CURRENT_COLUMN] - ref_data_df[config.CURRENT_COLUMN]

        return {self._with_unit('Min_Max_Range', config.CURRENT_UNIT): diff.max() - diff.min()}

    def get_plot_data(self, data_df: pd.DataFrame, ref_data_df: pd.DataFrame) -> list:
        """Return markers at the max and min difference positions on the test curve."""
        # diff = (data_df["Current_A"] - ref_data_df["Current_A"]).values
        x = data_df[config.POTENTIAL_COLUMN].values
        y = data_df[config.CURRENT_COLUMN].values
        max_i, min_i = int(y.argmax()), int(y.argmin())
        style = dict(color=self.marker_color, symbol=self.marker_symbol, size=self.marker_size)
        hover = f'<b>%{{text}}</b><br>Potential: %{{x:.4f}} {config.POTENTIAL_UNIT}<br>Current: %{{y:.2e}} {config.CURRENT_UNIT}<extra></extra>'
        return [
            go.Scatter(x=[x[max_i]], y=[y[max_i]], mode='markers',
                       marker=style, name='Max', showlegend=False,
                       text=['Max'], hovertemplate=hover),
            go.Scatter(x=[x[min_i]], y=[y[min_i]], mode='markers',
                       marker={**style, 'symbol': self.marker_symbol + '-open'},
                       name='Min', showlegend=False,
                       text=['Min'], hovertemplate=hover),
        ]
