import os
import datetime
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import requests


class TokenManager:
    def __init__(self):
        load_dotenv()
        self.token = None
        self.token_expiry = None
    
    def get_valid_token(self):
        # Check if token exists and is still valid (with 5 minutes buffer)
        if self.token and self.token_expiry and datetime.now() < self.token_expiry - timedelta(minutes=5):
            return self.token
            
        # Get new token
        token_url = "https://alpha.uipath.com/identity_/connect/token"
        client_id = "D445A127-17F0-4582-9533-343E2A80A3A8"
        client_secret = os.getenv('UIPATH_CLIENT_SECRET')
        
        if not client_secret:
            raise ValueError("UIPATH_CLIENT_SECRET environment variable not set")
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret
        }
        
        try:
            response = requests.post(token_url, headers=headers, data=data)
            response.raise_for_status()
            token_data = response.json()
            
            self.token = token_data['access_token']
            # Set token expiry to 1 hour from now
            self.token_expiry = datetime.now() + timedelta(hours=1)
            
            return self.token
            
        except requests.exceptions.RequestException as e:
            print(f"Error getting token: {e}")
            raise