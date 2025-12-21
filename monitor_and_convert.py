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

# Strava Support
from strava_uploader import StravaUploader
STRAVA_CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
STRAVA_CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')
STRAVA_REFRESH_TOKEN = os.getenv('STRAVA_REFRESH_TOKEN')
STRAVA_ENABLED = all([STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REFRESH_TOKEN])

if STRAVA_ENABLED:
    strava_uploader = StravaUploader(STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REFRESH_TOKEN)
    print("Strava auto-import: ENABLED")
else:
    print("Strava auto-import: DISABLED (missing STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, or STRAVA_REFRESH_TOKEN)")

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Monitor and convert PWX files to TCX/FIT formats')
parser.add_argument('directory', nargs='?', default=None, 
                    help='Base directory containing original/ folder (default: script location)')
args = parser.parse_args()

# Configuration
USING_CLI_ARG = False
if args.directory:
    MONITOR_PATH = args.directory
    USING_CLI_ARG = True
else:
    # Default to current directory if not in Docker /veloMonitor
    if os.path.exists('/veloMonitor'):
        MONITOR_PATH = '/veloMonitor'
    elif os.path.exists('/Volumes/veloMonitor'):
        MONITOR_PATH = '/Volumes/veloMonitor'
        print(f"Network drive found - using: {MONITOR_PATH}")
    else:
        MONITOR_PATH = os.getcwd()
        print(f"Running locally - using directory: {MONITOR_PATH}")

BASE_DIRECTORY = os.path.abspath(MONITOR_PATH)

# VALIDATION: Prevent "Creating Directory" loop on Unraid
# If the path doesn't exist, AND we didn't explicitly ask for it via CLI,
# AND the default /veloMonitor mount point DOES exist... then it's a config error.
if not os.path.exists(BASE_DIRECTORY) and not USING_CLI_ARG:
    if os.path.exists('/veloMonitor'):
        print(f"\nSaved you from a crash! :)")
        print(f"CRITICAL MISCONFIGURATION DETECTED:")
        print(f"-------------------------------------------------------------")
        print(f"The Container is trying to look at: '{BASE_DIRECTORY}'")
        print(f"BUT that directory does not exist inside this container.")
        print(f"However, the default path '/veloMonitor' DOES exist.")
        print(f"-------------------------------------------------------------")
        print(f"SOLUTION: Change your 'MONITOR_PATH' variable to '/veloMonitor'.")
        print(f"Unraid has mapped your external files to '/veloMonitor', so that is")
        print(f"where the script needs to look.")
        print(f"-------------------------------------------------------------\n")
        print("Sleeping for 60 seconds to prevent restart loop...")
        time.sleep(60)
        sys.exit(1)

# Permissions Configuration (Unraid/LinuxServer style)
# Only active if PUID/PGID are explicitly set in environment
PUID = os.getenv('PUID')
PGID = os.getenv('PGID')
if PUID: PUID = int(PUID)
if PGID: PGID = int(PGID)

def set_permissions(path):
    """Apply PUID/PGID permissions only if configured."""
    if not PUID or not PGID:
        return
    try:
        os.chown(path, PUID, PGID)
    except Exception as e:
        pass # Silently fail on local systems where this isn't supported

