import os
import sys
import time
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

import driveFunctions
import sheetFunctions
import csv
import questionary
import AssignmentsFunctions

SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/documents']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'
registrationSheetID = "1LgQxP67-pe6JW0lixWacp3ou5UV1f2vmSGVI8j5IPIs"
registrationSheetURL = f"https://docs.google.com/spreadsheets/d/{registrationSheetID}/edit"
sheetname = "testing"

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

drive_service = driveFunctions.get_drive_service(authenticate())
sheets_service = build('sheets', 'v4', credentials=authenticate())

sheetSchools = sheetFunctions.get_column_data_until_empty(sheets_service, registrationSheetID, sheetname, "A", 2)
unassignedSchools = AssignmentsFunctions.get_unassigned_schools(sheetSchools, "assignedSchools.csv")

while unassignedSchools:
    selectedSchool = AssignmentsFunctions.select_school_to_assign(unassignedSchools)
    row = sheetFunctions.find_row_by_string(sheets_service, registrationSheetID, sheetname, "A", selectedSchool)
    output = sheetFunctions.read_cells(sheets_service, registrationSheetID, [f"{sheetname}!R{row}", f"{sheetname}!S{row}", f"{sheetname}!T{row}", f"{sheetname}!U{row}", f"{sheetname}!V{row}", f"{sheetname}!W{row}", f"{sheetname}!X{row}", f"{sheetname}!Y{row}", f"{sheetname}!Q{row}"])
    CountryPrefs = output[0]
    MiddleEasternBloc = output[1]
    AmericanBloc = output[2]
    EuropeanBloc = output[3]
    AsianBloc = output[4]
    AfricanBloc = output[5]
    PacificBloc = output[6]
    SecurityCouncil = output[7]
    numdels = output[8]
    if len(output) == 9:  # check if all 9 cells have values
        print("Top 5 country preferences:", CountryPrefs)
        print("Middle Eastern Bloc:", MiddleEasternBloc)
        print("American Bloc:", AmericanBloc)
        print("European Bloc:", EuropeanBloc)
        print("Asian Bloc:", AsianBloc)
        print("African Country Bloc:", AfricanBloc)
        print("Pacific Country Bloc:", PacificBloc)
        print("Security Council interest:", SecurityCouncil)
        nextrow = sheetFunctions.get_column_until_empty(sheets_service, registrationSheetID, "Assignments", "A", 1) + 1
        cells_map = {}
        for i in range(numdels):
            cells_map["Assignments!"+sheetFunctions.sheets_alphabet(i+1)+str(nextrow)] = f"{selectedSchool} - #{i+1}"
        sheetFunctions.write_values_to_sheet_from_dict(sheets_service, registrationSheetID, cells_map)

        GA = int(input("How many delegates to put in GA?"))
        Specialized = int(input("How many delegates to put in Specialized?"))
        if GA + Specialized > numdels:
            print("Error: The total number of delegates does not match the expected count.")
        else:
            Crisis = numdels - GA - Specialized
            print("\033[F", end="")
            print("\033[F", end="")
            print("\033[K", end="")
            print("\033[K", end="")
            print(f"GA: {GA}, Specialized: {Specialized}, Crisis: {Crisis}")
        unassignedSchools.remove(selectedSchool)

        time.sleep(5) #pause for sheet to register changes, then check.
        #CSV add this school after checking!
    else:
        print("Error: Not all expected cells have values. Please check the sheet for completeness.")
    #remember to add the assigned school to the CSV!