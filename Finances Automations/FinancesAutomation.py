#If the code outputs nothing, check if there are any emails in the Finances Automation label.
import os
import datetime
import sys
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
#These four are other .py files with the proper functions called here.
import ATCode
import gmailFunctions
import driveFunctions
import sheetFunctions
import docFunctions

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

def statename(state):
    statetempstore = state
    stateabbreviation = {"Alabama": "AL","Alaska": "AK","Arizona": "AZ","Arkansas": "AR","California": "CA","Colorado": "CO","Connecticut": "CT","Delaware": "DE","Florida": "FL","Georgia": "GA",
        "Hawaii": "HI","Idaho": "ID","Illinois": "IL","Indiana": "IN","Iowa": "IA","Kansas": "KS","Kentucky": "KY","Louisiana": "LA","Maine": "ME","Maryland": "MD","Massachusetts": "MA","Michigan": "MI",
        "Minnesota": "MN","Mississippi": "MS","Missouri": "MO","Montana": "MT","Nebraska": "NE","Nevada": "NV","New Hampshire": "NH","New Jersey": "NJ","New Mexico": "NM","New York": "NY",
        "North Carolina": "NC","North Dakota": "ND","Ohio": "OH","Oklahoma": "OK","Oregon": "OR","Pennsylvania": "PA","Rhode Island": "RI","South Carolina": "SC","South Dakota": "SD","Tennessee": "TN","Texas": "TX","Utah": "UT",
        "Vermont": "VT","Virginia": "VA","Washington": "WA","West Virginia": "WV","Wisconsin": "WI","Wyoming": "WY","District of Columbia": "DC"}
    
    state = stateabbreviation.get(state)
    if state == None:
        print("Not a US state in address. Manually check the invoice to edit address.")
        state = statetempstore
    return state

def folderfinding(sName):
    findfolder = driveFunctions.find_subfolder_id(
            service=drive_service,
            parent_folder_id= NotAttendingFolderID,
            search_string= sName.replace("High School","").replace("School","").strip()
        )

    if findfolder != None:
        movedfolder = driveFunctions.move_drive_folder(
            service=drive_service,
            folder_id=findfolder,
            new_parent_folder_id= AttendingFolderID
        )
        print("Folder moved successfully. Check name regardless.")
        yearfolder = driveFunctions.create_drive_folder(
            service=drive_service,
            name='SCVMUN LV (2026)', #this is what you should change every year.
            mime_type='application/vnd.google-apps.folder',
            parent_id=movedfolder
        )

    elif findfolder == None:
        createdfolder = driveFunctions.create_drive_folder(
            service=drive_service,
            name= sName,
            mime_type='application/vnd.google-apps.folder',
            parent_id=AttendingFolderID
        )
        print("Folder created successfully. Check name regardless.")
        yearfolder = driveFunctions.create_drive_folder(
            service=drive_service,
            name='SCVMUN LV (2026)', #this is what you should change every year.
            mime_type='application/vnd.google-apps.folder',
            parent_id=createdfolder
        )
    else:
        print("Error in finding folder.")
        tryagain = input("Try again? y/n").lower().strip()
        while not tryagain in ["y", "n"]:
            tryagain = input("Invalid input. Try again? y/n").lower().strip()
        if tryagain == "y":
            folderfinding(sName)
        else:            
            print("Process cancelled.")
            sys.exit()
    
    return yearfolder # type: ignore

def keepgoing():
    keepgoing = input("Share? y/n")
    while not keepgoing in ["y", "n"]:
        keepgoing = input("Invalid input. Continue? y/n")
    if keepgoing != "y":
        print("Process cancelled.")
        sys.exit()

# ----------------------- MAIN SCRIPT -----------------------
#Below two lines only need to happen once.
sheets_service = build('sheets', 'v4', credentials=authenticate())
creds = authenticate()
drive_service = driveFunctions.get_drive_service(creds)
gmail_service = build('gmail', 'v1', credentials=creds)
docs_service = build('docs', 'v1', credentials=creds)
api_token = "patcikx9vfYeXF4gz.20004c29f9f7601a7bb9ee1d4474468dc46e4c4a1ebcc1105b7fd6a310933560"
base_id = "appEySB2x9jqHy16Q"   #change this next year
table_name = "Form Response"
AttendingFolderID = "1BPlHoP2G4ih7ewIRQsU0vV9ILkOSxsCv"  #change these two when years change.
NotAttendingFolderID = "12yoRVdgJ9U7Koo-OK-wp-09ycOMoMc_4"
template1_independent = "1nIXIxgR57DWdu6A7eopkBAoB8IiuicZgd1Y1TvQSBdk" #change these templates every year.
template2_independent = "1JFi7uRHeQV9pYd6nAGcDl-elXs4D31tS3FqzpF3jEzc"
template3_independent = "1plvWHfrhVu9PjRlRdJ9EPg9EkNxOB4yrRw3ySwnNIeI"
template1_school = "1ZB17zyTXzjWeX_3xsUXVIaZIGWfEayqwU68HQ2IL3zg"
template2_school = "1EBKQYdnZevr2sJV1fdi4S2pVtZFHtsWKowrXGzdeoCs"
template3_school = "1Kzg_Nkdx1SdzvCADenSK_vvHkCv5qBer6_Ia-TwXXEg"
emailtemplate = "1OB-rn-AcMMhjaeELjg2nI8IDZUb7d6jW3gJcehKqnHk"
emailfolderID = "1SWw6PxL_ewuVRWtJwyLkS1HmKLkffdf5"

