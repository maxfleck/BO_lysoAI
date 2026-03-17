"""
Data processor for orchestrating file processing and analysis.
"""

import os
import pandas as pd
from typing import Tuple, List, Callable, Optional
from read_ferro_bare import read_ferro_bare_csv
from core.metrics_registry import MetricsRegistry
import config


class DataProcessor:
    """Orchestrates file processing and metrics calculation."""

    def __init__(self, metrics_registry: MetricsRegistry):
        """
        Initialize data processor.

        Args:
            metrics_registry: Registry containing all metrics to calculate
        """
        self.metrics_registry = metrics_registry
        self.reference_data = None
        self.reference_metadata = None
        self.reference_filepath = None
        self.results = []
        self.all_processed_data = []  # Store for plotting
        self.full_data_df = None  # DataFrame containing all processed data
        self.all_plot_traces = {}  # filename -> list of Plotly traces from metrics
        self._current_scale = 1.0
        self._current_unit = 'A'


    @staticmethod
    def _detect_current_unit(raw_df) -> Tuple[float, str]:
        """Return (scale_factor, unit_label) for the best SI prefix based on reference data."""
        max_abs = raw_df["Current_A"].abs().max()
        for factor, label in [(1.0, 'A'), (1e3, 'mA'), (1e6, 'µA'), (1e9, 'nA'), (1e12, 'pA')]:
            if max_abs * factor >= 1.0:
                return factor, label
        return 1e12, 'pA'

    @staticmethod
    def _scale_current(df: pd.DataFrame, scale: float, unit: str) -> pd.DataFrame:
        """Return a copy of df with Current_A scaled and renamed to Current_{unit}."""
        new_col = f"Current_{unit}"
        df = df.copy()
        df[new_col] = df["Current_A"] * scale
        return df.drop(columns=["Current_A"])

    def set_reference(self, filepath: str) -> None:
        """Load and set reference file, auto-detecting current unit from data."""
        self.reference_metadata, raw_ref = read_ferro_bare_csv(filepath)
        self.reference_filepath = filepath
        self._current_scale, self._current_unit = self._detect_current_unit(raw_ref)
        config.CURRENT_COLUMN = f"Current_{self._current_unit}"
        config.CURRENT_UNIT = self._current_unit
        self.reference_data = self._scale_current(raw_ref, self._current_scale, self._current_unit)

    def load_existing_data(self, directory: str) -> None:
        """
        Load existing data.csv if it exists.

        Args:
            directory: Directory containing data.csv
        """
        csv_path = os.path.join(directory, 'data.csv')
        if os.path.exists(csv_path):
            try:
                self.full_data_df = pd.read_csv(csv_path)
                print(f"Loaded {len(self.full_data_df)} existing entries from data.csv")
            except Exception as e:
                print(f"Error loading existing data.csv: {str(e)}")
                self.full_data_df = None

    def process_file(self, filepath: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Process a single test file against reference.

        Args:
            filepath: Path to test CSV file

        Returns:
            Tuple of (metadata, data) DataFrames
        """
        # Read CSV and scale current to match reference unit
        metadata, raw_data = read_ferro_bare_csv(filepath)
        data = self._scale_current(raw_data, self._current_scale, self._current_unit)

        # Calculate all metrics
        metrics = self.metrics_registry.calculate_all(data, self.reference_data)

        # Merge metadata + metrics + flag
        result = {**metadata.iloc[0].to_dict(), **metrics, 'is_reference': False}
        self.results.append(result)

        return metadata, data

    def process_batch(
        self,
        filepaths: List[str],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Tuple[pd.DataFrame, str]]:
        """
        Process multiple files with progress updates.

        Args:
            filepaths: List of file paths to process
            progress_callback: Optional callback function(current, total)

        Returns:
            List of tuples (data_df, filename) for plotting
        """
        processed_data = []

        # Get reference filename for the ReferenceFilename column
        if not self.reference_filepath:
            raise ValueError("Reference file must be set before processing batch")
        reference_filename = os.path.basename(self.reference_filepath)

        for i, filepath in enumerate(filepaths):
            try:
                metadata, data = self.process_file(filepath)
                filename = os.path.basename(filepath)
                processed_data.append((data, filename))
                self.all_processed_data.append((data, filename))
                self.all_plot_traces[filename] = self.metrics_registry.collect_plot_data(data, self.reference_data)

                # Update the last result added by process_file()
                # Add ReferenceFilename column and set is_reference flag
                last_result = self.results[-1]
                last_result['ReferenceFilename'] = reference_filename

                # Set is_reference flag based on whether this is the reference file
                if filepath == self.reference_filepath:
                    last_result['is_reference'] = True
                else:
                    last_result['is_reference'] = False

                # Call progress callback if provided
                if progress_callback:
                    progress_callback(i + 1, len(filepaths))

            except Exception as e:
                print(f"Error processing {filepath}: {str(e)}")
                # Continue processing other files

        return processed_data

    def get_results_dataframe(self) -> pd.DataFrame:
        """
        Get full results DataFrame (includes both existing and new data).

        Returns:
            DataFrame with all results
        """
        # If we have existing data, append new results to it
        if self.full_data_df is not None:
            if self.results:
                new_df = pd.DataFrame(self.results)
                self.full_data_df = pd.concat([self.full_data_df, new_df], ignore_index=True)
                self.results = []  # Clear after merging
            return self.full_data_df
        else:
            # No existing data, just return current results
            return pd.DataFrame(self.results)

    def save_results(self, directory: str) -> Tuple[str, str]:
        """
        Save results as CSV and Excel in specified directory.

        Args:
            directory: Directory where to save results

        Returns:
            Tuple of (csv_path, excel_path)
        """
        df = self.get_results_dataframe()  # This now returns full DataFrame

        csv_path = os.path.join(directory, 'data.csv')
        excel_path = os.path.join(directory, 'data.xlsx')

        # Fill NaN values with empty strings to preserve manually added columns
        df = df.fillna('')

        # Save CSV (overwrites with complete data)
        df.to_csv(csv_path, index=False)

        # Save Excel
        try:
            df.to_excel(excel_path, index=False, engine='openpyxl')
        except Exception as e:
            print(f"Error saving Excel: {str(e)}")
            # Excel export is optional

        return csv_path, excel_path

    def clear_results(self) -> None:
        """Clear all results (useful for starting fresh)."""
        self.results = []
        self.all_processed_data = []
        self.all_plot_traces = {}

    def get_all_processed_data(self) -> List[Tuple[pd.DataFrame, str]]:
        """
        Get all processed data for plotting.

        Returns:
            List of tuples (data_df, filename)
        """
        return self.all_processed_data
