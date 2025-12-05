import os
import time
import shutil
import sys
from convert_pwx_to_tcx import convert_pwx_to_tcx

# Configuration
WATCH_DIRECTORY = os.getcwd()  # Monitor current directory by default
ORIGINAL_DIR_NAME = "original"
CONVERTED_DIR_NAME = "converted"
FAILED_DIR_NAME = "failed"
POLL_INTERVAL = 2  # Seconds

def setup_directories():
    """Ensure necessary directories exist."""
    for dir_name in [ORIGINAL_DIR_NAME, CONVERTED_DIR_NAME, FAILED_DIR_NAME]:
        path = os.path.join(WATCH_DIRECTORY, dir_name)
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"Created directory: {path}")

def process_file(filename):
    """Process a single PWX file."""
    input_path = os.path.join(WATCH_DIRECTORY, filename)
    
    # Generate output filename
    base_name = os.path.splitext(filename)[0]
    output_filename = f"{base_name}.tcx"
    output_path = os.path.join(WATCH_DIRECTORY, CONVERTED_DIR_NAME, output_filename)
    
    print(f"Processing: {filename}...")
    
    try:
        # Convert
        convert_pwx_to_tcx(input_path, output_path)
        
        # Move original file
        original_dest = os.path.join(WATCH_DIRECTORY, ORIGINAL_DIR_NAME, filename)
        shutil.move(input_path, original_dest)
        print(f"  -> Converted to {output_filename}")
        print(f"  -> Moved original to {ORIGINAL_DIR_NAME}/")
        
    except Exception as e:
        print(f"  -> FAILED: {e}")
        # Move to failed directory to avoid infinite loops
        failed_dest = os.path.join(WATCH_DIRECTORY, FAILED_DIR_NAME, filename)
        try:
            shutil.move(input_path, failed_dest)
            print(f"  -> Moved to {FAILED_DIR_NAME}/")
        except Exception as move_error:
            print(f"  -> CRITICAL: Could not move failed file: {move_error}")

def monitor_directory():
    """Main monitoring loop."""
    print(f"Monitoring directory: {WATCH_DIRECTORY}")
    print(f"Press Ctrl+C to stop.")
    
    setup_directories()
    
    try:
        while True:
            # List files in directory
            for filename in os.listdir(WATCH_DIRECTORY):
                if filename.lower().endswith(".pwx"):
                    # Check if it's a file (not a dir)
                    if os.path.isfile(os.path.join(WATCH_DIRECTORY, filename)):
                        process_file(filename)
            
            time.sleep(POLL_INTERVAL)
            
    except KeyboardInterrupt:
        print("\nStopping monitor.")

if __name__ == "__main__":
    # Allow overriding watch directory via argument
    if len(sys.argv) > 1:
        WATCH_DIRECTORY = sys.argv[1]
        
    monitor_directory()
