from fit_tool.fit_file import FitFile
from fit_tool.fit_file_builder import FitFileBuilder
from fit_tool.profile.messages.file_id_message import FileIdMessage
from fit_tool.profile.profile_type import Manufacturer, FileType
import os

def inject_garmin_id(input_path, output_path):
    """
    Injects Garmin device identification into a FIT file.
    Returns True if successful, False otherwise.
    """
    try:
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Source file not found: {input_path}")

        fit_file = FitFile.from_file(input_path)
        
        # Collect all data messages (skip definition messages, builder adds them)
        messages = []
        found_file_id = False
        
        for record in fit_file.records:
            if not record.is_definition:
                msg = record.message
                if isinstance(msg, FileIdMessage) and not found_file_id:
                    msg.manufacturer = Manufacturer.GARMIN
                    msg.product = 3121 # Garmin Edge 530
                    msg.serial_number = 12345
                    found_file_id = True
                messages.append(msg)
        
        if not found_file_id:
            new_file_id = FileIdMessage()
            new_file_id.type = FileType.ACTIVITY
            new_file_id.manufacturer = Manufacturer.GARMIN
            new_file_id.product = 3121
            new_file_id.serial_number = 12345
            messages.insert(0, new_file_id)

        # Rebuild using FitFileBuilder
        builder = FitFileBuilder(auto_define=True)
        for msg in messages:
            builder.add(msg)
            
        new_fit_file = builder.build()
        new_fit_file.to_file(output_path)
        return True

    except Exception as e:
        print(f"Error injecting Garmin ID: {e}")
        return False
