import os
import datetime
import sys
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
from dotenv import load_dotenv
from Automations.Infrastructure import DriveAPI
from Automations.Infrastructure import SheetAPI
from Automations.Infrastructure import DisplayClass

CloudStorageAPI = DriveAPI()
Sheets = SheetAPI()
Display = DisplayClass()
load_dotenv()

#--------------------- Controls ------------------------
AttendingFolderID = os.getenv("AttendingFolderID")  
YearText = os.getenv("YearText")
fullyPaidInvoiceFolderID = os.getenv("fullyPaidInvoiceFolderID")
partiallyPaidInvoiceFolderID = os.getenv("partiallyPaidInvoiceFolderID")
unpaidInvoiceFolderID = os.getenv("unpaidInvoiceFolderID")
#-------------------------------------------------------

def inputcheck(input_text, valid):
    while input_text not in valid:
        input_text = Display.take_text_input("Invalid input. " + "Continue? y/n")
    return input_text

Final = Display.take_text_input("Is this the final invoice? y/n")
if Final != "y":
    From = int(Display.take_text_input("Invoice number that you are copying from?"))
    To = int(Display.take_text_input("Invoice number that you are copying to?"))
    if From == To or To > 3 or From > 2:
        Display.display ("Input error.")
        sys.exit()

FolderIDs = CloudStorageAPI.get_subfolders_as_dict(AttendingFolderID)
names = list(FolderIDs.keys())
toeditsheets = {}
paidschoolsheets = {}
yearfolderids = []
stop = 0
for i in range(len(names)):
    yearfolder = CloudStorageAPI.find_subfolder_id(FolderIDs[names[i]], YearText)
    if yearfolder is None:
        Display.display(f"Could not find year folder for {names[i]}.")
        stop = 1
        continue
    else:
        yearfolderids.append(yearfolder)

if stop >= 1:
    Display.display("Process cancelled due to missing year folders.")
    sys.exit()

if Final != "y":
    for i in range(len(FolderIDs)):
        yearfolder = yearfolderids[i]
        inputcheck(Display.take_text_input(f"Processing {names[i]}... Continue? y/n"), ["y", "n"])
        fromsheetID = CloudStorageAPI.find_sheet_id_by_name_contains(yearfolder, f"Invoice {From}") #type: ignore
        if fromsheetID is None:
            Display.display("Could not find source sheet.")
            continue

        payments = Sheets.read_single_unformatted_cell(fromsheetID, "Purchase order!H33")
        balance = Sheets.read_single_unformatted_cell(fromsheetID, "Purchase order!H36")
        if not balance is None and not payments is None:
            balance = int(balance)
            payments = int(payments)

        if Final != "y": #not final invoice, regular copying.
            From = int(Display.take_text_input("Invoice number that you are copying from?"))
            To = int(Display.take_text_input("Invoice number that you are copying to?"))
            
            if From == To or To > 3 or From > 2: #error checking.
                Display.display ("Input error.")
                sys.exit()
            
            tosheetID = CloudStorageAPI.copy_drive_file(fromsheetID, yearfolder, f"Invoice {To} - {names[i]}")
            if payments == 0: #unpaid.
                if From == 1 and To == 2:
                    earlydelegates = int(Sheets.read_single_cell(fromsheetID, "Purchase order!B28")) #type: ignore
                    Sheets.write_values_to_sheet_from_dict(
                        tosheetID,
                        {
                            "Purchase order!C22": datetime.datetime.now().strftime("%m/%d/%Y"),
                            "Purchase order!B29": earlydelegates,
                            "Purchase order!B28": "0",
                            "Purchase order!A10": f"Invoice {To}",
                        }
                    )
                elif From == 2 and To == 3:
                    earlydelegates = int(Sheets.read_single_cell(fromsheetID, "Purchase order!B28")) #type: ignore
                    regulardelegates = int(Sheets.read_single_cell(fromsheetID, "Purchase order!B29")) #type: ignore
                    Sheets.write_values_to_sheet_from_dict(
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
                Sheets.write_values_to_sheet_from_dict(
                    tosheetID,
                    {
                        "Purchase order!C22": datetime.datetime.now().strftime("%m/%d/%Y"),
                        "Purchase order!A10": f"Invoice {To}",
                    })
            elif payments != 0 and balance == 0: #fully paid
                paidschoolsheets[names[i]] = tosheetID
                Sheets.write_values_to_sheet_from_dict(
                    tosheetID,
                    {
                        "Purchase order!C22": datetime.datetime.now().strftime("%m/%d/%Y"),
                        "Purchase order!A10": f"Invoice {To}",
                    })
            Display.display("Here is the new invoice: https://docs.google.com/spreadsheets/d/" + tosheetID )


    forfunctionlist = list(toeditsheets.keys())
    Display.display("You should manually edit these sheets:")
    for n in range (len(toeditsheets)):
        Display.display(forfunctionlist[n] + " - " + "https://docs.google.com/spreadsheets/d/" + str(toeditsheets[forfunctionlist[n]]))

    Display.display() #for readability
    forfunctionlist2 = list(paidschoolsheets.keys())
    Display.display("These schools have paid in full:")

    for i in range(len(paidschoolsheets)):
        Display.display(forfunctionlist2[i] + " - " + str(paidschoolsheets[forfunctionlist2[i]]))

elif Final == "y":
    for i in range(len(FolderIDs)):
        yearfolder = yearfolderids[i]
        if names[i] == "Santa Teresa High School":
            continue
        Display.display(f"Processing final invoice for {names[i]}...")
        fromsheetID = CloudStorageAPI.find_sheet_id_by_name_contains(yearfolder, "Invoice 3")
        if fromsheetID is None:
            Display.display("Could not find source sheet.")
            continue

        payments = int(Sheets.read_single_unformatted_cell(fromsheetID, "Purchase order!H33")) #type: ignore
        balance = int(Sheets.read_single_unformatted_cell(fromsheetID, "Purchase order!H36")) #type: ignore

        if payments != 0 and balance == 0:
            tosheetID = CloudStorageAPI.copy_drive_file(fromsheetID, fullyPaidInvoiceFolderID, f"Final Invoice - {names[i]}")
            Sheets.write_values_to_sheet_from_dict(
                tosheetID,
                {
                    "Purchase order!A10": "FINAL INVOICE",
                })
            Display.display("Paid" )
        elif payments != 0 and balance != 0:
            tosheetID = CloudStorageAPI.copy_drive_file(fromsheetID, partiallyPaidInvoiceFolderID, f"Final Invoice - {names[i]}")
            Sheets.write_values_to_sheet_from_dict(
                tosheetID,
                {
                    "Purchase order!A10": "FINAL INVOICE",
                })
            Display.display("Partially Paid")
        elif payments == 0 and balance >= 0:
            tosheetID = CloudStorageAPI.copy_drive_file(fromsheetID, unpaidInvoiceFolderID, f"Final Invoice - {names[i]}")
            Sheets.write_values_to_sheet_from_dict(
                tosheetID,
                {
                    "Purchase order!A10": "FINAL INVOICE",
                })
            Display.display(f"Unpaid")
        