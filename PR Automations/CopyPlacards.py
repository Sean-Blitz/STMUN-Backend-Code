import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
# Requires: pip install gspread google-auth
from typing import List, Union, Dict
import driveFunctions
import SlidesFunctions
import sheetFunctions

SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/presentations']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

def authenticate():
    """
    Handles OAuth login and returns valid credentials.
    """
    creds = None

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

    return creds

creds = authenticate()
sheets_service = build('sheets', 'v4', creds)
drive_service = driveFunctions.get_drive_service(creds)
slides_service = build('slides', 'v1', creds)

committeescount = int(input("How many committees are there? "))

dictionaryofplacards = sheetFunctions.read_columns_until_blank("1LgQxP67-pe6JW0lixWacp3ou5UV1f2vmSGVI8j5IPIs", "Placards Automation", committeescount, sheets_service)
committeenames = sheetFunctions.read_headers("1LgQxP67-pe6JW0lixWacp3ou5UV1f2vmSGVI8j5IPIs", "Placards Automation", committeescount, sheets_service)

for i in range(len(dictionaryofplacards)): # Iterate through each committee. You are on file level here.
    committeename = committeenames[i]
    
    # Copy the template slide and rename it
    copied_slide_id = driveFunctions.copy_drive_file(
        drive_service,
        '191sgGYyUZ8NKz9e92JHeLLR_ilo9KJTuH2nQColZDAY',  
        new_name=committeename
    )

    firstslideID = SlidesFunctions.get_first_slide_id(
        slides_service,
        copied_slide_id
    )

    if len(dictionaryofplacards[committeename]) % 2 != 0:
        pagelength = (len(dictionaryofplacards[committeename]) // 2) + 1
    else:
        pagelength = len(dictionaryofplacards[committeename]) // 2
    
    pageIDs = []
    print(f"Creating {pagelength} pages...")
    for i in range(pagelength): #you are on page level now. Copying pages here.
        pageIDs.append(SlidesFunctions.duplicate_slide(
            slides_service,
            copied_slide_id,
            firstslideID 
        ))

    print("Adding new placeholdrs...")
    for i in range(pagelength): #now replacing placeholders with new placeholder names on each slide.
        newnumber = i + 3
        SlidesFunctions.replace_two_placeholders_on_slide(
            slides_service,
            copied_slide_id,
            pageIDs[i],
            "{Country_1}",
            f"{{Country_{newnumber}}}",
            "{Country_2}",
            f"{{Country_{newnumber + 1}}}"
        )
    
    print("Building value map...")
    value_map = {} #building a dictionary to map new placeholder names to actual names from placardnames.
    for i in range(pagelength):
        number = i+1
        placardnames = dictionaryofplacards[i]
        value_map[f"{{Country_{number}}}"] = placardnames[i]

    print("Applying names...")
    SlidesFunctions.apply_value_map_to_slide(
        slides_service,
        copied_slide_id,
        value_map= value_map
    )

    print("Done with " + committeename)