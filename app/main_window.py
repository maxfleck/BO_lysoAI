"""
Main application window — thin wrapper around LysoAIWidget for standalone use.
"""

from PySide6.QtWidgets import QMainWindow, QApplication
from app.widgets.lysoai_widget import LysoAIWidget
from core.metrics_registry import MetricsRegistry
import config


class MainWindow(QMainWindow):
    """Standalone window wrapping LysoAIWidget."""

    def __init__(self, metrics_registry: MetricsRegistry):
        super().__init__()
        self.setWindowTitle(f"{config.APP_NAME} v{config.APP_VERSION}")

        screen = QApplication.primaryScreen().availableGeometry()
        screen_height = screen.height()
        self.setGeometry(100, 0, screen_height, screen_height)

        self.lysoai = LysoAIWidget(metrics_registry)
        self.setCentralWidget(self.lysoai)
