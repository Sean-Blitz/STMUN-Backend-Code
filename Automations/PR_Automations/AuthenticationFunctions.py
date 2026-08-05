from googleapiclient.discovery import build
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

def authenticate():
    """
    Handles OAuth login and returns valid credentials.
    """
    creds = None

    SCOPES = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/presentations',
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/gmail.modify'
    ]

    CREDENTIALS_FILE = 'credentials.json'
    TOKEN_FILE = 'token.json'

    # Load existing token
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If no valid credentials, log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token for next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    # Build service objects
    drive_service = build('drive', 'v3', credentials=creds)
    sheets_service = build('sheets', 'v4', credentials=creds)
    slides_service = build('slides', 'v1', credentials=creds)
    docs_service = build('docs', 'v1', credentials=creds)
    gmail_service = build('gmail', 'v1', credentials=creds)

    return drive_service, sheets_service, slides_service, docs_service, gmail_service