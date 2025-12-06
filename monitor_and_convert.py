import os
import time
import shutil
import sys
import datetime
import argparse
from convert_pwx_to_tcx import convert_pwx_to_tcx

# Optional FIT support
try:
    from convert_pwx_to_fit import convert_pwx_to_fit
    FIT_SUPPORT_ENABLED = True
except ImportError:
    FIT_SUPPORT_ENABLED = False
    print("Warning: 'fit_tool' library not found. FIT conversion will be disabled.")
    print("To enable FIT support, run: pip install fit_tool")

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Monitor and convert PWX files to TCX/FIT formats')
parser.add_argument('directory', nargs='?', default=None, 
                    help='Base directory containing original/ folder (default: script location)')
args = parser.parse_args()

# Configuration
if args.directory:
    BASE_DIRECTORY = os.path.abspath(args.directory)
else:
    BASE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

ORIGINAL_DIR_NAME = "original"
CONVERTED_DIR_NAME = "converted"
PROCESSED_DIR_NAME = "processed"
FAILED_DIR_NAME = "failed"
POLL_INTERVAL = 2  # Seconds

def setup_directories():
    """Ensure necessary directories exist."""
    # We need to make sure the watch directory (original) exists, 
    # as well as output (converted) and archive (processed/failed)
    for dir_name in [ORIGINAL_DIR_NAME, CONVERTED_DIR_NAME, PROCESSED_DIR_NAME, FAILED_DIR_NAME]:
        path = os.path.join(BASE_DIRECTORY, dir_name)
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"Created directory: {path}")

def process_file(filename):
    """Process a single PWX file found in the original directory."""
    # Input is now inside 'original'
    input_path = os.path.join(BASE_DIRECTORY, ORIGINAL_DIR_NAME, filename)
    
    # Extract ride timestamp from PWX file for filename
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(input_path)
        root = tree.getroot()
        
        # Handle namespaced PWX
        if '}' in root.tag:
            ns_url = root.tag.split('}')[0].strip('{')
            ns = {'pwx': ns_url}
            workout = root.find('pwx:workout', ns)
            time_node = workout.find('pwx:time', ns) if workout is not None else None
        else:
            workout = root.find('workout')
            time_node = workout.find('time') if workout is not None else None
        
        if time_node is not None and time_node.text:
            # Parse timestamp: 2025-11-18T14:29:43 -> 2025-11-18_14-29-43
            ride_time_str = time_node.text.split('.')[0]  # Remove fractional seconds if present
            ride_time = datetime.datetime.fromisoformat(ride_time_str)
            base_name = ride_time.strftime("%Y-%m-%d_%H-%M-%S")
        else:
            # Fallback to original filename if parsing fails
            base_name = os.path.splitext(filename)[0]
    except Exception as e:
        # Fallback to original filename on any error
        print(f"  -> Warning: Could not parse ride time, using original filename: {e}")
        base_name = os.path.splitext(filename)[0]
    
    tcx_filename = f"{base_name}.tcx"
    tcx_path = os.path.join(BASE_DIRECTORY, CONVERTED_DIR_NAME, tcx_filename)
    
    print(f"\nFound file: {filename}")
    print(f"Starting processing: {filename}...")
    sys.stdout.flush()
    
    try:
        # 1. Convert to TCX
        convert_pwx_to_tcx(input_path, tcx_path)
        print(f"  -> Generated TCX: converted/{tcx_filename}")

        # 2. Convert to FIT (if enabled)
        if FIT_SUPPORT_ENABLED:
            fit_filename = f"{base_name}.fit"
            fit_path = os.path.join(BASE_DIRECTORY, CONVERTED_DIR_NAME, fit_filename)
            try:
                convert_pwx_to_fit(input_path, fit_path)
                print(f"  -> Generated FIT: converted/{fit_filename}")
            except Exception as e:
                print(f"  -> FIT Conversion Failed: {e}")
        else:
            print("  -> FIT conversion skipped (library missing)")
        
        # Move original file to 'processed'
        processed_dest = os.path.join(BASE_DIRECTORY, PROCESSED_DIR_NAME, filename)
        shutil.move(input_path, processed_dest)
        print(f"Completed processing: {filename}")
        print(f"  -> Original moved to processed/")
        sys.stdout.flush()
        
    except Exception as e:
        print(f"  -> FAILED: {e}")
        # Move failed file to 'failed'
        try:
            failed_dest = os.path.join(BASE_DIRECTORY, FAILED_DIR_NAME, filename)
            shutil.move(input_path, failed_dest)
            print(f"  -> Moved original to failed/")
        except Exception as move_err:
            print(f"  -> CRITICAL: Could not move failed file: {move_err}")

def monitor_directory():
    """Main monitoring loop."""
    watch_dir = os.path.join(BASE_DIRECTORY, ORIGINAL_DIR_NAME)
    
    print(f"Monitoring directory: {watch_dir}")
    print(f"Current Working Directory: {os.getcwd()}")
    print(f"Place PWX files in '{ORIGINAL_DIR_NAME}' folder to convert them.")
    print(f"Press Ctrl+C to stop.")
    sys.stdout.flush()
    
    setup_directories()
    
    try:
        while True:
            # List files in the watch directory
            for filename in os.listdir(watch_dir):
                if filename.lower().endswith(".pwx"):
                    # Check if it's a file (not a dir)
                    if os.path.isfile(os.path.join(watch_dir, filename)):
                        process_file(filename)
            
            time.sleep(POLL_INTERVAL)
            
    except KeyboardInterrupt:
        print("\nStopping monitor.")

if __name__ == "__main__":
    # Allow overriding base directory via argument
    if len(sys.argv) > 1:
        BASE_DIRECTORY = sys.argv[1]
        
    monitor_directory()
