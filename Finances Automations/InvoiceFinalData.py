import csv
import os
import re
import datetime
import requests
import json
import sys
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
#Warning: this code will take a while to run because of time.sleep()
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
#These four are other .py files with the proper functions called here.
import driveFunctions
import sheetFunctions
import time

SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/documents']
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

#-------------------------------- Main Script ----------------------------#
sheets_service = build('sheets', 'v4', credentials=authenticate())
creds = authenticate()
drive_service = driveFunctions.get_drive_service(creds)
folderIDs = ['1HEfiWYpQKMCVeRheuj7fo0cUmZ6Rh6vA']
#Change folderIDs from year to year.

for i in range(len(folderIDs)): #each folder
    allsheetIDs = driveFunctions.list_google_sheet_ids(folderIDs[i], drive_service)
    balance = []
    comments = []
    name = []
    data = [['Name', 'Balance', 'Comments']]
    for j in range(len(allsheetIDs)): #each sheet
        sheetID = allsheetIDs[j]
        cell_values = sheetFunctions.read_cells(sheets_service, sheetID, ['Purchase order!H36', 'Purchase order!C38', 'Purchase order!C16'])
        balance = cell_values[0]
        comments = cell_values[1]
        name = cell_values[2]
        data.append([name, balance, comments])
        time.sleep(1)  # To avoid hitting API rate limits. 

    file_path = f'InvoiceData{i}.csv'
    # write the data to a CSV file
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        # Write all rows at once
        writer.writerows(data)

    print(f"Data successfully written to {file_path}")