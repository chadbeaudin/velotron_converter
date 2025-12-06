import os
import time
import shutil
import sys
import datetime
from convert_pwx_to_tcx import convert_pwx_to_tcx

# Optional FIT support
try:
    from convert_pwx_to_fit import convert_pwx_to_fit
    FIT_SUPPORT_ENABLED = True
except ImportError:
    FIT_SUPPORT_ENABLED = False
    print("Warning: 'fit_tool' library not found. FIT conversion will be disabled.")
    print("To enable FIT support, run: pip install fit_tool")

# Configuration
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
    
    # Generate output filenames
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    tcx_filename = f"{timestamp}.tcx"
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
            fit_filename = f"{timestamp}.fit"
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
