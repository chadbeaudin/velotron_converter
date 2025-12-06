# Velotron to Strava Converter

This utility monitors a directory for RacerMate Velotron `.pwx` files and automatically converts them to Strava-compatible `.tcx` files.

## Setup

### Prerequisites
- Python 3.x
- `pip install fit_tool` (Optional, required for `.fit` file generation)

1.  Ensure you have Python 3 installed.
2.  Install dependencies:
    ```bash
    pip install fit_tool
    ```

## Usage

1.  **Start the Monitor**:
    Open your terminal and run:
    ```bash
    python3 monitor_and_convert.py
    ```

2.  **Convert Files**:
    *   Drop your `.pwx` files into the `original` folder.
    *   The script will generate **two** output files in the `converted` folder:
        *   `YYYY-MM-DD_HH-MM-SS.tcx` (Strava-compatible TCX)
        *   `YYYY-MM-DD_HH-MM-SS.fit` (Strava-compatible FIT)
    *   Original file is moved to `processed`.
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

Converted files are named using the ride's timestamp from the PWX file (e.g., `2025-11-18_14-29-43.tcx` and `2025-11-18_14-29-43.fit`).

## Technical Details

To ensure Strava correctly reads elevation data from indoor rides:
1.  **No Position Data**: The TCX file intentionally omits GPS `Position` tags. If present (even as 0,0), Strava overwrites device elevation with map elevation (sea level).
2.  **Device Spoofing**: The converter adds metadata mimicking a "Garmin TCX with Barometer". This encourages Strava to trust the elevation data in the file.
