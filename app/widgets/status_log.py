"""
Status log widget for displaying messages and logs.
"""

from PyQt6.QtWidgets import QTextEdit
from datetime import datetime
import config


class StatusLogWidget(QTextEdit):
    """Widget for displaying status messages and logs."""

    def __init__(self):
        """Initialize status log widget."""
        super().__init__()

        # Settings
        self.setReadOnly(True)
        self.setMaximumHeight(config.STATUS_LOG_HEIGHT)

        # Styling
        self.setStyleSheet("""
            QTextEdit {
                background-color: #f9f9f9;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                font-family: 'Courier New', monospace;
                font-size: 10pt;
            }
        """)

        # Welcome message
        self.log("Ferroci Analyzer started. Drop CSV files to begin analysis.", 'INFO')

    def log(self, message: str, level: str = 'INFO'):
        """
        Add a log message with timestamp and color coding.

        Args:
            message: Message to log
            level: Log level (INFO, ERROR, SUCCESS, WARNING)
        """
        timestamp = datetime.now().strftime('%H:%M:%S')

        # Color mapping
        colors = {
            'INFO': config.COLOR_INFO,
            'ERROR': config.COLOR_ERROR,
            'SUCCESS': config.COLOR_SUCCESS,
            'WARNING': config.COLOR_WARNING
        }
        color = colors.get(level, config.COLOR_INFO)

        # Format message
        formatted_message = f'<span style="color:{color}"><b>[{timestamp}]</b> {message}</span>'

        # Append to log
        self.append(formatted_message)

        # Auto-scroll to bottom
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def clear_log(self):
        """Clear all log messages."""
        self.clear()
