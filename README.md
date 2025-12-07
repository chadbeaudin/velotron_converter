# Velotron to Strava Converter

This utility monitors a directory for RacerMate Velotron `.pwx` files and automatically converts them to Strava-compatible `.tcx` and `.fit` files.

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
    
    **Default mode** (uses script's directory):
    ```bash
    python3 monitor_and_convert.py
    ```
    
    **Custom directory mode**:
    ```bash
    python3 monitor_and_convert.py /path/to/your/directory
    ```
    
    The script will create/use `original/`, `converted/`, `processed/`, and `failed/` subdirectories in the specified location.

2.  **Convert Files**:
    *   Drop your `.pwx` files into the `original` folder.
    *   The script will generate **two** output files in the `converted` folder:
        *   `YYYY-MM-DD_HH-MM-SS.tcx` (Strava-compatible TCX)
        *   `YYYY-MM-DD_HH-MM-SS.fit` (Strava-compatible FIT)
    *   Original file is moved to `processed`.
    *   **Progress**: You will see a real-time progress percentage in the terminal.
    *   **Summary**: After conversion, a summary of the ride (Distance, Duration, Elevation) is displayed.

## Directory Structure

*   `original/`: **Inbox**. Place new files here.
*   `converted/`: **Outbox**. Collect your converted `.tcx` and `.fit` files here.
*   `processed/`: **Archive**. Source files are stored here after conversion.
*   `failed/`: **Error**. Files that could not be converted are moved here.
*   `monitor_and_convert.py`: The main script to run.
*   `convert_pwx_to_tcx.py`: TCX conversion logic.
*   `convert_pwx_to_fit.py`: FIT conversion logic (requires `fit_tool`).

## Output Filenames

Converted files are named using the ride's timestamp from the PWX file (e.g., `2025-11-18_14-29-43.tcx` and `2025-11-18_14-29-43.fit`).

## Technical Details

To ensure Strava correctly displays all data (elevation, HR graphs, power, etc.):
1.  **Static GPS Coordinates**: Uses a fixed location (Boulder, CO) to enable Strava's time-series graphs while preserving barometric elevation data.
2.  **Device Metadata**: Mimics a "Garmin Edge 530" device to ensure Strava trusts the elevation and sensor data.
3.  **Timezone Handling**: Automatically adds local timezone info to timestamps so activities appear at the correct time in Strava.
4.  **Sport Type**: Marked as regular cycling (not indoor) to enable full graph display in Strava.
