"""
Main application window.
"""

import os
import glob
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QApplication,
                              QProgressBar, QSplitter, QMessageBox, QLabel)
from PyQt6.QtCore import Qt
from app.widgets.drop_zone import DropZoneWidget
from app.widgets.plot_widget import PlotWidget
from app.widgets.results_table import ResultsTableWidget
from app.widgets.status_log import StatusLogWidget
from core.data_processor import DataProcessor
from core.file_manager import FileManager
from core.metrics_registry import MetricsRegistry
import config


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, metrics_registry: MetricsRegistry):
        """
        Initialize main window.

        Args:
            metrics_registry: Registry containing all metrics
        """
        super().__init__()
        self.metrics_registry = metrics_registry
        self.data_processor = DataProcessor(metrics_registry)
        self.file_manager = None

        # Window settings
        self.setWindowTitle(f"{config.APP_NAME} v{config.APP_VERSION}")
        screen = QApplication.primaryScreen().availableGeometry()
        screen_height = screen.height()
        self.setGeometry(100, 0, screen_height, screen_height)
        self.setMaximumWidth(screen_height)

        # Setup UI
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """Setup user interface."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        layout = QVBoxLayout(central_widget)

        # Top row: Log (left) | Instructions (right)
        top_row = QSplitter(Qt.Orientation.Horizontal)

        self.status_log = StatusLogWidget()
        self.status_log.setMaximumHeight(100)

        instructions = QLabel()
        instructions.setText(
            "<b>How to use:</b><br>"
            "• <b>First time:</b> Drag and drop your reference CSV file. "
            "All other CSV files in the same folder will be automatically processed.<br>"
            "• <b>Adding more data:</b> If data.csv exists, drop new CSV files to append results.<br>"
            "• <b>After processing:</b> View the plot, results table, and find data.csv, data.xlsx, "
            "and plot files (PNG/PDF) saved in the same folder as your CSV files."
        )
        instructions.setWordWrap(True)
        instructions.setMaximumHeight(100)
        instructions.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                color: #ff00ff;
                border: 2px solid #ff00ff;
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
                font-size: 10pt;
            }
        """)

        top_row.addWidget(self.status_log)
        top_row.addWidget(instructions)
        top_row.setSizes([300, 700])
        layout.addWidget(top_row)

        # Drop zone (compact)
        self.drop_zone = DropZoneWidget()
        self.drop_zone.setFixedHeight(config.DROP_ZONE_MIN_HEIGHT)
        layout.addWidget(self.drop_zone)

        # Plot/Table splitter (plot maximized)
        self.plot_widget = PlotWidget()
        self.results_table = ResultsTableWidget()

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.plot_widget)
        splitter.addWidget(self.results_table)
        splitter.setSizes([600, 150])

        layout.addWidget(splitter, stretch=1)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def connect_signals(self):
        """Connect signals to slots."""
        self.drop_zone.files_dropped.connect(self.on_files_dropped)

    def on_files_dropped(self, filepaths):
        """
        Handle dropped files.

        Args:
            filepaths: List of dropped file paths
        """
        if not filepaths:
            return

        # Determine working directory from first file
        working_dir = os.path.dirname(filepaths[0])
        self.file_manager = FileManager(working_dir)

        # Load existing data.csv if it exists
        if self.file_manager.has_existing_results():
            self.data_processor.load_existing_data(working_dir)

        # Check directory is writable
        if not self.file_manager.validate_directory_writable():
            self.status_log.log(f"Error: Directory {working_dir} is not writable", 'ERROR')
            QMessageBox.critical(self, "Error", "Directory is not writable. Please check permissions.")
            return

        # Check for existing data.csv
        if not self.file_manager.has_existing_results():
            # First file is reference
            ref_file = filepaths[0]
            self.status_log.log(f"Setting reference: {os.path.basename(ref_file)}", 'INFO')

            try:
                self.data_processor.set_reference(ref_file)
                self.status_log.log("Reference file loaded successfully", 'SUCCESS')
            except Exception as e:
                self.status_log.log(f"Error loading reference: {str(e)}", 'ERROR')
                QMessageBox.critical(self, "Error", f"Failed to load reference file:\n{str(e)}")
                return

            # NEW: Find ALL CSV files in the folder (except reference and data.csv)
            import glob
            all_csv_files = glob.glob(os.path.join(working_dir, '*.csv'))
            files_to_process = [
                f for f in all_csv_files 
                if os.path.basename(f).lower() != 'data.csv'  # ← Only exclude data.csv, include ref_file
            ]

            if files_to_process:
                self.status_log.log(f"Found {len(files_to_process)} file(s) to process (including reference)", 'INFO')


        else:
            # Load existing reference
            ref_file = self.file_manager.load_existing_reference_full_path()
            if ref_file and os.path.exists(ref_file):
                self.status_log.log(f"Using existing reference: {os.path.basename(ref_file)}", 'INFO')
                try:
                    # Only load reference data, don't add to results again
                    from read_ferro_bare import read_ferro_bare_csv
                    self.data_processor.reference_metadata, self.data_processor.reference_data = read_ferro_bare_csv(ref_file)
                    self.data_processor.reference_filepath = ref_file
                except Exception as e:
                    self.status_log.log(f"Error loading existing reference: {str(e)}", 'ERROR')
                    QMessageBox.critical(self, "Error", f"Failed to load existing reference:\n{str(e)}")
                    return
            else:
                self.status_log.log("Warning: Could not find existing reference file", 'WARNING')

            # Process only the dropped files (don't auto-process all files)
            # Filter out reference, data.csv, and already-processed files

            # Check which files are already in the DataFrame
            existing_filenames = set()
            if self.data_processor.full_data_df is not None and 'Filename' in self.data_processor.full_data_df.columns:
                existing_filenames = set(self.data_processor.full_data_df['Filename'].tolist())

            files_to_process = [
                f for f in filepaths
                if f != ref_file
                and os.path.basename(f).lower() != 'data.csv'
                and os.path.basename(f) not in existing_filenames
            ]

            # Log skipped files
            skipped = [os.path.basename(f) for f in filepaths if os.path.basename(f) in existing_filenames]
            if skipped:
                self.status_log.log(f"Skipping already processed: {', '.join(skipped)}", 'INFO')

        # Process files if any
        if files_to_process:
            self.process_files(files_to_process)
        else:
            self.status_log.log("No files to process", 'INFO')
            # Still update display with reference
            self.update_display()

    def process_files(self, filepaths):
        """
        Process files and update UI.

        Args:
            filepaths: List of file paths to process
        """
        self.status_log.log(f"Processing {len(filepaths)} file(s)...", 'INFO')
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # Progress callback
        def progress_callback(current, total):
            progress = int(100 * current / total)
            self.progress_bar.setValue(progress)

        # Process files
        try:
            processed_data = self.data_processor.process_batch(filepaths, progress_callback)
            self.status_log.log(f"Successfully processed {len(processed_data)} file(s)", 'SUCCESS')

            # Update display
            self.update_display()

            # Save results
            self.save_results()

            # Auto-save plot
            plot_path = os.path.join(self.file_manager.working_directory, 'plot.png')
            if self.plot_widget.save_plot(plot_path):
                self.status_log.log(f"Plot saved to {os.path.basename(plot_path)}", 'SUCCESS')

            plot_path = os.path.join(self.file_manager.working_directory, 'plot.pdf')
            if self.plot_widget.save_plot(plot_path):
                self.status_log.log(f"Plot saved to {os.path.basename(plot_path)}", 'SUCCESS')


        except Exception as e:
            self.status_log.log(f"Error during processing: {str(e)}", 'ERROR')
            QMessageBox.critical(self, "Error", f"Failed to process files:\n{str(e)}")
        finally:
            self.progress_bar.setVisible(False)

    def update_display(self):
        """Update plot and results table."""
        # Update results table with full DataFrame
        results_df = self.data_processor.get_results_dataframe()
        self.results_table.update_results(results_df)

        # Update plot - need to load CSV files for plot data
        if self.data_processor.reference_data is not None and self.file_manager is not None and not results_df.empty:
            test_data = []
            test_rows = results_df[results_df['is_reference'] == False]

            for _, row in test_rows.iterrows():
                filename = row['Filename']
                filepath = os.path.join(self.file_manager.working_directory, filename)
                if os.path.exists(filepath):
                    try:
                        from read_ferro_bare import read_ferro_bare_csv
                        _, data = read_ferro_bare_csv(filepath)
                        test_data.append((data, filename))
                    except Exception as e:
                        self.status_log.log(f"Warning: Could not load {filename}: {str(e)}", 'WARNING')

            self.plot_widget.plot_data(self.data_processor.reference_data, test_data)

    def save_results(self):
        """Save results to CSV and Excel."""
        if not self.file_manager:
            return

        try:
            csv_path, excel_path = self.data_processor.save_results(self.file_manager.working_directory)
            self.status_log.log(f"Results saved to {os.path.basename(csv_path)}", 'SUCCESS')
            self.status_log.log(f"Results saved to {os.path.basename(excel_path)}", 'SUCCESS')
        except Exception as e:
            self.status_log.log(f"Error saving results: {str(e)}", 'ERROR')

