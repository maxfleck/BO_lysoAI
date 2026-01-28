"""
Interactive plot widget using Plotly for displaying electrochemical curves.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QFileDialog
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtCore import pyqtSignal
import plotly.graph_objects as go
import plotly.io as pio
import config


class PlotWidget(QWidget):
    """Widget for embedded interactive Plotly plotting."""

    save_error = pyqtSignal(str)  # Signal to report save errors

    def __init__(self):
        """Initialize plot widget."""
        super().__init__()

        # Create web view for Plotly HTML
        self.web_view = QWebEngineView()
        self.web_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Enable downloads from Plotly toolbar
        profile = QWebEngineProfile.defaultProfile()
        profile.downloadRequested.connect(self._handle_download)

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

        # Find global min/max for reference
        ref_min_idx = reference_data[config.CURRENT_COLUMN].idxmin()
        ref_max_idx = reference_data[config.CURRENT_COLUMN].idxmax()

        # Add min marker
        fig.add_trace(go.Scatter(
            x=[reference_data.loc[ref_min_idx, config.POTENTIAL_COLUMN]],
            y=[reference_data.loc[ref_min_idx, config.CURRENT_COLUMN]],
            mode='markers',
            marker=dict(size=12, color='limegreen', symbol='triangle-down'),
            name='Reference Min',
            hovertemplate='<b>Reference Min</b><br>Potential: %{x:.4f} V<br>Current: %{y:.2e} A<extra></extra>',
            showlegend=False
        ))

        # Add max marker
        fig.add_trace(go.Scatter(
            x=[reference_data.loc[ref_max_idx, config.POTENTIAL_COLUMN]],
            y=[reference_data.loc[ref_max_idx, config.CURRENT_COLUMN]],
            mode='markers',
            marker=dict(size=12, color='limegreen', symbol='triangle-up'),
            name='Reference Max',
            hovertemplate='<b>Reference Max</b><br>Potential: %{x:.4f} V<br>Current: %{y:.2e} A<extra></extra>',
            showlegend=False
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

                # Find global min/max for this test curve
                test_min_idx = data[config.CURRENT_COLUMN].idxmin()
                test_max_idx = data[config.CURRENT_COLUMN].idxmax()

                # Add min marker (triangle-down)
                fig.add_trace(go.Scatter(
                    x=[data.loc[test_min_idx, config.POTENTIAL_COLUMN]],
                    y=[data.loc[test_min_idx, config.CURRENT_COLUMN]],
                    mode='markers',
                    # marker=dict(size=12, color=config.REFERENCE_LINE_COLOR, symbol='triangle-down'),
                    marker=dict(size=12, color='limegreen', symbol='triangle-down'),
                    name=f'{filename} Min',
                    hovertemplate=f'<b>{filename} Min</b><br>Potential: %{{x:.4f}} V<br>Current: %{{y:.2e}} A<extra></extra>',
                    showlegend=False
                ))

                # Add max marker (triangle-up)
                fig.add_trace(go.Scatter(
                    x=[data.loc[test_max_idx, config.POTENTIAL_COLUMN]],
                    y=[data.loc[test_max_idx, config.CURRENT_COLUMN]],
                    mode='markers',
                    # marker=dict(size=12, color=config.REFERENCE_LINE_COLOR, symbol='triangle-up'),
                    marker=dict(size=12, color='limegreen', symbol='triangle-up'),
                    name=f'{filename} Max',
                    hovertemplate=f'<b>{filename} Max</b><br>Potential: %{{x:.4f}} V<br>Current: %{{y:.2e}} A<extra></extra>',
                    showlegend=False
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
            newshape=dict(
                line=dict(color='red', width=2),
                #layer='below',  # Draw shapes behind traces
            )
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
            'editable': False,  # Disabled to allow eraseshape to work
            'displayModeBar': True,
            'modeBarButtonsToAdd': ['drawline', 'eraseshape'],
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

    def _handle_download(self, download):
        """Handle download requests from Plotly toolbar with file dialog."""
        suggested_name = download.downloadFileName() or "plot.png"
        # Remove extension to allow user to pick format
        base_name = suggested_name.rsplit('.', 1)[0]

        filepath, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save Plot",
            base_name,
            "PNG Files (*.png);;PDF Files (*.pdf);;All Files (*)"
        )

        if filepath:
            # Add extension based on selected filter if not present
            if "png" in selected_filter.lower() and not filepath.lower().endswith('.png'):
                filepath += '.png'
            elif "pdf" in selected_filter.lower() and not filepath.lower().endswith('.pdf'):
                filepath += '.pdf'
            elif not filepath.lower().endswith(('.png', '.pdf')):
                filepath += '.png'  # Default to PNG

            download.setDownloadFileName(filepath.split('/')[-1])
            download.setDownloadDirectory(filepath.rsplit('/', 1)[0])
            download.accept()
        else:
            download.cancel()

    def save_plot(self, filepath):
        """
        Save plot to file (PNG or PDF).

        Args:
            filepath: Path where to save the plot

        Returns:
            True if successful, False otherwise
        """
        if self.current_fig is None:
            self.save_error.emit("No plot to save")
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
            self.save_error.emit(f"Error saving plot: {str(e)}")
            return False

