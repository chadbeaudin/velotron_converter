from fit_tool.fit_file import FitFile
import sys

def debug_api(path):
    try:
        fit_file = FitFile.from_file(path)
        print(f"Attributes of FitFile: {dir(fit_file)}")
        print(f"Number of records: {len(fit_file.records)}")
        if len(fit_file.records) > 0:
            first_record = fit_file.records[0]
            print(f"First record type: {type(first_record)}")
            print(f"First record attributes: {dir(first_record)}")
            if hasattr(first_record, 'message'):
                print(f"First record message type: {type(first_record.message)}")
                print(f"First record message content: {first_record.message}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_api("/Users/chadbeaudin/Downloads/MyWhoosh_Zone_2_Endurance_40min.fit")
