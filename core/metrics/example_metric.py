"""
Example metric template.

This is a template showing how to create new metrics.
Copy this file and modify to create your own custom metrics.
"""

import numpy as np
import pandas as pd
from core.metrics.base_metric import BaseMetric


class ExampleMetric(BaseMetric):
    """
    Example metric template.

    Replace this with your metric's description.
    """

    def get_name(self) -> str:
        """
        Return metric name for CSV column.

        Replace with your metric's name (use underscores, no spaces).
        Example: "Peak_Height", "Area_Under_Curve", etc.
        """
        return "Example_Metric"

    def get_description(self) -> str:
        """
        Return human-readable description.

        Replace with a clear description of what your metric calculates.
        """
        return "Example metric - replace with your own calculation"

    def calculate(self, data_df: pd.DataFrame, ref_data_df: pd.DataFrame) -> float:
        """
        Calculate your custom metric.

        Args:
            data_df: Test data with Potential_V and Current_A columns
            ref_data_df: Reference data with Potential_V and Current_A columns

        Returns:
            float: Your calculated metric value
        """
        # Example: Calculate maximum current (doesn't use reference)
        # Replace with your own calculation logic
        return data_df["Current_A"].max()

    def requires_interpolation(self) -> bool:
        """
        Override if your metric doesn't need reference interpolation.

        Returns:
            bool: False if metric doesn't use reference data
        """
        return False  # This example doesn't use reference


# USAGE INSTRUCTIONS:
# ====================
# 1. Copy this file to a new file in core/metrics/ directory
#    Example: cp example_metric.py peak_height.py
#
# 2. Rename the class (ExampleMetric -> YourMetricName)
#
# 3. Implement the three required methods:
#    - get_name(): Return column name for CSV
#    - get_description(): Return human-readable description
#    - calculate(): Implement your calculation logic
#
# 4. Optional: Override requires_interpolation() if you don't need reference data
#
# 5. Register your metric in main.py:
#    from core.metrics.your_metric import YourMetricName
#    registry.register(YourMetricName())
#
# That's it! Your metric will automatically:
#  - Appear in results table
#  - Be saved to CSV and Excel
#  - Be calculated for all processed files
