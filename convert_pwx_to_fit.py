import datetime
from fit_tool.fit_file_builder import FitFileBuilder
from fit_tool.profile.messages.file_id_message import FileIdMessage
from fit_tool.profile.messages.record_message import RecordMessage
from fit_tool.profile.messages.lap_message import LapMessage
from fit_tool.profile.messages.session_message import SessionMessage
from fit_tool.profile.messages.event_message import EventMessage
from fit_tool.profile.profile_type import Manufacturer, FileType, Sport, SubSport, Event, EventType
import xml.etree.ElementTree as ET
import sys

def convert_pwx_to_fit(pwx_file_path, fit_file_path):
    # Namespaces
    ns_pwx = {'pwx': 'http://www.thierrys-world.de/pwx/'} # Adjust if different
    
    # Parse XML
    tree = ET.parse(pwx_file_path)
    root = tree.getroot()

    # robust namespace handling
    if '}' in root.tag:
        ns_url = root.tag.split('}')[0].strip('{')
        ns_pwx = {'pwx': ns_url}
    else:
        ns_pwx = {}

    # Find workout
    if ns_pwx:
        workout_node = root.find('pwx:workout', ns_pwx)
    else:
        workout_node = root.find('workout')

    if workout_node is None:
        raise ValueError("No 'workout' element found in PWX file")

    builder = FitFileBuilder(auto_define=True, min_string_size=50)

    # Time parsing
    time_str = workout_node.find('pwx:time', ns_pwx).text
    try:
        start_time = datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        # Try with fractional seconds
        start_time = datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.%f")
    
    # If no timezone info, assume it's local time and add timezone
    if start_time.tzinfo is None:
        import time as time_module
        # Get local timezone offset
        if time_module.daylight:
            utc_offset = -time_module.altzone
        else:
            utc_offset = -time_module.timezone
        tz = datetime.timezone(datetime.timedelta(seconds=utc_offset))
        start_time = start_time.replace(tzinfo=tz)

    # 1. File ID
    file_id = FileIdMessage()
    file_id.type = FileType.ACTIVITY
    file_id.manufacturer = Manufacturer.GARMIN #need this.
    file_id.product = 3121  # Garmin Edge 530 (from working reference file)
    file_id.serial_number = 12345
    file_id.time_created = round(start_time.timestamp() * 1000)
    builder.add(file_id)

    # Convert samples to records
    samples = workout_node.findall('pwx:sample', ns_pwx)
    records = []
    
    total_dist = 0.0
    max_speed = 0.0
    total_ascent = 0.0
    prev_alt = None
    
    # Start Event
    event_start = EventMessage()
    event_start.event = Event.TIMER
    event_start.event_type = EventType.START
    event_start.timestamp = round(start_time.timestamp() * 1000)
    builder.add(event_start)

    print(f"Converting {len(samples)} samples to FIT...")
    for i, sample in enumerate(samples):
        # Progress update every 10%
        if len(samples) > 0 and i % (len(samples) // 10 if len(samples) >= 10 else 1) == 0:
            percent = int((i / len(samples)) * 100)
            sys.stdout.write(f"\rProgress: {percent}%")
            sys.stdout.flush()

        time_offset = float(sample.find('pwx:timeoffset', ns_pwx).text)
        current_time = start_time + datetime.timedelta(seconds=time_offset)
        timestamp_ms = round(current_time.timestamp() * 1000)

        record = RecordMessage()
        record.timestamp = timestamp_ms
        
        # Position: Static GPS for graphing support
        # Strava needs GPS data to display HR/power graphs over time.
        # Using a static position in Colorado so graphs work while preserving elevation.
        record.position_lat = int(40.0150 * ((2**32) / 360))  # Boulder, CO area (semicircles)
        record.position_long = int(-105.2705 * ((2**32) / 360))

        # Distance
        dist_node = sample.find('pwx:dist', ns_pwx)
        if dist_node is not None:
            dist = float(dist_node.text)
            record.distance = dist # meters
            total_dist = max(total_dist, dist)

        # Altitude
        alt_node = sample.find('pwx:alt', ns_pwx)
        if alt_node is not None:
            alt = float(alt_node.text)
            record.altitude = alt           # legacy field
            record.enhanced_altitude = alt  # High precision field
            if prev_alt is not None:
                diff = alt - prev_alt
                if diff > 0:
                    total_ascent += diff
            prev_alt = alt

        # Heart Rate
        hr_node = sample.find('pwx:hr', ns_pwx)
        if hr_node is not None:
            record.heart_rate = int(hr_node.text)

        # Cadence
        cad_node = sample.find('pwx:cad', ns_pwx)
        if cad_node is not None:
            record.cadence = int(cad_node.text)

        # Power
        pwr_node = sample.find('pwx:pwr', ns_pwx)
        if pwr_node is not None:
            record.power = int(pwr_node.text)

        # Speed
        spd_node = sample.find('pwx:spd', ns_pwx)
        if spd_node is not None:
            speed = float(spd_node.text)
            record.speed = speed
            max_speed = max(max_speed, speed)

        builder.add(record)
        records.append(record)

    # Final progress
    sys.stdout.write("\rProgress: 100%\n")
    sys.stdout.flush()

    # LAP
    lap = LapMessage()
    lap.timestamp = records[-1].timestamp if records else round(start_time.timestamp() * 1000)
    lap.start_time = round(start_time.timestamp() * 1000)
    
    elapsed_time_val = float(samples[-1].find('pwx:timeoffset', ns_pwx).text) if samples else 0.0
    
    lap.total_elapsed_time = elapsed_time_val
    lap.total_timer_time = elapsed_time_val
    lap.total_distance = total_dist
    lap.max_speed = max_speed
    lap.total_ascent = total_ascent
    builder.add(lap)

    # SESSION
    session = SessionMessage()
    session.timestamp = lap.timestamp
    session.start_time = lap.start_time
    session.total_elapsed_time = lap.total_elapsed_time
    session.total_timer_time = lap.total_timer_time
    session.total_distance = total_dist
    session.max_speed = max_speed
    session.total_ascent = total_ascent
    session.sport = Sport.CYCLING
    # session.sub_sport = SubSport.INDOOR_CYCLING  # Removed: prevents HR graphs in Strava
    session.first_lap_index = 0
    session.num_laps = 1
    builder.add(session)

    fit_file = builder.build()
    fit_file.to_file(fit_file_path)

    # Print Summary
    dist_miles = total_dist * 0.000621371
    dur_str = str(datetime.timedelta(seconds=int(elapsed_time_val)))
    elev_feet = total_ascent * 3.28084
    
    print("\nFIT Conversion Summary:")
    print("--------------------")
    print(f"Distance:  {dist_miles:.2f} miles")
    print(f"Duration:  {dur_str}")
    print(f"Elevation: {elev_feet:.0f} feet")
    print("--------------------")
