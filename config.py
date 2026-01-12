"""
Configuration constants for the Ferroci Analyzer application.
"""

# Application metadata
APP_NAME = "Ferroci Analyzer"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Electrochemical Data Analysis Tool"

# File settings
DATA_OUTPUT_FILENAME = "data.csv"
EXCEL_OUTPUT_FILENAME = "data.xlsx"
SUPPORTED_EXTENSIONS = ['.csv']

# Plot settings
PLOT_DPI = 100
PLOT_FIGSIZE = (8, 6)
REFERENCE_LINE_WIDTH = 3
REFERENCE_LINE_COLOR = 'magenta'
TEST_LINE_ALPHA = 0.6
PLOT_GRID_ALPHA = 0.3

# UI settings
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
STATUS_LOG_HEIGHT = 150
DROP_ZONE_MIN_HEIGHT = 150

# Data column names
POTENTIAL_COLUMN = "Potential_V"
CURRENT_COLUMN = "Current_A"
REFERENCE_FLAG_COLUMN = "is_reference"
REFERENCE_FILENAME_COLUMN = "ReferenceFilename"
FILENAME_COLUMN = "Filename"

# Colors for UI
COLOR_INFO = 'black'
COLOR_ERROR = 'red'
COLOR_SUCCESS = 'green'
COLOR_WARNING = 'orange'

# Drop zone styling
DROP_ZONE_BORDER_COLOR = '#ff00ff'  # Magenta
DROP_ZONE_HOVER_COLOR = '#ff66ff'   # Lighter magenta for hover
DROP_ZONE_BG_COLOR = '#1a1a1a'      # Dark background
DROP_ZONE_HOVER_BG_COLOR = '#2a1a2a'  # Slightly lighter dark with magenta tint
