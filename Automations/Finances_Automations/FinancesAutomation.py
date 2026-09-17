#If the code outputs nothing, check if there are any emails in the Finances Automation label.
import os
import datetime
import sys
from pathlib import Path
AUTOMATIONS_DIR = Path(__file__).resolve().parent.parent

# Inject the path into sys.path if it isn't already present
if str(AUTOMATIONS_DIR) not in sys.path:
    sys.path.insert(0, str(AUTOMATIONS_DIR))

from dotenv import load_dotenv
from Infrastructure import GmailAPI
from Infrastructure import DriveAPI
from Infrastructure import SheetAPI
from Infrastructure import DocAPI
from Infrastructure import AirtableAPI
BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = str(BASE_DIR / "credentials.json")
TOKEN_FILE = str(BASE_DIR / "token.json")

mailAPI = GmailAPI(CREDENTIALS_FILE=CREDENTIALS_FILE, TOKEN_FILE=TOKEN_FILE)
CloudStorageAPI = DriveAPI(CREDENTIALS_FILE=CREDENTIALS_FILE, TOKEN_FILE=TOKEN_FILE)
Sheets = SheetAPI(CREDENTIALS_FILE=CREDENTIALS_FILE, TOKEN_FILE=TOKEN_FILE)
Document = DocAPI(CREDENTIALS_FILE=CREDENTIALS_FILE, TOKEN_FILE=TOKEN_FILE)
Database = AirtableAPI()
load_dotenv()

# ----------------------- Controls -----------------------
table_name = "Form Response"
AttendingFolderID = os.getenv("AttendingFolderID")  #change these two when years change.
NotAttendingFolderID = os.getenv("NotAttendingFolderID")
template1_independent = os.getenv("template1_independent_invoice_ID") #change these templates every year.
template2_independent = os.getenv("template2_independent_invoice_ID")
template3_independent = os.getenv("template3_independent_invoice_ID")
template1_school = os.getenv("template1_school_invoice_ID")
template2_school = os.getenv("template2_school_invoice_ID")
template3_school = os.getenv("template3_school_invoice_ID")
emailtemplate = os.getenv("emailtemplateID")
emailfolderID = os.getenv("emailfolderID")
YearText = os.getenv("YearText")
# -------------------------------------------------------

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
    findfolder = CloudStorageAPI.find_subfolder_id(
            parent_folder_id= NotAttendingFolderID,
            search_string= sName.replace("High School","").replace("School","").strip()
        )

    if findfolder != None:
        movedfolder = CloudStorageAPI.move_drive_folder(
            folder_id=findfolder,
            new_parent_folder_id= AttendingFolderID
        )
        print("Folder moved successfully. Check name regardless.")
        yearfolder = CloudStorageAPI.create_drive_folder(
            name=YearText,
            mime_type='application/vnd.google-apps.folder',
            parent_id=movedfolder
        )

    elif findfolder == None:
        createdfolder = CloudStorageAPI.create_drive_folder(
            name= sName,
            mime_type='application/vnd.google-apps.folder',
            parent_id=AttendingFolderID
        )
        print("Folder created successfully. Check name regardless.")
        yearfolder = CloudStorageAPI.create_drive_folder(
            name=YearText, 
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

today = datetime.date.today()
gmailIDs = mailAPI.find_emails_from_sender_with_label()
if EmailCount := len(gmailIDs) == 0:
    print("No emails found with the label 'Finances Automation'. What this means is that you have to check your email to see if the Airtable automated email is marked with the label.")
    sys.exit()
print(f"Found {len(gmailIDs)} emails with the label 'Finances Automation'.")
mail_school_names = mailAPI.extract_strings_and_remove_label(message_ids=gmailIDs)

i=0
for i in range(len(mail_school_names)):
    record_id = Database.get_field_by_name(search_name=mail_school_names[i], search_column="School Name")

    sName, sAddress, sPhoneNumber, aName, aPhoneNumber, aEmail, DelegateCount, Balance, CheckDelegateCount, Subtotal, delFee, head_delegate_email, date = Database.search_records(record_id)
    city, state, zipCode, DelCount = Database.search_formResponse(record_id)
    state = statename(state)

    independent = input("Independent registration? y/n. Exit to stop.").lower().strip()
    if independent == "exit":
        print("Process cancelled.")
        continue
    while not independent in ["y", "n", "exit"]:
        independent = input("Invalid input. Independent registration? y/n. Exit to stop.")
    if independent == "exit":
        print("Process cancelled for this school.")
        continue

    yearfolder = folderfinding(sName)
    CreateInvoice = lambda templateID, independent: CloudStorageAPI.copy_drive_file_with_number(
                
                original_file_id= templateID,
                destination_folder_id=yearfolder,
                new_name_template="Invoice {n}" + (" - Independent" if independent == "y" else ""),
                sName = sName)

    if "-" in str(date):
        splitter = "-"
    elif "/" in str(date):
        splitter = "/"
    else:
        print("Date format error. Check Airtable.")
        print("Date: " + str(date))
        sys.exit()
    month = int(date.split(splitter)[1])
    day = int(date.split(splitter)[2])
    year = int(date.split(splitter)[0])
    date = datetime.date(year, month, day)

    if date.month == 11 and date.day == 1 or date.month == 10 or date.month == 9 or date.month == 8:
        newInvoice = CreateInvoice(template1_independent if independent == "y" else template1_school, independent)
        checkcell = "B25"
        inputCell = "B28"
    elif date.month == 12 and date.day <= 20 or date.month == 11 and date.day >= 2: 
        newInvoice = CreateInvoice(template2_independent if independent == "y" else template2_school, independent)
        checkcell = "B26"
        inputCell = "B29"
    elif date.month == 1 and date.day <= 26 or date.month == 12 and date.day >= 21:
        newInvoice = CreateInvoice(template3_independent if independent == "y" else template3_school, independent)
        checkcell = "B27"
        inputCell = "B30"
    else:
        print("Today's date error for delegate fee.")
        sys.exit()

    Sheets.write_values_to_sheet_from_dict(
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

    Sheets.write_values_to_sheet_from_dict(
        spreadsheet_id=newInvoice,
        cell_value_map={
            f"Purchase order!{checkcell}": "true",
            f"Purchase order!{inputCell}": DelCount,
        })

    SheetTotal = Sheets.read_single_cell(spreadsheet_id=newInvoice, cell_range="Purchase order!H36")

    if int(float(SheetTotal.replace("$", "").replace(",", "").strip()) if SheetTotal != None else 0) != Balance:
        print("Subtotal mismatch error.")

    sheeturl = "https://docs.google.com/spreadsheets/d/" + newInvoice
    print(sheeturl)

    docID = CloudStorageAPI.copy_drive_file(
        file_id=emailtemplate,
        destination_folder_id=emailfolderID,
        new_name=f"{sName} Email"
    )

    Document.fill_doc_placeholders(document_id=docID,aEmail = aEmail,schoolName = sName,sheeturl = sheeturl, headDelegateEmail = head_delegate_email)

    print("Email draft created.")
    keepgoing()
    CloudStorageAPI.share_doc_with_user(document_id=docID,email="sg@scvmun.com",role="writer")

    print("Shared.")
    print("https://docs.google.com/document/d/" + docID)