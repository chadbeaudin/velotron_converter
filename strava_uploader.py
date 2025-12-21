import os
import requests
import time
import sys

class StravaUploader:
    def __init__(self, client_id, client_secret, refresh_token):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token = None
        self.expires_at = 0

    def refresh_access_token(self):
        """Refreshes the access token using the refresh token."""
        url = "https://www.strava.com/oauth/token"
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token'
        }
        
        try:
            response = requests.post(url, data=payload)
            
            if response.status_code == 400:
                error_data = response.json()
                error_msg = error_data.get('message', '').lower()
                if 'client_id' in str(error_data).lower() or 'invalid client' in str(error_data).lower():
                    print("  !! ERROR: Strava STRAVA_CLIENT_ID or STRAVA_CLIENT_SECRET is incorrect.")
                elif 'refresh_token' in str(error_data).lower() or 'invalid_grant' in str(error_data).lower():
                    print("  !! ERROR: Strava STRAVA_REFRESH_TOKEN is invalid or expired.")
                else:
                    print(f"  !! ERROR: Strava Authentication failed: {error_data.get('message', 'Unknown Error')}")
                return False
                
            response.raise_for_status()
            data = response.json()
            
            self.access_token = data['access_token']
            self.refresh_token = data.get('refresh_token', self.refresh_token) # Strava may return a new refresh token
            self.expires_at = data['expires_at']
            
            print("Successfully refreshed Strava access token.")
            return True
        except Exception as e:
            print(f"  !! ERROR: Could not connect to Strava for token refresh: {e}")
            return False

    def ensure_token(self):
        """Ensures we have a valid access token."""
        # If token is missing or expires in less than 5 minutes, refresh it
        if not self.access_token or time.time() > (self.expires_at - 300):
            return self.refresh_access_token()
        return True

    def upload_file(self, file_path, activity_type=None, description="Uploaded by Velotron Converter"):
        """Uploads a FIT or TCX file to Strava."""
        if not self.ensure_token():
            print("Cannot upload to Strava: Token refresh failed.")
            return False

        print(f"Uploading {os.path.basename(file_path)} to Strava...")
        
        file_extension = os.path.splitext(file_path)[1].lower().strip('.')
        if file_extension not in ['fit', 'tcx']:
            print(f"Unsupported file format for Strava: {file_extension}")
            return False

        url = "https://www.strava.com/api/v3/uploads"
        headers = {
            'Authorization': f"Bearer {self.access_token}"
        }
        
        # We send a minimal payload to force Strava to read metadata from the file.
        # This mimics a manual web upload as closely as possible.
        payload = {
            'description': description,
            'data_type': file_extension
        }
        
        if activity_type:
            payload['activity_type'] = activity_type
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f)}
                response = requests.post(url, headers=headers, data=payload, files=files)
                response.raise_for_status()
                
                data = response.json()
                upload_id = data.get('id')
                print(f"Upload initiated. ID: {upload_id}")
                return upload_id
        except Exception as e:
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    
                    # Detect duplicate based on status code or message content
                    is_duplicate = (e.response.status_code == 409)
                    if not is_duplicate:
                        is_duplicate = 'duplicate' in str(error_data).lower()
                    
                    if is_duplicate:
                        print(f"  -> Note: This activity is already on Strava (Duplicate).")
                        return "duplicate"
                    
                    print(f"  -> Strava API Error: {e.response.status_code} - {error_data.get('message', 'No message')}")
                    if error_data.get('errors'):
                        print(f"     Details: {error_data.get('errors')}")
                except:
                    print(f"  -> Strava Error: {e}")
                    print(f"     Response Text: {e.response.text}")
            else:
                print(f"  -> Error: {e}")
            return False

    def check_upload_status(self, upload_id):
        """Polls Strava for the status of an upload."""
        if not self.ensure_token():
            return None

        url = f"https://www.strava.com/api/v3/uploads/{upload_id}"
        headers = {
            'Authorization': f"Bearer {self.access_token}"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error checking Strava upload status: {e}")
            return None

def main():
    # Simple CLI test if run directly
    client_id = os.getenv('STRAVA_CLIENT_ID')
    client_secret = os.getenv('STRAVA_CLIENT_SECRET')
    refresh_token = os.getenv('STRAVA_REFRESH_TOKEN')
    
    if not all([client_id, client_secret, refresh_token]):
        print("Strava credentials not fully configured in environment variables.")
        sys.exit(1)
        
    if len(sys.argv) < 2:
        print("Usage: python strava_uploader.py <file_to_upload>")
        sys.exit(1)
        
    file_path = sys.argv[1]
    uploader = StravaUploader(client_id, client_secret, refresh_token)
    upload_id = uploader.upload_file(file_path)
    
    if upload_id:
        print("Waiting for Strava to process the file...")
        for _ in range(10):
            time.sleep(2)
            status = uploader.check_upload_status(upload_id)
            if status:
                print(f"Status: {status.get('status')} - {status.get('error') or ''}")
                if status.get('activity_id'):
                    print(f"Success! Activity ID: {status.get('activity_id')}")
                    print(f"Link: https://www.strava.com/activities/{status.get('activity_id')}")
                    break
                if status.get('error'):
                    break
            else:
                break

if __name__ == "__main__":
    main()
