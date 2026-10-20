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
if fullyPaidInvoiceFolderID is None or partiallyPaidInvoiceFolderID is None or unpaidInvoiceFolderID is None:
    Display.display("One or more of the folder IDs for final invoices (fullyPaidInvoiceFolderID, partiallyPaidInvoiceFolderID, unpaidInvoiceFolderID) are not set in the environment variables. Please set them in your .env file.")
    sys.exit(1)
#-------------------------------------------------------

def inputcheck(input_text, valid):
    input_text = input_text.strip().lower()
    while input_text not in valid:
        input_text = Display.take_text_input("Invalid input. " + "Continue? y/n").strip().lower()
    return input_text

Final = inputcheck(Display.take_text_input("Are you copying to final invoices? y/n"), ["y", "n"])

FolderIDs = CloudStorageAPI.get_subfolders_as_dict(AttendingFolderID)
names = list(FolderIDs.keys())
toeditsheets = {}
paidschoolsheets = {}

def find_year_folder_id(school_name):
    yearfolder = CloudStorageAPI.find_subfolder_id(FolderIDs[school_name], YearText)
    if yearfolder is None:
        Display.display(f"Year folder not found for {school_name}. Please check the folder structure.")
    return yearfolder

def display_sheets_needing_edits():
    Display.display("You should manually edit these sheets due to partial payment/decisions you need to make:")
    for school_name, sheet_id in toeditsheets.items():
        Display.display(f"{school_name} - https://docs.google.com/spreadsheets/d/{sheet_id}")

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
    if cont.strip().lower() != "y":
        Display.display("Exiting...")
        sys.exit()
    for school_name in names:
        yearfolder = find_year_folder_id(school_name)
        if yearfolder is None:
            continue

        if inputcheck(Display.take_text_input(f"Processing {school_name}... Continue? y/n"), ["y", "n"]) == "n":
            continue
        fromsheetID = CloudStorageAPI.find_sheet_id_by_name_contains(yearfolder, f"Invoice - {school_name}")
        if fromsheetID is None:
            Display.display(f"Could not find source sheet for {school_name}.")
            continue

        from_tab = f"Invoice {From}"
        to_tab = f"Invoice {To}"
        sheet_names = Sheets.get_sheet_names(fromsheetID)
        if from_tab not in sheet_names:
            Display.display(f"{school_name}: skipped because {from_tab} is missing. Added to the manual-edit list.")
            toeditsheets[school_name] = fromsheetID
            continue
        if to_tab in sheet_names:
            Display.display(f"{school_name}: skipped because {to_tab} already exists. Added to the manual-edit list.")
            continue

        try:
            payments, balance = Sheets.read_cells(fromsheetID, [f"{from_tab}!H33", f"{from_tab}!H36"], value_render_option="UNFORMATTED_VALUE")
            balance = int(balance) if balance is not None else 0
            payments = int(payments) if payments is not None else 0
        except Exception as e:
            Display.display(f"Error reading cell values for {school_name}: {e}")
            Display.display(f"Likely due to a missing {from_tab} tab or non-numeric values. Skipping this school.")
            continue

        Sheets.copy_sheet_tab_to_front(fromsheetID, from_tab, new_sheet_name=to_tab)

        if payments == 0: #unpaid.
            if From == 1 and To == 2:
                earlydelegates = Sheets.read_single_cell(fromsheetID, f"{from_tab}!B28")
                if earlydelegates is not None:
                    earlydelegates = int(earlydelegates)
                Sheets.write_values_to_sheet_from_dict(
                    fromsheetID,
                    {
                        f"{to_tab}!C22": datetime.datetime.now().strftime("%m/%d/%Y"),
                        f"{to_tab}!B29": earlydelegates,
                        f"{to_tab}!B28": "0",
                        f"{to_tab}!A10": to_tab,
                    }
                )
            elif From == 2 and To == 3:
                earlydelegates = Sheets.read_single_cell(fromsheetID, f"{from_tab}!B28")
                earlydelegates = int(earlydelegates) if earlydelegates is not None else 0
                regulardelegates = Sheets.read_single_cell(fromsheetID, f"{from_tab}!B29")
                regulardelegates = int(regulardelegates) if regulardelegates is not None else 0
                Sheets.write_values_to_sheet_from_dict(
                    fromsheetID,
                    {
                        f"{to_tab}!C22": datetime.datetime.now().strftime("%m/%d/%Y"),
                        f"{to_tab}!B30": regulardelegates + earlydelegates,
                        f"{to_tab}!B28": "0",
                        f"{to_tab}!B29": "0",
                        f"{to_tab}!A10": to_tab,
                    }
                )
        elif payments != 0 and balance != 0: #partially paid.
            toeditsheets[school_name] = fromsheetID
            Sheets.write_values_to_sheet_from_dict(
                fromsheetID,
                {
                    f"{to_tab}!C22": datetime.datetime.now().strftime("%m/%d/%Y"),
                    f"{to_tab}!A10": to_tab,
                })
        elif payments != 0 and balance == 0: #fully paid
            paidschoolsheets[school_name] = fromsheetID
            Sheets.write_values_to_sheet_from_dict(
                fromsheetID,
                {
                    f"{to_tab}!C22": datetime.datetime.now().strftime("%m/%d/%Y"),
                    f"{to_tab}!A10": to_tab,
                })
        Display.display(f"Here is the invoice: https://docs.google.com/spreadsheets/d/{fromsheetID}")


    display_sheets_needing_edits()

    Display.display() #for readability
    Display.display("These schools have paid in full:")
    for school_name, sheet_id in paidschoolsheets.items():
        Display.display(f"{school_name} - {sheet_id}")