def safe_move(src, dst):
    """Robust move that handles network drives and metadata errors."""
    try:
        shutil.move(src, dst)
    except Exception as e:
        # If shutil.move fails (often metadata/permission issues on network drives),
        # try a manual copy and delete.
        try:
            shutil.copyfile(src, dst)
            os.remove(src)
        except Exception as inner_e:
            raise Exception(f"Failed to move file from {src} to {dst}: {inner_e}")

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
            set_permissions(path)
            print(f"Existing directory not found.  Created directory: {path}")
        else:
            # Enforce permissions on existing directories too (in case they were created by root previously)
            set_permissions(path)
            # print(f"Directory already exists, using existing directory: {path}")

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
        set_permissions(tcx_path)
        print(f"  -> Generated TCX: converted/{tcx_filename}")

        # 2. Convert to FIT (if enabled)
        if FIT_SUPPORT_ENABLED:
            fit_filename = f"{base_name}.fit"
            fit_path = os.path.join(BASE_DIRECTORY, CONVERTED_DIR_NAME, fit_filename)
            try:
                convert_pwx_to_fit(input_path, fit_path)
                set_permissions(fit_path)
                print(f"  -> Generated FIT: converted/{fit_filename}")
            except Exception as e:
                print(f"  -> FIT Conversion Failed: {e}")
        else:
            print("  -> FIT conversion skipped (library missing)")
        
        # 3. Import to Strava (if enabled)
        if STRAVA_ENABLED:
            # Prefer FIT for Strava if it exists, otherwise use TCX
            upload_path = None
            if FIT_SUPPORT_ENABLED:
                fit_filename = f"{base_name}.fit"
                fit_path = os.path.join(BASE_DIRECTORY, CONVERTED_DIR_NAME, fit_filename)
                if os.path.exists(fit_path):
                    upload_path = fit_path
            
            if not upload_path:
                upload_path = tcx_path
            
            print(f"  -> Uploading to Strava: {os.path.basename(upload_path)}...")
            try:
                result = strava_uploader.upload_file(upload_path)
                if result == "duplicate":
                    pass # Message already printed by uploader
                elif result:
                    print(f"  -> Strava upload initiated (ID: {result})")
                    print("  Waiting for Strava to process...", end="", flush=True)
                    # Poll for activity ID (max 15 seconds)
                    activity_id = None
                    for _ in range(5):
                        time.sleep(3)
                        print(".", end="", flush=True)
                        status = strava_uploader.check_upload_status(result)
                        if status and status.get('activity_id'):
                            activity_id = status.get('activity_id')
                            break
                        if status and status.get('error'):
                            err_msg = status.get('error', '')
                            if 'duplicate' in err_msg.lower() or 'already exists' in err_msg.lower():
                                print(f"\n  -> Note: This activity is already on Strava (Duplicate).")
                                result = "duplicate" # Mark as duplicate so we don't print "processing" fail
                            else:
                                print(f"\n  -> Strava Processing Error: {err_msg}")
                            break
                    
                    if activity_id:
                        print(f"\n  -> SUCCESS! Strava Activity: https://www.strava.com/activities/{activity_id}")
                    elif result == "duplicate":
                        pass
                    else:
                        print("\n  -> Upload still processing - check your Strava account shortly.")
                else:
                    print("  -> Strava upload failed (check logs for details)")
            except Exception as e:
                print(f"  -> Strava upload error: {e}")
        
        # Move original file to 'processed'
        processed_dest = os.path.join(BASE_DIRECTORY, PROCESSED_DIR_NAME, filename)
        safe_move(input_path, processed_dest)
        set_permissions(processed_dest)
        print(f"Completed processing: {filename}")
        print(f"  -> Original moved to processed/")
        sys.stdout.flush()
        
    except Exception as e:
        print(f"  -> FAILED: {e}")
        # Move failed file to 'failed'
        try:
            failed_dest = os.path.join(BASE_DIRECTORY, FAILED_DIR_NAME, filename)
            safe_move(input_path, failed_dest)
            set_permissions(failed_dest)
            print(f"  -> Moved original to failed/")
        except Exception as move_err:
            print(f"  -> CRITICAL: Could not move failed file: {move_err}")

def monitor_directory():
    """Main monitoring loop."""
    watch_dir = os.path.join(BASE_DIRECTORY, ORIGINAL_DIR_NAME)
    
    print(f"\nVelotron Converter Version: {os.getenv('APP_VERSION', 'unknown')} \n\n")
    print(f"Monitoring directory: {watch_dir}")
    print(f"Place PWX files in the '{watch_dir}' folder to convert them to TCX and FIT.")
    #print(f"Press Ctrl+C to stop.")
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
    monitor_directory()

print(f"Press Ctrl+C to stop.")
