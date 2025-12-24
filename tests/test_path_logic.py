import os
import pytest
from unittest.mock import patch
import sys

# Add project root to path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# We need to wrap the logic from monitor_and_convert in a function or mock it carefully
# For now, let's extract the core logic into a testable function or just test it via a helper

def get_monitor_path_logic(args_directory=None):
    # This is a copy of the logic in monitor_and_convert.py
    USING_CLI_ARG = False
    ENV_MONITOR_PATH = os.getenv('MONITOR_PATH')

    if args_directory:
        MONITOR_PATH = args_directory
        USING_CLI_ARG = True
    elif ENV_MONITOR_PATH:
        MONITOR_PATH = ENV_MONITOR_PATH
    else:
        # Default search paths if no environment variable or CLI arg is set
        if os.path.exists('/veloMonitor'):
            MONITOR_PATH = '/veloMonitor'
        elif os.path.exists('/velotronMonitor'):
            MONITOR_PATH = '/velotronMonitor'
        elif os.path.exists('/Volumes/veloMonitor'):
            MONITOR_PATH = '/Volumes/veloMonitor'
        else:
            MONITOR_PATH = os.getcwd()
    
    return MONITOR_PATH

def test_cli_path_precedence():
    assert get_monitor_path_logic("/some/cli/path") == "/some/cli/path"

def test_env_var_precedence():
    with patch.dict(os.environ, {"MONITOR_PATH": "/some/env/path"}):
        assert get_monitor_path_logic() == "/some/env/path"

def test_env_var_over_default_path():
    with patch.dict(os.environ, {"MONITOR_PATH": "/some/env/path"}):
        with patch("os.path.exists", return_value=True):
            assert get_monitor_path_logic() == "/some/env/path"

def test_default_veloMonitor():
    with patch.dict(os.environ, {}, clear=True):
        with patch("os.path.exists") as mock_exists:
            mock_exists.side_effect = lambda p: p == '/veloMonitor'
            assert get_monitor_path_logic() == '/veloMonitor'

def test_default_velotronMonitor():
    with patch.dict(os.environ, {}, clear=True):
        with patch("os.path.exists") as mock_exists:
            mock_exists.side_effect = lambda p: p == '/velotronMonitor'
            assert get_monitor_path_logic() == '/velotronMonitor'

def test_fallback_to_getcwd():
    with patch.dict(os.environ, {}, clear=True):
        with patch("os.path.exists", return_value=False):
            with patch("os.getcwd", return_value="/current/dir"):
                assert get_monitor_path_logic() == "/current/dir"
