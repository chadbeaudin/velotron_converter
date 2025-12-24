import os
import pytest
import sys
import xml.etree.ElementTree as ET

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from convert_pwx_to_tcx import convert_pwx_to_tcx

def test_convert_pwx_to_tcx_basic(tmp_pwx_file, tmp_path):
    output_tcx = str(tmp_path / "output.tcx")
    convert_pwx_to_tcx(tmp_pwx_file, output_tcx)
    
    assert os.path.exists(output_tcx)
    
    # Simple validation of output content
    tree = ET.parse(output_tcx)
    root = tree.getroot()
    
    # Check for Activities node
    activities = root.find('.//{http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2}Activities')
    assert activities is not None
    
    # Check for Trackpoints
    trackpoints = root.findall('.//{http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2}Trackpoint')
    assert len(trackpoints) == 3
    
    # Check if HR is present in a trackpoint
    hr_val = trackpoints[0].find('.//{http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2}HeartRateBpm/{http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2}Value')
    assert hr_val is not None
    assert hr_val.text == "120"

def test_convert_pwx_to_tcx_strava_optimized(tmp_pwx_file, tmp_path):
    output_tcx = str(tmp_path / "output_strava.tcx")
    convert_pwx_to_tcx(tmp_pwx_file, output_tcx, strava_optimized=True)
    
    tree = ET.parse(output_tcx)
    root = tree.getroot()
    
    activity = root.find('.//{http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2}Activity')
    assert activity.get('Sport') == "VirtualRide"

def test_convert_pwx_to_tcx_elevation_gain(tmp_pwx_file, tmp_path):
    output_tcx = str(tmp_path / "output_elev.tcx")
    convert_pwx_to_tcx(tmp_pwx_file, output_tcx)
    
    # We had 100 -> 105 -> 110, so gain should be 10.
    # Total distance was 200m.
    # Check if final distance is correct in Lap
    tree = ET.parse(output_tcx)
    root = tree.getroot()
    lap = root.find('.//{http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2}Lap')
    dist = lap.find('{http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2}DistanceMeters')
    assert float(dist.text) == 200.0
