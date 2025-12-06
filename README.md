# Velotron to Strava Converter

This utility monitors a directory for RacerMate Velotron `.pwx` files and automatically converts them to Strava-compatible `.tcx` files.

## Setup

### Prerequisites
- Python 3.x
- `pip install fit_tool` installed.

1.  Ensure you have Python 3 installed.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    # (or just ensure standard library modules are available: xml, datetime, os, shutil, sys)
    # The current script uses only standard libraries.
    ```

## Usage

1.  **Start the Monitor**:
    Open your terminal and run:
    ```bash
    python3 monitor_and_convert.py
    ```

2.  **Convert Files**:
    *   Drop your `.pwx` files into the `original` folder.
    *   The script will detect the file, convert it, and place the result in the `converted` folder.
    *   The original file is moved to `processed`.
    *   **Progress**: You will see a real-time progress percentage in the terminal.
    *   **Summary**: After conversion, a summary of the ride (Distance, Duration, Elevation) is displayed.

## Directory Structure

*   `original/`: **Inbox**. Place new files here.
*   `converted/`: **Outbox**. Collect your converted `.tcx` files here.
*   `processed/`: **Archive**. Source files are stored here after conversion.
*   `failed/`: **Error**. Files that could not be converted are moved here.
*   `monitor_and_convert.py`: The main script to run.
*   `convert_pwx_to_tcx.py`: The underlying conversion logic.

## Output Filenames

Converted files are named using the timestamp of conversion (e.g., `2025-12-05_17-00-00.tcx`) to ensure uniqueness.
