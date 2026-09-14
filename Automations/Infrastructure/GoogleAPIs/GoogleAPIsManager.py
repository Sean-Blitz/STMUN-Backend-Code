import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from pathlib import Path

class GoogleAPIs:
    def __init__(self, SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/documents', "https://www.googleapis.com/auth/script.projects"]):
        BASE_DIR = Path(__file__).resolve().parent
        self.CREDENTIALS_FILE = str(BASE_DIR / "credentials.json")
        self.TOKEN_FILE = str(BASE_DIR / "token.json")
        self.SCOPES = SCOPES
    
    def authenticate(self):
        """
        Handles OAuth login and returns valid credentials.
        """
        creds = None

        # Load existing token
        if os.path.exists(self.TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(self.TOKEN_FILE, self.SCOPES)

        # If no valid credentials, log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.CREDENTIALS_FILE, self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save token for next run
            with open(self.TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())

        return creds
