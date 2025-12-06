from fit_tool.fit_file import FitFile
import sys

def inspect_fit(path):
    print(f"--- Inspecting: {path} ---")
    try:
        fit_file = FitFile.from_file(path)
        
        # Check Records
        records = fit_file.records
        print(f"Total Records: {len(records)}")
        
        has_alt = False
        has_pos = False
        
        # Find first Data Record
        found_data = False
        for i, r in enumerate(records):
            msg = r.message
            if 'RecordMessage' in type(msg).__name__:
                print(f"First Data Record (Index {i}):")
                
                alt = getattr(msg, 'altitude', None)
                e_alt = getattr(msg, 'enhanced_altitude', None)
                
                print(f"  Alt: {alt}")
                print(f"  Enh Alt: {e_alt}")
                
                lat = getattr(msg, 'position_lat', None)
                long = getattr(msg, 'position_long', None)
                print(f"  Pos: {lat}, {long}")
                
                found_data = True
                break
        
        if not found_data:
            print("No RecordMessage found!")
        
        print(f"Has Altitude data: {has_alt}")
        print(f"Has Position data: {has_pos}")

        # Check Session/Lap
        for msg in fit_file.messages:
            if msg.name == 'session':
                print("SESSION MESSAGE:")
                print(f"  Sport: {getattr(msg, 'sport', 'N/A')}")
                print(f"  SubSport: {getattr(msg, 'sub_sport', 'N/A')}")
                print(f"  Total Ascent: {getattr(msg, 'total_ascent', 'N/A')}")
                print(f"  Total Distance: {getattr(msg, 'total_distance', 'N/A')}")
            if msg.name == 'file_id':
                print("FILE_ID MESSAGE:")
                print(f"  Manufacturer: {getattr(msg, 'manufacturer', 'N/A')}")
                print(f"  Product: {getattr(msg, 'product', 'N/A')}")

    except Exception as e:
        print(f"Error decoding {path}: {e}")
    print("\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inspect_fit.py <file1> <file2> ...")
        sys.exit(1)
        
    for f in sys.argv[1:]:
        inspect_fit(f)
