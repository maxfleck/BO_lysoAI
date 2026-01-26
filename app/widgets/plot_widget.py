"""
Interactive plot widget using Plotly for displaying electrochemical curves.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PyQt6.QtWebEngineWidgets import QWebEngineView
import plotly.graph_objects as go
import plotly.io as pio
import config


class PlotWidget(QWidget):
    """Widget for embedded interactive Plotly plotting."""

    def __init__(self):
        """Initialize plot widget."""
        super().__init__()

        # Create web view for Plotly HTML
        self.web_view = QWebEngineView()
        self.web_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Store current figure for saving
        self.current_fig = None

        # Create layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.web_view)
        self.setLayout(layout)

        # Initialize with empty plot
        self.clear_plot()

    def clear_plot(self):
        """Clear the plot and show empty state."""
        fig = go.Figure()
        fig.update_layout(
            title='Cyclic Voltammetry Curves',
            xaxis_title='Potential (V)',
            yaxis_title='Current (A)',
            template=config.PLOT_TEMPLATE,
            showlegend=True,
        )
        self._render_figure(fig)

    def plot_data(self, reference_data, test_data_list):
        """
        Plot reference and test curves.

        Args:
            reference_data: DataFrame with Potential_V and Current_A columns
            test_data_list: List of tuples (data_df, filename)
        """
        fig = go.Figure()

        # Plot reference curve with thick magenta line
        fig.add_trace(go.Scatter(
            x=reference_data[config.POTENTIAL_COLUMN],
            y=reference_data[config.CURRENT_COLUMN],
            mode='lines',
            name='Reference',
            line=dict(
                color=config.REFERENCE_LINE_COLOR,
                width=config.REFERENCE_LINE_WIDTH
            ),
            hovertemplate='<b>Reference</b><br>Potential: %{x:.4f} V<br>Current: %{y:.2e} A<extra></extra>'
        ))

        # Plot test curves
        if test_data_list:
            # Use Plotly's default color sequence
            colors = pio.templates[config.PLOT_TEMPLATE].layout.colorway
            if not colors:
                colors = pio.templates['plotly'].layout.colorway

            for i, (data, filename) in enumerate(test_data_list):
                # Skip reference files
                if 'BARE' in filename.upper() or 'REFERENCE' in filename.upper():
                    continue

                color = colors[i % len(colors)]

                fig.add_trace(go.Scatter(
                    x=data[config.POTENTIAL_COLUMN],
                    y=data[config.CURRENT_COLUMN],
                    mode='lines',
                    name=filename,
                    line=dict(width=1.5),
                    opacity=config.TEST_LINE_ALPHA,
                    hovertemplate=f'<b>{filename}</b><br>Potential: %{{x:.4f}} V<br>Current: %{{y:.2e}} A<extra></extra>'
                ))

        # Update layout
        fig.update_layout(
            title=dict(
                text='Cyclic Voltammetry Curves',
                font=dict(size=16)
            ),
            xaxis_title='Potential (V)',
            yaxis_title='Current (A)',
            template=config.PLOT_TEMPLATE,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=1.02
            ),
            hovermode='closest',
            margin=dict(r=150),  # Extra margin for legend
        )

        self._render_figure(fig)

    def _render_figure(self, fig):
        """
        Render Plotly figure to the web view.

        Args:
            fig: Plotly figure object
        """
        self.current_fig = fig

        # Configure interactivity
        plotly_config = {
            'editable': True,  # Allow editing axis labels and legend
            'displayModeBar': True,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
            'toImageButtonOptions': {
                'format': 'png',
                'height': config.PLOT_EXPORT_HEIGHT,
                'width': config.PLOT_EXPORT_WIDTH,
                'scale': config.PLOT_EXPORT_SCALE
            },
            'displaylogo': False,
        }

        # Generate HTML with embedded Plotly
        html = fig.to_html(
            include_plotlyjs='cdn',
            config=plotly_config,
            full_html=True
        )

        self.web_view.setHtml(html)

    def save_plot(self, filepath):
        """
        Save plot to file (PNG or PDF).

        Args:
            filepath: Path where to save the plot

        Returns:
            True if successful, False otherwise
        """
        if self.current_fig is None:
            print("No plot to save")
            return False

        try:
            # Use kaleido for static export
            self.current_fig.write_image(
                filepath,
                width=config.PLOT_EXPORT_WIDTH,
                height=config.PLOT_EXPORT_HEIGHT,
                scale=config.PLOT_EXPORT_SCALE
            )
            return True
        except Exception as e:
            print(f"Error saving plot: {str(e)}")
            return False
