import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from strava_uploader import StravaUploader

@pytest.fixture
def uploader():
    return StravaUploader("client_id", "client_secret", "refresh_token")

def test_refresh_access_token_success(uploader):
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'new_access_token',
            'expires_at': 1234567890,
            'refresh_token': 'new_refresh_token'
        }
        mock_post.return_value = mock_response
        
        assert uploader.refresh_access_token() is True
        assert uploader.access_token == 'new_access_token'
        assert uploader.refresh_token == 'new_refresh_token'

def test_refresh_access_token_failure(uploader):
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'message': 'Bad Request'}
        mock_post.return_value = mock_response
        
        assert uploader.refresh_access_token() is False

def test_ensure_token_expired(uploader):
    uploader.expires_at = 0 # Expired
    with patch.object(uploader, 'refresh_access_token', return_value=True) as mock_refresh:
        assert uploader.ensure_token() is True
        mock_refresh.assert_called_once()

def test_upload_file_success(uploader, tmp_path):
    test_file = tmp_path / "test.tcx"
    test_file.write_text("fake tcx content")
    
    with patch.object(uploader, 'ensure_token', return_value=True):
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {'id': 12345}
            mock_post.return_value = mock_response
            
            result = uploader.upload_file(str(test_file))
            assert result == 12345

def test_upload_file_duplicate(uploader, tmp_path):
    test_file = tmp_path / "test.fit"
    test_file.write_text("fake fit content")
    
    with patch.object(uploader, 'ensure_token', return_value=True):
        with patch('requests.post') as mock_post:
            from requests.exceptions import HTTPError
            mock_response = MagicMock()
            mock_response.status_code = 409
            mock_response.json.return_value = {'message': 'Conflict', 'errors': [{'resource': 'Upload', 'field': 'activity', 'code': 'duplicate'}]}
            
            # Setup the error to behave like a requests HTTPError
            error = HTTPError(response=mock_response)
            mock_post.side_effect = error
            
            result = uploader.upload_file(str(test_file))
            assert result == "duplicate"
