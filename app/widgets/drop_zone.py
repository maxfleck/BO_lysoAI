"""
Drop zone widget for drag-and-drop file interface.
"""

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import pyqtSignal, Qt
import config


class DropZoneWidget(QWidget):
    """Widget for drag-and-drop file upload."""

    files_dropped = pyqtSignal(list)

    def __init__(self):
        """Initialize drop zone widget."""
        super().__init__()
        self.setAcceptDrops(True)

        # Create layout
        layout = QVBoxLayout()
        self.label = QLabel("Drag & Drop CSV Files Here")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Style label
        font = self.label.font()
        font.setPointSize(14)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setStyleSheet("color: #ff00ff;")

        layout.addWidget(self.label)
        self.setLayout(layout)

        # Apply styling
        self.apply_default_style()

    def apply_default_style(self):
        """Apply default styling."""
        self.setStyleSheet(f"""
            QWidget {{
                border: 4px solid {config.DROP_ZONE_BORDER_COLOR};
                border-radius: 10px;
                background-color: {config.DROP_ZONE_BG_COLOR};
                min-height: {config.DROP_ZONE_MIN_HEIGHT}px;
            }}
        """)

    def apply_hover_style(self):
        """Apply hover styling."""
        self.setStyleSheet(f"""
            QWidget {{
                border: 4px solid {config.DROP_ZONE_HOVER_COLOR};
                border-radius: 10px;
                background-color: {config.DROP_ZONE_HOVER_BG_COLOR};
                min-height: {config.DROP_ZONE_MIN_HEIGHT}px;
            }}
        """)

    def dragEnterEvent(self, event):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.apply_hover_style()
            self.label.setText("Drop files to process")

    def dragLeaveEvent(self, event):
        """Handle drag leave event."""
        self.apply_default_style()
        self.label.setText("Drag & Drop CSV Files Here")

    def dropEvent(self, event):
        """Handle drop event."""
        files = []
        for url in event.mimeData().urls():
            filepath = url.toLocalFile()
            if filepath.endswith('.csv'):
                files.append(filepath)

        if files:
            self.files_dropped.emit(files)

        # Reset style and label
        self.apply_default_style()
        self.label.setText("Drag & Drop CSV Files Here")
