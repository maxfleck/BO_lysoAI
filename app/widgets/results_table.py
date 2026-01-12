"""
Results table widget for displaying analysis results.
"""

from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import pandas as pd
import config


class ResultsTableWidget(QTableWidget):
    """Widget for displaying results in table format."""

    def __init__(self):
        """Initialize results table widget."""
        super().__init__()

        # Table settings
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Header settings
        self.horizontalHeader().setStretchLastSection(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.verticalHeader().setVisible(False)

    def update_results(self, results_df: pd.DataFrame):
        """
        Display results DataFrame in table.

        Args:
            results_df: DataFrame with analysis results
        """
        if results_df.empty:
            self.clear()
            return

        # Set dimensions
        self.setRowCount(len(results_df))
        self.setColumnCount(len(results_df.columns))
        self.setHorizontalHeaderLabels(results_df.columns.tolist())

        # Fill table
        for i, row in results_df.iterrows():
            is_reference = row.get(config.REFERENCE_FLAG_COLUMN, False)

            for j, (col_name, value) in enumerate(row.items()):
                # Format value
                if pd.isna(value):
                    text = "N/A"
                elif isinstance(value, float):
                    # Format floats with scientific notation if needed
                    if abs(value) < 0.001 or abs(value) > 1000:
                        text = f"{value:.3e}"
                    else:
                        text = f"{value:.6f}"
                elif isinstance(value, bool):
                    text = "Yes" if value else "No"
                else:
                    text = str(value)

                item = QTableWidgetItem(text)

                # Highlight reference row
                if is_reference:
                    item.setBackground(QColor(255, 255, 200))  # Light yellow
                    item.setForeground(QColor(0, 0, 0))

                # Center alignment for boolean and numeric columns
                if col_name == config.REFERENCE_FLAG_COLUMN or isinstance(value, (int, float)):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                self.setItem(i, j, item)

        # Resize columns to content
        self.resizeColumnsToContents()

        # Set minimum column widths
        for col in range(self.columnCount()):
            if self.columnWidth(col) < 100:
                self.setColumnWidth(col, 100)

    def clear_results(self):
        """Clear all results from table."""
        self.setRowCount(0)
        self.setColumnCount(0)