today = datetime.date.today()

gmailIDs = gmailFunctions.find_emails_from_sender_with_label(service=gmail_service)

mail_school_names = gmailFunctions.extract_strings_and_remove_label(service=gmail_service, message_ids=gmailIDs)

i=0
for i in range(len(mail_school_names)):
    record_id = ATCode.get_field_by_name(search_name=mail_school_names[i], search_column="School Name")

    schoolName, schoolAddress, advisorPhoneNumber, advisorEmail, delegateCount, date, datestr = ATCode.view_latest_record(record_id) #first view latest record. DO NOT USE THESE VARIABLES EXCEPT DATE.
    #This is a bug to fix. Currently it pulls date from the most recent record, but we want it from specifically that school.

    sName, sAddress, sPhoneNumber, aName, aPhoneNumber, aEmail, DelegateCount, Balance, CheckDelegateCount, Subtotal, delFee = ATCode.search_records(record_id)
    city, state, zipCode, DelCount = ATCode.search_formResponse(record_id)
    state = statename(state)

    independent = input("Independent registration? y/n. Exit to stop.").lower().strip()
    if independent == "exit":
        print("Process cancelled.")
        continue
    while not independent in ["y", "n", "exit"]:
        independent = input("Invalid input. Independent registration? y/n. Exit to stop.")

    keepgoing()

    yearfolder = folderfinding(sName)
    CreateInvoice = lambda templateID, independent: driveFunctions.copy_drive_file_with_number(
                service=drive_service,
                original_file_id= templateID,
                destination_folder_id=yearfolder,
                new_name_template="Invoice {n}" + (" - Independent" if independent == "y" else ""),
                sName = sName)
    
    newrecord = lambda datebox, delbox, number: ATCode.create_airtable_record(record_id, datestr, datebox, delbox, DelegateCount, number, schoolName)
    if date.month == 11 and date.day == 1 or date.month == 10 or date.month == 9 or date.month == 8:
        DelBox = "Initial Delegates (Early)"
        DateBox = "Date (Early)"
        number_2 = 10 if independent == "y" else 40
        writing = newrecord(DateBox, DelBox, number_2)
        newInvoice = CreateInvoice(template1_independent if independent == "y" else template1_school, independent)
        checkcell = "B25"
        inputCell = "B28"
    elif date.month == 12 and date.day <= 20 or date.month == 11 and date.day >= 2: 
        DelBox = "Initial Delegates (Regular)"
        DateBox = "Date (Regular)"
        number_2 = 15 if independent == "y" else 50
        writing = newrecord(DateBox, DelBox, number_2)
        newInvoice = CreateInvoice(template2_independent if independent == "y" else template2_school, independent)
        checkcell = "B26"
        inputCell = "B29"
    elif date.month == 1 and date.day <= 26 or date.month == 12 and date.day >= 21:
        DelBox = "Initial Delegates (Late)"
        DateBox = "Date (Late)"
        number_2 = 20 if independent == "y" else 60
        writing = newrecord(DateBox, DelBox, number_2)
        newInvoice = CreateInvoice(template3_independent if independent == "y" else template3_school, independent)
        checkcell = "B27"
        inputCell = "B30"
    else:
        print("Today's date error for delegate fee.")
        sys.exit()

    sheetFunctions.write_values_to_sheet_from_dict(sheets_service,
        spreadsheet_id=newInvoice,
        cell_value_map={
            "Purchase order!C16": sName,
            "Purchase order!C17": aName,
            "Purchase order!C18": aEmail,
            "Purchase order!C19": aPhoneNumber,
            "Purchase order!C20": sAddress,
            "Purchase order!C21": city + ", " + state + " " + zipCode,
            "Purchase order!C22": datetime.date.today().strftime("%m/%d/%Y"),
        })

    sheetFunctions.write_values_to_sheet_from_dict(sheets_service,
        spreadsheet_id=newInvoice,
        cell_value_map={
            f"Purchase order!{checkcell}": "true",
            f"Purchase order!{inputCell}": DelCount,
        })

    SheetTotal = sheetFunctions.read_single_cell(service=sheets_service, spreadsheet_id=newInvoice, cell_range="Purchase order!H36")

    if int(float(SheetTotal.replace("$", "").replace(",", "").strip()) if SheetTotal != None else 0) != Balance:
        print("Subtotal mismatch error.")

    sheeturl = "https://docs.google.com/spreadsheets/d/" + newInvoice
    print(sheeturl)

    docID = driveFunctions.copy_drive_file(
        service=drive_service,
        file_id=emailtemplate,
        destination_folder_id=emailfolderID,
        new_name=f"{sName} Email"
    )

    docFunctions.fill_doc_placeholders(
        docs_service=docs_service,
        document_id=docID,
        aEmail = aEmail,
        schoolName = sName,
        sheeturl = sheeturl)

    print("Email draft created.")

    keepgoing()

    driveFunctions.share_doc_with_user(
        drive_service=drive_service,
        document_id=docID,
        email="sg@scvmun.com",
        role="writer")

    print("Shared.")
    print("https://docs.google.com/document/d/" + docID)