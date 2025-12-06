from fit_tool.fit_file import FitFile
import sys

def inspect(path):
    print(f"--- Inspecting: {path} ---")
    try:
        fit_file = FitFile.from_file(path)
        
        # Use to_rows() to get readable data
        rows = fit_file.to_rows()
        print(f"File parsed into {len(rows)} rows.")
        
        # Debug: Print first row structure
        if len(rows) > 0:
            print(f"First row type: {type(rows[0])}")
            print(f"First row content: {rows[0]}")
            return
                 
        # If to_rows returns something else, print type of first item
        if len(rows) > 0:
            print(f"First row type: {type(rows[0])}")
            print(f"First row content: {rows[0]}")
        
    except Exception as e:
        print(f"Error decoding {path}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 inspect_fit.py <file.fit>")
        sys.exit(1)
    
    inspect(sys.argv[1])
