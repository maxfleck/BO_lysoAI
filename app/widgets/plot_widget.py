"""
Plot widget for displaying electrochemical curves.
"""

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
import config


class PlotWidget(QWidget):
    """Widget for embedded matplotlib plotting."""

    def __init__(self):
        """Initialize plot widget."""
        super().__init__()

        # Create matplotlib figure (no fixed figsize for responsive resizing)
        self.figure = Figure(dpi=config.PLOT_DPI)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.ax = self.figure.add_subplot(111)

        # Make canvas expand to fill available space
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.canvas.updateGeometry()

        # Create layout with no margins for maximum space
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        # Initialize plot
        self.clear_plot()

    def clear_plot(self):
        """Clear the plot."""
        self.ax.clear()
        self.ax.set_xlabel('Potential (V)')
        self.ax.set_ylabel('Current (A)')
        self.ax.set_title('Cyclic Voltammetry Curves')
        self.ax.grid(True, alpha=config.PLOT_GRID_ALPHA)
        self.canvas.draw()

    def plot_data(self, reference_data, test_data_list):
        """
        Plot reference and test curves.

        Args:
            reference_data: DataFrame with Potential_V and Current_A columns
            test_data_list: List of tuples (data_df, filename)
        """
        self.ax.clear()

        # Plot reference with thick red line
        self.ax.plot(
            reference_data[config.POTENTIAL_COLUMN],
            reference_data[config.CURRENT_COLUMN],
            color=config.REFERENCE_LINE_COLOR,
            linewidth=config.REFERENCE_LINE_WIDTH,
            # Future use: pass reference filename for label
            # label=reference_filename + '(Reference)',
            label='Reference',
            zorder=10
        )

        # Plot test curves with normal thickness and various colors
        if test_data_list:
            # Generate colors
            num_curves = len(test_data_list)
            colors = plt.cm.tab10(range(num_curves))

            for (data, filename), color in zip(test_data_list, colors):
                # Skip if this is the reference (already plotted)
                if 'BARE' in filename.upper() or 'REFERENCE' in filename.upper():
                    continue

                self.ax.plot(
                    data[config.POTENTIAL_COLUMN],
                    data[config.CURRENT_COLUMN],
                    alpha=config.TEST_LINE_ALPHA,
                    label=filename,
                    color=color
                )

        # Customize plot
        self.ax.set_xlabel('Potential (V)', fontsize=12)
        self.ax.set_ylabel('Current (A)', fontsize=12)
        self.ax.set_title('Cyclic Voltammetry Curves', fontsize=14, fontweight='bold')
        self.ax.grid(True, alpha=config.PLOT_GRID_ALPHA)

        # Add legend
        self.ax.legend(loc='best', fontsize=8, framealpha=0.9)

        # Tight layout
        self.figure.tight_layout()

        # Redraw canvas
        self.canvas.draw()

    def save_plot(self, filepath):
        """
        Save plot to file.

        Args:
            filepath: Path where to save the plot
        """
        try:
            self.figure.savefig(filepath, dpi=300, bbox_inches='tight')
            return True
        except Exception as e:
            print(f"Error saving plot: {str(e)}")
            return False
