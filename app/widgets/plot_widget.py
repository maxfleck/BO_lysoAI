"""
Interactive plot widget using Plotly for displaying electrochemical curves.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QFileDialog
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import pyqtSignal, QObject, pyqtSlot
import plotly.graph_objects as go
import plotly.io as pio
import numpy as np
import config


class PlotBridge(QObject):
    """Bridge for JavaScript to Python communication."""

    def __init__(self, plot_widget):
        super().__init__()
        self.plot_widget = plot_widget

    @pyqtSlot(float, float, float, float)
    def on_line_drawn(self, x0, y0, x1, y1):
        """Called from JavaScript when a line is drawn."""
        self.plot_widget.handle_line_drawn(x0, y0, x1, y1)


class PlotWidget(QWidget):
    """Widget for embedded interactive Plotly plotting."""

    save_error = pyqtSignal(str)  # Signal to report save errors
    intersection_calculated = pyqtSignal(int)  # Reports number of intersections found

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

        # Store curve data for intersection calculations
        self.curve_data = {}

        # Store drawn lines for intersection calculations
        self.drawn_lines = []  # List of (x0, y0, x1, y1) tuples

        # Setup QWebChannel for JS-Python communication
        self.channel = QWebChannel()
        self.bridge = PlotBridge(self)
        self.channel.registerObject('bridge', self.bridge)
        self.web_view.page().setWebChannel(self.channel)

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

        # Store curve data for intersection calculations
        self.curve_data = {'Reference': reference_data}
        for data, filename in test_data_list:
            if 'BARE' not in filename.upper() and 'REFERENCE' not in filename.upper():
                self.curve_data[filename] = data

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
            dragmode='drawline',  # Auto-select draw line tool
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

        # Inject JavaScript for QWebChannel communication
        webchannel_js = '''
<script src="qrc:///qtwebchannel/qwebchannel.js"></script>
<script>
var bridge = null;
new QWebChannel(qt.webChannelTransport, function(channel) {
    bridge = channel.objects.bridge;
});

// Track shapes to detect new ones
var previousShapeCount = 0;

document.addEventListener('DOMContentLoaded', function() {
    var plotDiv = document.getElementsByClassName('plotly-graph-div')[0];
    if (plotDiv) {
        plotDiv.on('plotly_relayout', function(data) {
            if (bridge && plotDiv.layout && plotDiv.layout.shapes) {
                var shapes = plotDiv.layout.shapes;
                if (shapes.length > previousShapeCount) {
                    // New shape added
                    var last = shapes[shapes.length - 1];
                    if (last && last.type === 'line') {
                        bridge.on_line_drawn(last.x0, last.y0, last.x1, last.y1);
                    }
                }
                previousShapeCount = shapes.length;
            }
        });
    }
});
</script>
'''
        # Insert webchannel script before closing body tag
        html = html.replace('</body>', webchannel_js + '</body>')

        self.web_view.setHtml(html)

    def handle_line_drawn(self, x0, y0, x1, y1):
        """Store line coordinates when drawn."""
        self.drawn_lines.append((x0, y0, x1, y1))

    def calculate_all_intersections(self):
        """Calculate intersections for all drawn lines."""
        if not self.current_fig or not self.curve_data or not self.drawn_lines:
            self.intersection_calculated.emit(0)
            return

        count = 0
        for x0, y0, x1, y1 in self.drawn_lines:
            # Add the line itself in grey
            self.current_fig.add_trace(go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode='lines',
                line=dict(color='grey', width=2),
                showlegend=False,
                hoverinfo='skip'
            ))

            # Add intersection markers
            intersections = self._find_intersections(x0, y0, x1, y1)
            for name, x, y in intersections:
                self.current_fig.add_trace(go.Scatter(
                    x=[x],
                    y=[y],
                    mode='markers',
                    marker=dict(size=14, color='yellow', symbol='x',
                               line=dict(width=2, color='black')),
                    name='Intersection',
                    hovertemplate=f'<b>{name}</b><br>Potential: {x:.4f} V<br>Current: {y:.2e} A<extra></extra>',
                    showlegend=False
                ))
                count += 1

        self._render_figure(self.current_fig)
        self.intersection_calculated.emit(count)

    def _find_intersections(self, x0, y0, x1, y1):
        """
        Find where the drawn line intersects with all curves.

        Args:
            x0, y0: Start point of the line
            x1, y1: End point of the line

        Returns:
            List of tuples (curve_name, x, y) for each intersection
        """
        intersections = []

        for name, data in self.curve_data.items():
            x_vals = data[config.POTENTIAL_COLUMN].values
            y_vals = data[config.CURRENT_COLUMN].values

            # Check each segment of the curve
            for i in range(len(x_vals) - 1):
                pt = self._line_segment_intersection(
                    x0, y0, x1, y1,
                    x_vals[i], y_vals[i], x_vals[i + 1], y_vals[i + 1]
                )
                if pt is not None:
                    intersections.append((name, pt[0], pt[1]))

        return intersections

    def _line_segment_intersection(self, x1, y1, x2, y2, x3, y3, x4, y4):
        """
        Find intersection point between two line segments.

        Line 1: (x1, y1) to (x2, y2)
        Line 2: (x3, y3) to (x4, y4)

        Returns:
            (x, y) tuple if segments intersect, None otherwise
        """
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

        if abs(denom) < 1e-10:
            # Lines are parallel
            return None

        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

        # Check if intersection is within both segments
        if 0 <= t <= 1 and 0 <= u <= 1:
            x = x1 + t * (x2 - x1)
            y = y1 + t * (y2 - y1)
            return (x, y)

        return None

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

