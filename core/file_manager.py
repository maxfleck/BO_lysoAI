"""
File manager for handling reference file tracking and data.csv management.
"""

import os
import pandas as pd
from typing import Optional


class FileManager:
    """Manages file operations and reference tracking."""

    def __init__(self, working_directory: str):
        """
        Initialize file manager.

        Args:
            working_directory: Directory where data.csv and files are located
        """
        self.working_directory = working_directory
        self.data_csv_path = os.path.join(working_directory, 'data.csv')
        self.excel_path = os.path.join(working_directory, 'data.xlsx')

    def has_existing_results(self) -> bool:
        """
        Check if data.csv exists in working directory.

        Returns:
            bool: True if data.csv exists, False otherwise
        """
        return os.path.exists(self.data_csv_path)

    def load_existing_reference(self) -> Optional[str]:
        """
        Extract reference filename from existing data.csv.

        Returns:
            str: Reference filename if found, None otherwise
        """
        if not self.has_existing_results():
            return None

        try:
            df = pd.read_csv(self.data_csv_path)
            ref_row = df[df['is_reference'] == True]
            if not ref_row.empty:
                return ref_row.iloc[0]['Filename']
        except Exception as e:
            print(f"Error loading reference from data.csv: {str(e)}")

        return None

    def load_existing_reference_full_path(self) -> Optional[str]:
        """
        Get full path to reference file from existing data.csv.

        Returns:
            str: Full path to reference file if found, None otherwise
        """
        filename = self.load_existing_reference()
        if filename:
            # Try to find file in working directory
            potential_path = os.path.join(self.working_directory, filename)
            if os.path.exists(potential_path):
                return potential_path

        return None

    def validate_directory_writable(self) -> bool:
        """
        Check if working directory is writable.

        Returns:
            bool: True if directory is writable, False otherwise
        """
        return os.access(self.working_directory, os.W_OK)

    def get_data_csv_path(self) -> str:
        """
        Get full path to data.csv.

        Returns:
            str: Full path to data.csv
        """
        return self.data_csv_path

    def get_excel_path(self) -> str:
        """
        Get full path to data.xlsx.

        Returns:
            str: Full path to data.xlsx
        """
        return self.excel_path
