"""
LysoAI analysis widget — embeddable as a standalone tab or wrapped in MainWindow.
"""

import os
import glob
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QProgressBar, QSplitter, QMessageBox, QLabel)
from PySide6.QtCore import Qt
from app.widgets.drop_zone import DropZoneWidget
from app.widgets.plot_widget import PlotWidget
from app.widgets.results_table import ResultsTableWidget
from app.widgets.status_log import StatusLogWidget
from core.data_processor import DataProcessor
from core.file_manager import FileManager
from core.metrics_registry import MetricsRegistry
import config


class LysoAIWidget(QWidget):
    """Self-contained LysoAI analysis widget."""

    def __init__(self, metrics_registry: MetricsRegistry):
        super().__init__()
        self.metrics_registry = metrics_registry
        self.data_processor = DataProcessor(metrics_registry)
        self.file_manager = None

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

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

        # Drop zone
        self.drop_zone = DropZoneWidget()
        self.drop_zone.setFixedHeight(config.DROP_ZONE_MIN_HEIGHT)
        layout.addWidget(self.drop_zone)

        # Plot / Table splitter
        self.plot_widget = PlotWidget()
        self.results_table = ResultsTableWidget()

        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.addWidget(self.results_table)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.plot_widget)
        splitter.addWidget(bottom_widget)
        splitter.setSizes([600, 150])
        layout.addWidget(splitter, stretch=1)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def _connect_signals(self):
        self.drop_zone.files_dropped.connect(self.on_files_dropped)
        self.plot_widget.save_error.connect(
            lambda msg: self.status_log.log(msg, 'ERROR')
        )
        self.plot_widget.intersection_calculated.connect(self._on_intersections_calculated)

    # ------------------------------------------------------------------
    # File handling
    # ------------------------------------------------------------------

    def on_files_dropped(self, filepaths):
        if not filepaths:
            return

        working_dir = os.path.dirname(filepaths[0])
        self.file_manager = FileManager(working_dir)

        if self.file_manager.has_existing_results():
            self.data_processor.load_existing_data(working_dir)

        if not self.file_manager.validate_directory_writable():
            self.status_log.log(f"Error: Directory {working_dir} is not writable", 'ERROR')
            QMessageBox.critical(self, "Error", "Directory is not writable. Please check permissions.")
            return

        if not self.file_manager.has_existing_results():
            ref_file = filepaths[0]
            self.status_log.log(f"Setting reference: {os.path.basename(ref_file)}", 'INFO')

            try:
                self.data_processor.set_reference(ref_file)
                self.status_log.log("Reference file loaded successfully", 'SUCCESS')
            except Exception as e:
                self.status_log.log(f"Error loading reference: {str(e)}", 'ERROR')
                QMessageBox.critical(self, "Error", f"Failed to load reference file:\n{str(e)}")
                return

            all_csv_files = glob.glob(os.path.join(working_dir, '*.csv'))
            files_to_process = [
                f for f in all_csv_files
                if os.path.basename(f).lower() != 'data.csv'
            ]

            if files_to_process:
                self.status_log.log(
                    f"Found {len(files_to_process)} file(s) to process (including reference)", 'INFO')

        else:
            ref_file = self.file_manager.load_existing_reference_full_path()
            if ref_file and os.path.exists(ref_file):
                self.status_log.log(f"Using existing reference: {os.path.basename(ref_file)}", 'INFO')
                try:
                    self.data_processor.set_reference(ref_file)
                except Exception as e:
                    self.status_log.log(f"Error loading existing reference: {str(e)}", 'ERROR')
                    QMessageBox.critical(self, "Error", f"Failed to load existing reference:\n{str(e)}")
                    return
            else:
                self.status_log.log("Warning: Could not find existing reference file", 'WARNING')

            files_to_process = [
                f for f in filepaths
                if f != ref_file and os.path.basename(f).lower() != 'data.csv'
            ]

            if self.data_processor.full_data_df is not None and files_to_process:
                reprocess_names = {os.path.basename(f) for f in files_to_process}
                df = self.data_processor.full_data_df
                self.data_processor.full_data_df = (
                    df[~df['Filename'].isin(reprocess_names)].reset_index(drop=True)
                )

        if files_to_process:
            self.process_files(files_to_process)
        else:
            self.status_log.log("No files to process", 'INFO')
            self.update_display()

    def process_files(self, filepaths):
        self.status_log.log(f"Processing {len(filepaths)} file(s)...", 'INFO')
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        def progress_callback(current, total):
            self.progress_bar.setValue(int(100 * current / total))

        try:
            processed_data = self.data_processor.process_batch(filepaths, progress_callback)
            self.status_log.log(f"Successfully processed {len(processed_data)} file(s)", 'SUCCESS')

            self.update_display()
            self.save_results()

            for ext in ('png', 'pdf'):
                plot_path = os.path.join(self.file_manager.working_directory, f'plot.{ext}')
                if self.plot_widget.save_plot(plot_path):
                    self.status_log.log(f"Plot saved to plot.{ext}", 'SUCCESS')

        except Exception as e:
            self.status_log.log(f"Error during processing: {str(e)}", 'ERROR')
            QMessageBox.critical(self, "Error", f"Failed to process files:\n{str(e)}")
        finally:
            self.progress_bar.setVisible(False)

    def update_display(self):
        results_df = self.data_processor.get_results_dataframe()

        if not results_df.empty:
            metric_names = self.metrics_registry.get_metric_names()
            display_columns = ['Filename', 'is_reference'] + metric_names
            display_columns = [col for col in display_columns if col in results_df.columns]
            display_df = results_df[display_columns]
        else:
            display_df = results_df

        self.results_table.update_results(display_df)

        if (self.data_processor.reference_data is not None
                and self.file_manager is not None
                and not results_df.empty):

            test_data = []
            test_rows = results_df[results_df['is_reference'] == False]

            for _, row in test_rows.iterrows():
                filename = row['Filename']
                filepath = os.path.join(self.file_manager.working_directory, filename)
                if os.path.exists(filepath):
                    try:
                        from read_ferro_bare import read_ferro_bare_csv
                        _, raw = read_ferro_bare_csv(filepath)
                        data = self.data_processor._scale_current(
                            raw, self.data_processor._current_scale, self.data_processor._current_unit)
                        test_data.append((data, filename))
                    except Exception as e:
                        self.status_log.log(f"Warning: Could not load {filename}: {str(e)}", 'WARNING')

            all_traces = []
            for data, filename in test_data:
                if filename not in self.data_processor.all_plot_traces:
                    self.data_processor.all_plot_traces[filename] = \
                        self.metrics_registry.collect_plot_data(data, self.data_processor.reference_data)
                for trace in self.data_processor.all_plot_traces[filename]:
                    trace.update(legendgroup=filename)
                all_traces.extend(self.data_processor.all_plot_traces[filename])

            ref_filename = os.path.basename(self.data_processor.reference_filepath)
            if ref_filename not in self.data_processor.all_plot_traces:
                self.data_processor.all_plot_traces[ref_filename] = \
                    self.metrics_registry.collect_plot_data(
                        self.data_processor.reference_data, self.data_processor.reference_data)
            for trace in self.data_processor.all_plot_traces[ref_filename]:
                trace.update(legendgroup='Reference')
            all_traces.extend(self.data_processor.all_plot_traces[ref_filename])

            self.plot_widget.plot_data(self.data_processor.reference_data, test_data, extra_traces=all_traces)

    def save_results(self):
        if not self.file_manager:
            return
        try:
            csv_path, excel_path = self.data_processor.save_results(self.file_manager.working_directory)
            self.status_log.log(f"Results saved to {os.path.basename(csv_path)}", 'SUCCESS')
            self.status_log.log(f"Results saved to {os.path.basename(excel_path)}", 'SUCCESS')
        except Exception as e:
            self.status_log.log(f"Error saving results: {str(e)}", 'ERROR')

    def _on_intersections_calculated(self, count):
        if count > 0:
            self.status_log.log(f"Found {count} intersection(s)", 'SUCCESS')
        else:
            self.status_log.log("No intersections found (no lines drawn?)", 'INFO')
