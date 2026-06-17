import os
import datetime
import sys
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import driveFunctions
import sheetFunctions
import FinancesAutomation

def inputcheck(input, valid):
    while input not in valid:
        input = input("Invalid input. " + "Continue? y/n")
    return input

#if modifying scopes, go to FinancesAutomation.py and change there.
creds = FinancesAutomation.authenticate()
sheets_service = build('sheets', 'v4', credentials=creds)
drive_service = driveFunctions.get_drive_service(creds)

Final = input("Is this the final invoice? y/n")
if Final != "y":
    From = int(input("Invoice number that you are copying from?"))
    To = int(input("Invoice number that you are copying to?"))
    if From == To or To > 3 or From > 2:
        print ("Input error.")
        sys.exit()

FolderIDs = driveFunctions.get_subfolders_as_dict(drive_service, PARENT_FOLDER_ID = "1BPlHoP2G4ih7ewIRQsU0vV9ILkOSxsCv") #change this every year.
names = list(FolderIDs.keys())
toeditsheets = {}
paidschoolsheets = {}
yearfolderids = []
stop = 0
for i in range(len(names)):
    yearfolder = driveFunctions.find_subfolder_id(drive_service, FolderIDs[names[i]], "SCVMUN LV (2026)") #change this every year.
    if yearfolder is None:
        print(f"Could not find year folder for {names[i]}.")
        stop = 1
        continue
    else:
        yearfolderids.append(yearfolder)

if stop >= 1:
    print("Process cancelled due to missing year folders.")
    sys.exit()

if Final != "y":
    for i in range(len(FolderIDs)):
        yearfolder = yearfolderids[i]
        inputcheck(input(f"Processing {names[i]}... Continue? y/n"), ["y", "n"])
        fromsheetID = driveFunctions.find_sheet_id_by_name_contains(drive_service, yearfolder, f"Invoice {From}") #type: ignore
        if fromsheetID is None:
            print("Could not find source sheet.")
            continue

        payments = sheetFunctions.read_single_unformatted_cell(sheets_service, fromsheetID, "Purchase order!H33")
        balance = sheetFunctions.read_single_unformatted_cell(sheets_service, fromsheetID, "Purchase order!H36")
        if not balance is None and not payments is None:
            balance = int(balance)
            payments = int(payments)

        if Final != "y": #not final invoice, regular copying.
            From = int(input("Invoice number that you are copying from?"))
            To = int(input("Invoice number that you are copying to?"))
            
            if From == To or To > 3 or From > 2: #error checking.
                print ("Input error.")
                sys.exit()
            
            tosheetID = driveFunctions.copy_drive_file(drive_service, fromsheetID, yearfolder, f"Invoice {To} - {names[i]}")
            if payments == 0: #unpaid.
                if From == 1 and To == 2:
                    earlydelegates = int(sheetFunctions.read_single_cell(sheets_service, fromsheetID, "Purchase order!B28")) #type: ignore
                    sheetFunctions.write_values_to_sheet_from_dict(
                        sheets_service,
                        tosheetID,
                        {
                            "Purchase order!C22": datetime.datetime.now().strftime("%m/%d/%Y"),
                            "Purchase order!B29": earlydelegates,
                            "Purchase order!B28": "0",
                            "Purchase order!A10": f"Invoice {To}",
                        }
                    )
                elif From == 2 and To == 3:
                    earlydelegates = int(sheetFunctions.read_single_cell(sheets_service, fromsheetID, "Purchase order!B28")) #type: ignore
                    regulardelegates = int(sheetFunctions.read_single_cell(sheets_service, fromsheetID, "Purchase order!B29")) #type: ignore
                    sheetFunctions.write_values_to_sheet_from_dict(
                        sheets_service,
                        tosheetID,
                        {
                            "Purchase order!C22": datetime.datetime.now().strftime("%m/%d/%Y"),
                            "Purchase order!B30": regulardelegates + earlydelegates,
                            "Purchase order!B28": "0",
                            "Purchase order!B29": "0",
                            "Purchase order!A10": f"Invoice {To}",
                        }
                    )
            elif payments != 0 and balance != 0: #partially paid.
                toeditsheets[names[i]] = tosheetID
                sheetFunctions.write_values_to_sheet_from_dict(
                    sheets_service,
                    tosheetID,
                    {
                        "Purchase order!C22": datetime.datetime.now().strftime("%m/%d/%Y"),
                        "Purchase order!A10": f"Invoice {To}",
                    })
            elif payments != 0 and balance == 0: #fully paid
                paidschoolsheets[names[i]] = tosheetID
                sheetFunctions.write_values_to_sheet_from_dict(
                    sheets_service,
                    tosheetID,
                    {
                        "Purchase order!C22": datetime.datetime.now().strftime("%m/%d/%Y"),
                        "Purchase order!A10": f"Invoice {To}",
                    })
            print("Here is the new invoice: https://docs.google.com/spreadsheets/d/" + tosheetID )


    forfunctionlist = list(toeditsheets.keys())
    print("You should manually edit these sheets:")
    for n in range (len(toeditsheets)):
        print(forfunctionlist[n] + " - " + "https://docs.google.com/spreadsheets/d/" + str(toeditsheets[forfunctionlist[n]]))

    print() #for readability
    forfunctionlist2 = list(paidschoolsheets.keys())
    print("These schools have paid in full:")

    for i in range(len(paidschoolsheets)):
        print(forfunctionlist2[i] + " - " + str(paidschoolsheets[forfunctionlist2[i]]))

elif Final == "y":
    for i in range(len(FolderIDs)):
        yearfolder = yearfolderids[i]
        if names[i] == "Santa Teresa High School":
            continue
        print(f"Processing final invoice for {names[i]}...")
        fromsheetID = driveFunctions.find_sheet_id_by_name_contains(drive_service, yearfolder, "Invoice 3")
        if fromsheetID is None:
            print("Could not find source sheet.")
            continue

        payments = int(sheetFunctions.read_single_unformatted_cell(sheets_service, fromsheetID, "Purchase order!H33")) #type: ignore
        balance = int(sheetFunctions.read_single_unformatted_cell(sheets_service, fromsheetID, "Purchase order!H36")) #type: ignore

        if payments != 0 and balance == 0:
            tosheetID = driveFunctions.copy_drive_file(drive_service, fromsheetID, "1lpF-H-EhDMQWBOK6xgqlhYE00E0wWiUt", f"Final Invoice - {names[i]}")
            sheetFunctions.write_values_to_sheet_from_dict(
                sheets_service,
                tosheetID,
                {
                    "Purchase order!A10": "FINAL INVOICE",
                })
            print("Paid" )
        elif payments != 0 and balance != 0:
            tosheetID = driveFunctions.copy_drive_file(drive_service, fromsheetID, "1TUMtb3k4lv6ahFIxxDAeAYZReiT0RCJj", f"Final Invoice - {names[i]}")
            sheetFunctions.write_values_to_sheet_from_dict(
                sheets_service,
                tosheetID,
                {
                    "Purchase order!A10": "FINAL INVOICE",
                })
            print("Partially Paid")
        elif payments == 0 and balance >= 0:
            tosheetID = driveFunctions.copy_drive_file(drive_service, fromsheetID, "11u9S7UrT6HEAqsMAyh0yZVhb0BvSLxMa", f"Final Invoice - {names[i]}")
            sheetFunctions.write_values_to_sheet_from_dict(
                sheets_service,
                tosheetID,
                {
                    "Purchase order!A10": "FINAL INVOICE",
                })
            print(f"Unpaid")
        
#There are IDs for every payment status folder above. Change that each year.