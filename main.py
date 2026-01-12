"""
Ferroci Analyzer - Electrochemical Data Analysis Tool

Main entry point for the application.
"""

import sys
from PyQt6.QtWidgets import QApplication
from app.main_window import MainWindow
from core.metrics_registry import MetricsRegistry
from core.metrics.curve_difference import CurveDifferenceMetric
from core.metrics.min_max_range import MinMaxDifferenceMetric
import config


def main():
    """Main application entry point."""
    # Initialize metrics registry
    registry = MetricsRegistry()

    # Register existing metrics
    registry.register(CurveDifferenceMetric())
    registry.register(MinMaxDifferenceMetric())

    # TO ADD NEW METRICS: Create your metric class and register it here
    # Example:
    # from core.metrics.your_metric import YourMetricName
    # registry.register(YourMetricName())

    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)
    app.setApplicationVersion(config.APP_VERSION)

    # Set application style
    app.setStyle('Fusion')

    # Create and show main window
    window = MainWindow(registry)
    window.show()

    # Run application
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
