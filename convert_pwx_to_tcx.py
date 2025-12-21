import xml.etree.ElementTree as ET
import datetime
import sys
import os

def convert_pwx_to_tcx(input_file, output_file, strava_optimized=False):
    try:
        tree = ET.parse(input_file)
        root = tree.getroot()
    except Exception as e:
        raise Exception(f"Error parsing PWX file: {e}")

    # Namespaces
    ns_pwx = {'pwx': 'http://www.peaksware.com/PWX/1/0'}
    
    # Extract start time
    # <time>2025-12-03T05:48:22</time>
    workout_node = root.find('pwx:workout', ns_pwx)
    if workout_node is None:
        print("Error: No workout node found.")
        return

    time_node = workout_node.find('pwx:time', ns_pwx)
    if time_node is None:
        print("Error: No start time found.")
        return
    
    start_time_str = time_node.text
    try:
        # Parse the timestamp
        start_time = datetime.datetime.fromisoformat(start_time_str)
        
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
            
    except ValueError:
        # Fallback for formats that might not be strictly ISO
        print(f"Warning: Could not parse time '{start_time_str}' with fromisoformat.")
        return

    # Create TCX structure
    tcx_ns = "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"
    tpx_ns = "http://www.garmin.com/xmlschemas/ActivityExtension/v2"
    xsi_ns = "http://www.w3.org/2001/XMLSchema-instance"
    
    ET.register_namespace("", tcx_ns)
    ET.register_namespace("ax", tpx_ns)
    ET.register_namespace("xsi", xsi_ns)

    tcx_root = ET.Element(f"{{{tcx_ns}}}TrainingCenterDatabase", {
        f"{{{xsi_ns}}}schemaLocation": f"{tcx_ns} http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd"
    })

    activities = ET.SubElement(tcx_root, "Activities")
    if strava_optimized:
        activity = ET.SubElement(activities, "Activity", Sport="VirtualRide")
        ET.SubElement(activity, "Id").text = start_time_str
        ET.SubElement(activity, "Notes").text = "Virtual Ride"
    else:
        activity = ET.SubElement(activities, "Activity", Sport="Biking")
        ET.SubElement(activity, "Id").text = start_time_str
        ET.SubElement(activity, "Notes").text = "Indoor Cycling"
    
    # Creator metadata (copied from working sample to ensure Strava trusts elevation)
    creator = ET.SubElement(activity, "Creator")
    creator.set(f"{{{xsi_ns}}}type", "Device_t")
    ET.SubElement(creator, "Name").text = "Garmin TCX with Barometer"
    ET.SubElement(creator, "UnitId").text = "0"
    ET.SubElement(creator, "ProductId").text = "20119"
    version = ET.SubElement(creator, "Version")
    ET.SubElement(version, "VersionMajor").text = "0"
    ET.SubElement(version, "VersionMinor").text = "0"
    ET.SubElement(version, "BuildMajor").text = "0"
    ET.SubElement(version, "BuildMinor").text = "0"

    lap = ET.SubElement(activity, "Lap", StartTime=start_time_str)
    
    # Summary data (optional but good to have if available, we'll skip for now and just do tracks)
    # We need TotalTimeSeconds and DistanceMeters for the Lap at least strictly speaking, 
    # but Strava often calculates this from tracks. Let's try to get it from summarydata if possible.
    summary_data = workout_node.find('pwx:summarydata', ns_pwx)
    total_time = 0
    total_dist = 0
    
    if summary_data is not None:
        dur_node = summary_data.find('pwx:duration', ns_pwx)
        if dur_node is not None:
            total_time = float(dur_node.text)
            ET.SubElement(lap, "TotalTimeSeconds").text = f"{total_time:.1f}"
            
        # Dist is usually in samples, but let's see if we can find max dist in samples later
        # For now, placeholder or 0
        ET.SubElement(lap, "DistanceMeters").text = "0.0" 

    # Track
    track = ET.SubElement(lap, "Track")

    samples = workout_node.findall('pwx:sample', ns_pwx)
    total_samples = len(samples)
    
    max_dist = 0.0
    total_elevation_gain_m = 0.0
    previous_alt = None
    
    print(f"Converting {total_samples} samples...")
    
    for i, sample in enumerate(samples):
        # Progress update every 10%
        if total_samples > 0 and i % (total_samples // 10 if total_samples >= 10 else 1) == 0:
            percent = int((i / total_samples) * 100)
            sys.stdout.write(f"\rProgress: {percent}%")
            sys.stdout.flush()

        trackpoint = ET.SubElement(track, "Trackpoint")
        
        # 1. Time (Must be first)
        time_offset = float(sample.find('pwx:timeoffset', ns_pwx).text)
        tp_time = start_time + datetime.timedelta(seconds=time_offset)
        ET.SubElement(trackpoint, "Time").text = tp_time.isoformat()
        
        # Extract all potential values first
        alt_node = sample.find('pwx:alt', ns_pwx)
        dist_node = sample.find('pwx:dist', ns_pwx)
        hr_node = sample.find('pwx:hr', ns_pwx)
        cad_node = sample.find('pwx:cad', ns_pwx)
        pwr_node = sample.find('pwx:pwr', ns_pwx)
        spd_node = sample.find('pwx:spd', ns_pwx)

        # 2. Position (Static GPS for graphing support)
        # Strava needs GPS data to display HR/power graphs over time.
        # Using a static position in Colorado so graphs work while preserving elevation.
        position = ET.SubElement(trackpoint, "Position")
        ET.SubElement(position, "LatitudeDegrees").text = "40.0150"  # Boulder, CO area
        ET.SubElement(position, "LongitudeDegrees").text = "-105.2705"

        # 3. AltitudeMeters (Must be before Distance, HR, Cadence)
        if alt_node is not None:
             alt_val = float(alt_node.text)
             ET.SubElement(trackpoint, "AltitudeMeters").text = alt_node.text
             
             if previous_alt is not None:
                 delta = alt_val - previous_alt
                 if delta > 0:
                     total_elevation_gain_m += delta
             previous_alt = alt_val

        # 4. DistanceMeters
        if dist_node is not None:
            dist_val = float(dist_node.text)
            ET.SubElement(trackpoint, "DistanceMeters").text = f"{dist_val:.2f}"
            if dist_val > max_dist:
                max_dist = dist_val

        # 5. HeartRateBpm
        if hr_node is not None:
            hr_val = hr_node.text
            hr_elm = ET.SubElement(trackpoint, "HeartRateBpm")
            ET.SubElement(hr_elm, "Value").text = str(int(float(hr_val)))
            
        # 6. Cadence
        if cad_node is not None:
            ET.SubElement(trackpoint, "Cadence").text = str(int(float(cad_node.text)))

        # 7. Extensions (Power, Speed)
        if pwr_node is not None or spd_node is not None:
            extensions = ET.SubElement(trackpoint, "Extensions")
            tpx = ET.SubElement(extensions, f"{{{tpx_ns}}}TPX")
            
            if pwr_node is not None:
                ET.SubElement(tpx, f"{{{tpx_ns}}}Watts").text = str(int(float(pwr_node.text)))
            
            if spd_node is not None:
                 ET.SubElement(tpx, f"{{{tpx_ns}}}Speed").text = spd_node.text
    
    # Final progress update
    sys.stdout.write(f"\rProgress: 100%\n")
    sys.stdout.flush()

    # Update Lap Distance
    lap.find("DistanceMeters").text = f"{max_dist:.2f}"

    # Calculate Summary Stats
    dist_miles = max_dist * 0.000621371
    elevation_feet = total_elevation_gain_m * 3.28084
    
    # Duration formatting (total_time is already extracted if available, otherwise from last sample)
    if total_time == 0 and len(samples) > 0:
         # Try to estimate from last sample time offset if not in summary
         last_sample = samples[-1]
         last_offset = float(last_sample.find('pwx:timeoffset', ns_pwx).text)
         total_time = last_offset

    if total_time > 0:
        duration = str(datetime.timedelta(seconds=int(total_time)))
    else:
        duration = "Unknown"

    print("\nConversion Summary:")
    print("-" * 20)
    print(f"Distance:  {dist_miles:.2f} miles")
    print(f"Duration:  {duration}")
    print(f"Elevation: {elevation_feet:.0f} feet")
    print("-" * 20 + "\n")

    # Write to file
    tree = ET.ElementTree(tcx_root)
    tree.write(output_file, encoding='UTF-8', xml_declaration=True)
    print(f"Successfully converted {input_file} to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_pwx_to_tcx.py <input_pwx> [output_tcx]")
        sys.exit(1)
    
    input_pwx = sys.argv[1]
    
    # Determine output filename
    if len(sys.argv) >= 3:
        output_filename = os.path.basename(sys.argv[2])
    else:
        # Default to input filename with .tcx extension
        base_name = os.path.splitext(os.path.basename(input_pwx))[0]
        output_filename = f"{base_name}.tcx"
    
    # Ensure output directory exists
    output_dir = "converted"
    os.makedirs(output_dir, exist_ok=True)
    
    output_tcx = os.path.join(output_dir, output_filename)
    
    convert_pwx_to_tcx(input_pwx, output_tcx)
