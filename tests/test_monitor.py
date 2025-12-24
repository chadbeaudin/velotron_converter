import pytest
import sys
import os
import time
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import monitor_and_convert

def test_setup_directories(setup_test_dirs):
    # Patch BASE_DIRECTORY in the module
    with patch('monitor_and_convert.BASE_DIRECTORY', setup_test_dirs['base']):
        monitor_and_convert.setup_directories()
        
        for dir_name in ['original', 'converted', 'processed', 'failed']:
            assert os.path.exists(os.path.join(setup_test_dirs['base'], dir_name))

def test_process_file_success(setup_test_dirs, tmp_pwx_file):
    # Move tmp_pwx_file to the 'original' directory
    filename = os.path.basename(tmp_pwx_file)
    target_path = os.path.join(setup_test_dirs['original'], filename)
    import shutil
    shutil.copy(tmp_pwx_file, target_path)
    
    with patch('monitor_and_convert.BASE_DIRECTORY', setup_test_dirs['base']):
        with patch('monitor_and_convert.STRAVA_ENABLED', False):
            with patch('monitor_and_convert.FIT_SUPPORT_ENABLED', False):
                monitor_and_convert.process_file(filename)
                
                # Check if output exists in converted/
                # The filename logic uses timestamp from PWX: 2025-12-03T05:48:22 -> 2025-12-03_05-48-22.tcx
                expected_tcx = os.path.join(setup_test_dirs['converted'], "2025-12-03_05-48-22.tcx")
                assert os.path.exists(expected_tcx)
                
                # Check if original moved to processed/
                assert os.path.exists(os.path.join(setup_test_dirs['processed'], filename))
                assert not os.path.exists(target_path)

def test_process_file_failure(setup_test_dirs):
    # Create a corrupted PWX file
    filename = "corrupt.pwx"
    target_path = os.path.join(setup_test_dirs['original'], filename)
    with open(target_path, 'w') as f:
        f.write("not xml")
    
    with patch('monitor_and_convert.BASE_DIRECTORY', setup_test_dirs['base']):
        with patch('monitor_and_convert.STRAVA_ENABLED', False):
            monitor_and_convert.process_file(filename)
            
            # Check if original moved to failed/
            assert os.path.exists(os.path.join(setup_test_dirs['failed'], filename))
            assert not os.path.exists(target_path)
