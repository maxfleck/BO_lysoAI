"""
Interactive plot widget using Plotly for displaying electrochemical curves.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QFileDialog
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtCore import Signal, QObject, Slot
import plotly.graph_objects as go
import plotly.io as pio
import numpy as np
import config


class PlotBridge(QObject):
    """Bridge for JavaScript to Python communication."""

    def __init__(self, plot_widget):
        super().__init__()
        self.plot_widget = plot_widget

    @Slot(float, float, float, float)
    def on_line_drawn(self, x0, y0, x1, y1):
        """Called from JavaScript when a line is drawn."""
        self.plot_widget.handle_line_drawn(x0, y0, x1, y1)

    @Slot()
    def calculate_intersections(self):
        """Called from JavaScript modebar button."""
        self.plot_widget.calculate_all_intersections()

    @Slot(str)
    def calculate_intersections_for(self, filenames_json):
        """Called from JavaScript with JSON list of currently visible legendgroups."""
        import json
        active = set(json.loads(filenames_json))
        self.plot_widget.calculate_all_intersections(active_legendgroups=active)


class PlotWidget(QWidget):
    """Widget for embedded interactive Plotly plotting."""

    save_error = Signal(str)  # Signal to report save errors
    intersection_calculated = Signal(int)  # Reports number of intersections found

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

        # Index where metric overlay traces start in the current figure (for modebar toggle)
        self._first_metric_idx = 0

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
            xaxis_title=f'Potential ({config.POTENTIAL_UNIT})',
            yaxis_title=f'Current ({config.CURRENT_UNIT})',
            template=config.PLOT_TEMPLATE,
            showlegend=True,
        )
        self._render_figure(fig)

    @staticmethod
    def _legend_label(filename, max_chars=20):
        return filename if len(filename) <= max_chars else filename[:max_chars - 1] + '…'

    def plot_data(self, reference_data, test_data_list, extra_traces=None):
        """
        Plot reference and test curves.

        Args:
            reference_data: DataFrame with Potential_V and Current_A columns
            test_data_list: List of tuples (data_df, filename)
            extra_traces: Optional list of Plotly trace objects from metrics
        """
        fig = go.Figure()

        # Store curve data for intersection calculations
        self.curve_data = {'Reference': reference_data}
        for data, filename in test_data_list:
            self.curve_data[filename] = data

        # Plot reference curve with thick magenta line
        fig.add_trace(go.Scatter(
            x=reference_data[config.POTENTIAL_COLUMN],
            y=reference_data[config.CURRENT_COLUMN],
            mode='lines',
            name='Reference',
            legendgroup='Reference',
            line=dict(
                color=config.REFERENCE_LINE_COLOR,
                width=config.REFERENCE_LINE_WIDTH
            ),
            hovertemplate=f'<b>Reference</b><br>Potential: %{{x:.4f}} {config.POTENTIAL_UNIT}<br>Current: %{{y:.2e}} {config.CURRENT_UNIT}<extra></extra>'
        ))

        # Plot test curves
        if test_data_list:
            # Use Plotly's default color sequence
            colors = pio.templates[config.PLOT_TEMPLATE].layout.colorway
            if not colors:
                colors = pio.templates['plotly'].layout.colorway

            for i, (data, filename) in enumerate(test_data_list):
                color = colors[i % len(colors)]

                fig.add_trace(go.Scatter(
                    x=data[config.POTENTIAL_COLUMN],
                    y=data[config.CURRENT_COLUMN],
                    mode='lines',
                    name=self._legend_label(filename),
                    legendgroup=filename,
                    line=dict(width=2.5),
                    opacity=config.TEST_LINE_ALPHA,
                    hovertemplate=f'<b>{filename}</b><br>Potential: %{{x:.4f}} {config.POTENTIAL_UNIT}<br>Current: %{{y:.2e}} {config.CURRENT_UNIT}<extra></extra>'
                ))

        # Update layout
        fig.update_layout(
            title=dict(
                text='Cyclic Voltammetry Curves',
                font=dict(size=16)
            ),
            xaxis_title=f'Potential ({config.POTENTIAL_UNIT})',
            yaxis_title=f'Current ({config.CURRENT_UNIT})',
            template=config.PLOT_TEMPLATE,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=1.02
            ),
            hovermode='closest',
            margin=dict(r=200),  # Extra margin for legend
            dragmode='drawline',  # Auto-select draw line tool
            newshape=dict(
                line=dict(color='red', width=2),
                #layer='below',  # Draw shapes behind traces
            )
        )

        # Add any extra traces from metrics, recording split point for the modebar toggle
        first_metric_idx = len(fig.data)
        for trace in (extra_traces or []):
            fig.add_trace(trace)
        self._first_metric_idx = first_metric_idx

        self._render_figure(fig)

    def _render_figure(self, fig):
        """
        Render Plotly figure to the web view.

        Args:
            fig: Plotly figure object
        """
        self.current_fig = fig

        # Minimal initial config — custom buttons are injected via JS after first render
        plotly_config = {
            'editable': True,
            'displayModeBar': True,
            'displaylogo': False,
        }

        # Generate HTML with embedded Plotly
        html = fig.to_html(
            include_plotlyjs='cdn',
            config=plotly_config,
            full_html=True
        )

        # Inject JavaScript for QWebChannel communication + custom modebar buttons
        first_metric_idx = self._first_metric_idx
        webchannel_js = f'''
<script src="qrc:///qtwebchannel/qwebchannel.js"></script>
<script>
var bridge = null;
new QWebChannel(qt.webChannelTransport, function(channel) {{
    bridge = channel.objects.bridge;
}});

// Index where metric traces start; main curve traces are 0..firstMetricIdx-1
var firstMetricIdx = {first_metric_idx};

// Custom modebar buttons — add more objects here to extend
var customModebarButtons = [
    {{
        name: 'toggle-metrics',
        title: 'Toggle metric overlays',
        icon: Plotly.Icons.drawrect,
        click: function(gd) {{
            var visibleGroups = new Set();
            for (var i = 0; i < firstMetricIdx; i++) {{
                var v = gd.data[i].visible;
                if (v !== false && v !== 'legendonly') visibleGroups.add(gd.data[i].legendgroup);
            }}
            var toToggle = [];
            for (var i = firstMetricIdx; i < gd.data.length; i++) {{
                if (visibleGroups.has(gd.data[i].legendgroup)) toToggle.push(i);
            }}
            if (!toToggle.length) return;
            var anyVisible = toToggle.some(function(i) {{
                var v = gd.data[i].visible;
                return v !== false && v !== 'legendonly';
            }});
            Plotly.restyle(gd, {{visible: anyVisible ? false : true}}, toToggle);
        }}
    }},
    {{
        name: 'calc-intersections',
        title: 'Calculate intersections',
        icon: Plotly.Icons.drawcircle,
        click: function(gd) {{
            if (!bridge) return;
            var visible = [];
            for (var i = 0; i < firstMetricIdx; i++) {{
                var v = gd.data[i].visible;
                if (v !== false && v !== 'legendonly') visible.push(gd.data[i].legendgroup);
            }}
            bridge.calculate_intersections_for(JSON.stringify(visible));
        }}
    }}
];

// Track shapes to detect new ones
var previousShapeCount = 0;

document.addEventListener('DOMContentLoaded', function() {{
    var plotDiv = document.getElementsByClassName('plotly-graph-div')[0];
    if (plotDiv) {{
        // Apply custom modebar config immediately (Plotly CDN is a blocking script,
        // so plotDiv.data and plotDiv.layout are already populated by DOMContentLoaded)
        Plotly.react(plotDiv, plotDiv.data, plotDiv.layout, {{
            editable: true,
            displayModeBar: true,
            displaylogo: false,
            modeBarButtonsToAdd: customModebarButtons.concat(['drawline', 'eraseshape']),
            modeBarButtonsToRemove: ['lasso2d', 'select2d'],
            toImageButtonOptions: {{
                format: 'png',
                height: {config.PLOT_EXPORT_HEIGHT},
                width: {config.PLOT_EXPORT_WIDTH},
                scale: {config.PLOT_EXPORT_SCALE}
            }}
        }});

        plotDiv.on('plotly_relayout', function(data) {{
            if (bridge && plotDiv.layout && plotDiv.layout.shapes) {{
                var shapes = plotDiv.layout.shapes;
                if (shapes.length > previousShapeCount) {{
                    var last = shapes[shapes.length - 1];
                    if (last && last.type === 'line') {{
                        bridge.on_line_drawn(last.x0, last.y0, last.x1, last.y1);
                    }}
                }}
                previousShapeCount = shapes.length;
            }}
        }});
    }}
}});
</script>
'''
        # Insert webchannel script before closing body tag
        html = html.replace('</body>', webchannel_js + '</body>')

        self.web_view.setHtml(html)

    def handle_line_drawn(self, x0, y0, x1, y1):
        """Store line coordinates when drawn."""
        self.drawn_lines.append((x0, y0, x1, y1))

    def calculate_all_intersections(self, mode='lines', active_legendgroups=None):
        """Calculate intersections for all drawn lines.

        Args:
            mode: 'lines' (default) finds intersections between drawn lines;
                  'curves' finds intersections between drawn lines and CV curves.
        """
        if not self.current_fig or not self.drawn_lines:
            self.intersection_calculated.emit(0)
            return

        if mode == 'lines':
            intersections = self._find_line_line_intersections()
        else:  # 'curves'
            if not self.curve_data:
                self.intersection_calculated.emit(0)
                return
            intersections = []
            for x0, y0, x1, y1 in self.drawn_lines:
                intersections.extend(self._find_intersections(x0, y0, x1, y1))

        # Render grey lines
        for x0, y0, x1, y1 in self.drawn_lines:
            self.current_fig.add_trace(go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode='lines',
                line=dict(color='grey', width=2),
                showlegend=False,
                hoverinfo='skip'
            ))

        # Render intersection markers
        for name, x, y in intersections:
            self.current_fig.add_trace(go.Scatter(
                x=[x],
                y=[y],
                mode='markers',
                marker=dict(size=14, color='yellow', symbol='x',
                           line=dict(width=2, color='black')),
                name='Intersection',
                hovertemplate=f'<b>{name}</b><br>Potential: {x:.4f} {config.POTENTIAL_UNIT}<br>Current: {y:.2e} {config.CURRENT_UNIT}<extra></extra>',
                showlegend=False
            ))

        # Restore visibility state: mark traces hidden by the user before re-render
        if active_legendgroups is not None:
            for trace in self.current_fig.data:
                lg = getattr(trace, 'legendgroup', None) or ''
                if lg and lg not in active_legendgroups:
                    trace.visible = 'legendonly'

        self._render_figure(self.current_fig)
        self.intersection_calculated.emit(len(intersections))

    def _find_line_line_intersections(self):
        """Find intersections between all pairs of drawn lines.

        Returns:
            List of tuples (label, x, y) for each intersection found.
        """
        results = []
        lines = self.drawn_lines
        for i in range(len(lines)):
            for j in range(i + 1, len(lines)):
                x0, y0, x1, y1 = lines[i]
                x2, y2, x3, y3 = lines[j]
                pt = self._line_segment_intersection(x0, y0, x1, y1, x2, y2, x3, y3)
                if pt is not None:
                    results.append((f'Line {i+1} × Line {j+1}', pt[0], pt[1]))
        return results

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

