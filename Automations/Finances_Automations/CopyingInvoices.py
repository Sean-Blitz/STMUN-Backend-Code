import os
import datetime
import sys
from pathlib import Path
AUTOMATIONS_DIR = Path(__file__).resolve().parent.parent
if str(AUTOMATIONS_DIR) not in sys.path:
    sys.path.insert(0, str(AUTOMATIONS_DIR))
from dotenv import load_dotenv
from Infrastructure import DriveAPI
from Infrastructure import SheetAPI
from Infrastructure import DisplayClass

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

Final = inputcheck(Display.take_text_input("Are you copying to final invoices? y/n"), ["y", "n"])

FolderIDs = CloudStorageAPI.get_subfolders_as_dict(AttendingFolderID)
names = list(FolderIDs.keys())
toeditsheets = {}
paidschoolsheets = {}
yearfolderids = []

def find_year_folder_id(school_name):
    yearfolder = CloudStorageAPI.find_subfolder_id(FolderIDs[school_name], YearText)
    if yearfolder is None:
        Display.display(f"Year folder not found for {school_name}. Please check the folder structure.")
    return yearfolder

if Final == "n":
    try:
        From = int(Display.take_text_input("Copying from which invoice? (1 or 2)"))
        To = int(Display.take_text_input("Copying to which invoice? (2 or 3)"))
    except ValueError:
        Display.display("Input error: invoice numbers must be whole numbers.")
        sys.exit()
    if From == To or From < 1 or From > 2 or To < 2 or To > 3:
        Display.display ("Input error.")
        sys.exit()

    cont = Display.take_text_input(f"The pre-condition for this is that Invoice {From} tabs are created for all schools. Ensure this and press y to continue. Continue? y/n")
    if cont != "y":
        Display.display("Exiting...")
        sys.exit()
    for i in range(len(names)):
        yearfolder = find_year_folder_id(names[i])
        if yearfolder is None:
            continue

        if inputcheck(Display.take_text_input(f"Processing {names[i]}... Continue? y/n"), ["y", "n"]) == "n":
            continue
        fromsheetID = CloudStorageAPI.find_sheet_id_by_name_contains(yearfolder, f"Invoice - {names[i]}")
        if fromsheetID is None:
            Display.display("Could not find source sheet.")
            continue

        try:
            payments = Sheets.read_single_unformatted_cell(fromsheetID, f"Invoice {From}!H33")
            balance = Sheets.read_single_unformatted_cell(fromsheetID, f"Invoice {From}!H36")
            balance = int(balance) if balance is not None else 0
            payments = int(payments) if payments is not None else 0
        except Exception as e:
            Display.display(f"Error reading cell values for {names[i]}: {e}")
            Display.display(f"Likely due to a missing Invoice {From} tab or non-numeric values. Please check the sheet and ensure Invoice {From} is created. Skipping this school.")
            continue
        
        Sheets.copy_sheet_tab_to_front(fromsheetID, f"Invoice {From}", new_sheet_name=f"Invoice {To}")

        if payments == 0: #unpaid.
            if From == 1 and To == 2:
                earlydelegates = Sheets.read_single_cell(fromsheetID, f"Invoice {From}!B28")
                if earlydelegates is not None:
                    earlydelegates = int(earlydelegates)
                Sheets.write_values_to_sheet_from_dict(
                    fromsheetID,
                    {
                        f"Invoice {To}!C22": datetime.datetime.now().strftime("%m/%d/%Y"),
                        f"Invoice {To}!B29": earlydelegates,
                        f"Invoice {To}!B28": "0",
                        f"Invoice {To}!A10": f"Invoice {To}",
                    }
                )
            elif From == 2 and To == 3:
                earlydelegates = Sheets.read_single_cell(fromsheetID, f"Invoice {From}!B28")
                earlydelegates = int(earlydelegates) if earlydelegates is not None else 0
                regulardelegates = Sheets.read_single_cell(fromsheetID, f"Invoice {From}!B29")
                regulardelegates = int(regulardelegates) if regulardelegates is not None else 0
                Sheets.write_values_to_sheet_from_dict(
                    fromsheetID,
                    {
                        f"Invoice {To}!C22": datetime.datetime.now().strftime("%m/%d/%Y"),
                        f"Invoice {To}!B30": regulardelegates + earlydelegates,
                        f"Invoice {To}!B28": "0",
                        f"Invoice {To}!B29": "0",
                        f"Invoice {To}!A10": f"Invoice {To}",
                    }
                )
        elif payments != 0 and balance != 0: #partially paid.
            toeditsheets[names[i]] = fromsheetID
            Sheets.write_values_to_sheet_from_dict(
                fromsheetID,
                {
                    f"Invoice {To}!C22": datetime.datetime.now().strftime("%m/%d/%Y"),
                    f"Invoice {To}!A10": f"Invoice {To}",
                })
        elif payments != 0 and balance == 0: #fully paid
            paidschoolsheets[names[i]] = fromsheetID
            Sheets.write_values_to_sheet_from_dict(
                fromsheetID,
                {
                    f"Invoice {To}!C22": datetime.datetime.now().strftime("%m/%d/%Y"),
                    f"Invoice {To}!A10": f"Invoice {To}",
                })
        Display.display("Here is the invoice: https://docs.google.com/spreadsheets/d/" + fromsheetID)


    forfunctionlist = list(toeditsheets.keys())
    Display.display("You should manually edit these sheets due to partial payment/decisions you need to make:")
    for n in range (len(toeditsheets)):
        Display.display(forfunctionlist[n] + " - " + "https://docs.google.com/spreadsheets/d/" + str(toeditsheets[forfunctionlist[n]]))

    Display.display() #for readability
    forfunctionlist2 = list(paidschoolsheets.keys())
    Display.display("These schools have paid in full:")

    for i in range(len(paidschoolsheets)):
        Display.display(forfunctionlist2[i] + " - " + str(paidschoolsheets[forfunctionlist2[i]]))

elif Final == "y":
    cont = Display.take_text_input("The pre-condition for this is that Invoice 3 is created for all schools. Ensure this and press y to continue. Continue? y/n")
    if cont == "y":
        Display.display("Continuing...")
    else:
        Display.display("Exiting...")
        sys.exit()
    for i in range(len(names)):
        if names[i] == "Santa Teresa High School":
            continue
        yearfolder = find_year_folder_id(names[i])
        if yearfolder is None: continue
        Display.display(f"Processing final invoice for {names[i]}...")

        fromsheetID = CloudStorageAPI.find_sheet_id_by_name_contains(yearfolder, f"Invoice - {names[i]}")
        if fromsheetID is None:
            Display.display("Could not find source sheet.")
            continue

        try:
            payments = int(Sheets.read_single_unformatted_cell(fromsheetID, "Invoice 3!H33")) #type: ignore
            balance = int(Sheets.read_single_unformatted_cell(fromsheetID, "Invoice 3!H36")) #type: ignore
        except Exception as e:
            Display.display(f"Error reading cell values for {names[i]}: {e}")
            Display.display("Likely due to missing Invoice 3 tab. Please check the sheet and ensure Invoice 3 is created. Skipping this school.")
            continue

        Sheets.copy_sheet_tab_to_front(fromsheetID, f"Invoice 3", new_sheet_name=f"Final Invoice")

        Sheets.write_values_to_sheet_from_dict(fromsheetID,{"Final Invoice!A10": "FINAL INVOICE",})

        if payments != 0 and balance == 0:
            Display.display("Paid" )
        elif payments != 0 and balance != 0:
            Display.display("Partially Paid")
        elif payments == 0 and balance >= 0:
            Display.display(f"Unpaid")
        