elif Final == "y":
    cont = Display.take_text_input("The pre-condition for this is that Invoice 3 is created for all schools. Ensure this and press y to continue. Continue? y/n").strip().lower()
    if cont == "y":
        Display.display("Continuing...")
    else:
        Display.display("Exiting...")
        sys.exit()
    for school_name in names:
        if school_name == "Santa Teresa High School":
            continue
        yearfolder = find_year_folder_id(school_name)
        if yearfolder is None: continue
        Display.display(f"Processing final invoice for {school_name}...")

        fromsheetID = CloudStorageAPI.find_sheet_id_by_name_contains(yearfolder, f"Invoice - {school_name}")
        if fromsheetID is None:
            Display.display(f"Could not find source sheet for {school_name}.")
            continue

        sheet_names = Sheets.get_sheet_names(fromsheetID)
        if "Invoice 3" not in sheet_names or "Final Invoice" in sheet_names:
            Display.display(f"{school_name}: skipped because Invoice 3 is missing or Final Invoice already exists. Added to the manual-edit list.")
            toeditsheets[school_name] = fromsheetID
            continue

        try:
            payments, balance = Sheets.read_cells(fromsheetID, ["Invoice 3!H33", "Invoice 3!H36"], value_render_option="UNFORMATTED_VALUE")
            payments = int(payments) if payments is not None else 0
            balance = int(balance) if balance is not None else 0
        except Exception as e:
            Display.display(f"Error reading cell values for {school_name}: {e}")
            Display.display("Likely due to missing Invoice 3 tab. Please check the sheet and ensure Invoice 3 is created. Skipping this school.")
            continue

        Sheets.copy_sheet_tab_to_front(fromsheetID, "Invoice 3", new_sheet_name="Final Invoice")

        Sheets.write_values_to_sheet_from_dict(fromsheetID,{"Final Invoice!A10": "FINAL INVOICE",})

        if payments != 0 and balance == 0:
            CloudStorageAPI.copy_drive_file(fromsheetID, fullyPaidInvoiceFolderID, f"Final Invoice - {school_name}")
            Display.display("Paid")
        elif payments != 0 and balance != 0:
            CloudStorageAPI.copy_drive_file(fromsheetID, partiallyPaidInvoiceFolderID, f"Final Invoice - {school_name}")
            Display.display("Partially Paid")
        elif payments == 0 and balance >= 0:
            CloudStorageAPI.copy_drive_file(fromsheetID, unpaidInvoiceFolderID, f"Final Invoice - {school_name}")
            Display.display("Unpaid")

    display_sheets_needing_edits()
        