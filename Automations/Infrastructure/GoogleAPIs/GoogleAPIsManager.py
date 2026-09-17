import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from pathlib import Path

class GoogleAPIs:
    def __init__(self, SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/documents', "https://www.googleapis.com/auth/script.projects"], CREDENTIALS_FILE = None, TOKEN_FILE = None):
        if CREDENTIALS_FILE is None:
            BASE_DIR = Path(__file__).resolve().parent
            self.CREDENTIALS_FILE = str(BASE_DIR / "credentials.json")
            if not os.path.exists(self.CREDENTIALS_FILE):
                raise FileNotFoundError(f"Credentials file not found at {self.CREDENTIALS_FILE}. Please ensure the credentials.json file is present, or pass into function an explicit location.")
            if TOKEN_FILE is None:
                self.TOKEN_FILE = str(BASE_DIR / "token.json")
            if TOKEN_FILE is not None:
                raise ValueError("TOKEN_FILE cannot exist if credentials file exists. This violates the program and may break functionality in the future. Find the credentials file!")
        else:
            self.CREDENTIALS_FILE = CREDENTIALS_FILE
            if TOKEN_FILE is None:
                self.TOKEN_FILE = str(Path(CREDENTIALS_FILE).parent / "token.json")
            else:
                self.TOKEN_FILE = TOKEN_FILE
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
