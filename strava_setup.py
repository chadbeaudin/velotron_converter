import os
import sys
try:
    import requests
except ImportError:
    print("\nError: The 'requests' library is not installed.")
    print("Please install it by running:")
    print("\n    pip install requests\n")
    sys.exit(1)

import webbrowser
from urllib.parse import urlencode

def setup_strava():
    print("\n--- Strava API Setup Assistant ---\n")
    print("This script will help you get your Strava Refresh Token.")
    print("You will need your Client ID and Client Secret from: https://www.strava.com/settings/api\n")

    client_id = input("Enter your Strava Client ID: ").strip()
    client_secret = input("Enter your Strava Client Secret: ").strip()

    if not client_id or not client_secret:
        print("Client ID and Secret are required.")
        return

    # Scope activity:write is required for uploading
    params = {
        'client_id': client_id,
        'redirect_uri': 'http://localhost',
        'response_type': 'code',
        'scope': 'activity:write,activity:read_all',
        'approval_prompt': 'force'
    }

    url = "https://www.strava.com/oauth/authorize?" + urlencode(params)

    print(f"\n1. Open the following URL in your browser to authorize this app:")
    print(f"\n{url}\n")
    
    try:
        webbrowser.open(url)
    except:
        pass

    print("2. After you authorize, you will be redirected to localhost.")
    print("3. The URL will look like: http://localhost/?state=&code=AUTHORIZATION_CODE&scope=...")
    auth_code = input("\nCopy and paste the AUTHORIZATION_CODE from the URL here: ").strip()

    if not auth_code:
        print("Authorization code is required.")
        return

    print("\nExchanging code for tokens...")
    
    token_url = "https://www.strava.com/oauth/token"
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': auth_code,
        'grant_type': 'authorization_code'
    }

    try:
        response = requests.post(token_url, data=payload)
        response.raise_for_status()
        data = response.json()
        
        refresh_token = data.get('refresh_token')
        access_token = data.get('access_token')
        
        print("\n--- SUCCESS! ---\n")
        print(f"Your Strava Refresh Token is: {refresh_token}")
        print("\nAdd these environment variables to your Docker container or environment:")
        print(f"STRAVA_CLIENT_ID={client_id}")
        print(f"STRAVA_CLIENT_SECRET={client_secret}")
        print(f"STRAVA_REFRESH_TOKEN={refresh_token}")
        print("\nKeep these secret!")
        
    except Exception as e:
        print(f"\nError exchanging code for tokens: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")

if __name__ == "__main__":
    setup_strava()
