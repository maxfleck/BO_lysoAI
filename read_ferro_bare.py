import pandas as pd
import numpy as np
from typing import Tuple, Dict


def read_ferro_bare_csv(filepath: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Read a FERRO BARE.csv file containing cyclic voltammetry data.

    This function extracts metadata from the header section and the
    potential-current relationship from the data section.

    Parameters
    ----------
    filepath : str
        Path to the FERRO BARE.csv file

    Returns
    -------
    metadata_df : pd.DataFrame
        Single-row DataFrame containing all metadata fields that can be merged with other files.
        Columns include experimental parameters like scan rate, initial/high/low potential, etc.
    data_df : pd.DataFrame
        DataFrame with columns ['Potential_V', 'Current_A'] containing the voltage-current measurements

    Examples
    --------
    >>> metadata, data = read_ferro_bare_csv('FERRO BARE.csv')
    >>> print(metadata.columns)
    >>> print(data.head())
    """

    # Initialize metadata dictionary
    metadata = {}

    # Read the file line by line
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Parse metadata from header (lines before "Potential/V, Current/A")
    data_start_idx = None
    for idx, line in enumerate(lines):
        line = line.strip()

        # Replace commas to avoid csv parsing issues
        line = line.replace(',', '.')

        # Check if we've reached the data section
        if line.startswith('Potential/V'):
            data_start_idx = idx + 1  # Data starts after the header line
            break

        # Skip empty lines and section markers
        if not line or line in ['Results:', 'Channel 1:', 'Header:', 'Note:'] or line.startswith('Segment'):
            continue

        # Parse key-value pairs
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()

            # Try to convert to numeric if possible
            try:
                # Handle scientific notation
                if 'e' in value.lower():
                    value = float(value)
                elif '.' in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                pass  # Keep as string

            metadata[key] = value
        elif ':' in line and '=' not in line and '   ' not in line:
            # Handle lines like "Sept. 12, 2025   15:54:51" or "File: ..."
            parts = line.split(':', 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()

                # Create descriptive key names
                if key == 'File':
                    metadata['File_Path'] = value
                elif 'Cyclic Voltammetry' not in line:
                    # For date/time lines or other metadata
                    if not key:  # Handle cases like the timestamp
                        continue
                    metadata[key] = value
        else:
            # Handle first line (date and time)
            if idx == 0:
                metadata['DateTime'] = line
            # Handle technique line
            elif 'Cyclic Voltammetry' in line:
                metadata['Technique'] = line
            # Handle other single-value lines
            elif idx < 10 and line:  # Only for header section
                # Try to extract useful info
                if 'Data Source' in line:
                    metadata['Data_Source'] = line.split(':', 1)[1].strip()
                elif 'Instrument Model' in line:
                    metadata['Instrument_Model'] = line.split(':', 1)[1].strip()

    # Create single-row DataFrame from metadata
    metadata_df = pd.DataFrame([metadata])

    # Add the filename as a column for tracking
    import os
    metadata_df['Filename'] = os.path.basename(filepath)

    # Parse the data section
    if data_start_idx is None:
        raise ValueError("Could not find 'Potential/V, Current/A' header in file")

    # Read data lines and parse them
    potentials = []
    currents = []

    for line in lines[data_start_idx:]:
        line = line.strip()
        if not line:
            continue

        try:
            # Split by comma
            parts = line.split(',')
            if len(parts) == 2:
                potential = float(parts[0].strip())
                current = float(parts[1].strip())
                potentials.append(potential)
                currents.append(current)
        except ValueError:
            # Skip lines that can't be parsed as numbers
            continue

    # Create DataFrame for potential-current data
    data_df = pd.DataFrame({
        'Potential_V': potentials,
        'Current_A': currents
    })

    return metadata_df, data_df


if __name__ == "__main__":
    # Example usage
    filepath = "/home/max/Desktop/BO_lysoAI/FERRO BARE.csv"

    metadata, data = read_ferro_bare_csv(filepath)

    print("=" * 60)
    print("METADATA")
    print("=" * 60)
    print(metadata.T)  # Transpose for better readability
    print("\n")

    print("=" * 60)
    print("DATA (first and last 10 rows)")
    print("=" * 60)
    print("First 10 rows:")
    print(data.head(10))
    print("\n")
    print("Last 10 rows:")
    print(data.tail(10))
    print("\n")
    print(f"Total data points: {len(data)}")
