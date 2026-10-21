import csv
from pathlib import Path
import sys
import os
import time
AUTOMATIONS_DIR = Path(__file__).resolve().parent.parent
if str(AUTOMATIONS_DIR) not in sys.path:
    sys.path.insert(0, str(AUTOMATIONS_DIR))
from dotenv import load_dotenv
from Infrastructure import DriveAPI
from Infrastructure import SheetAPI
from Infrastructure import DisplayClass
#These four are other .py files with the proper functions called here.

storage = DriveAPI()
SheetsAPI = SheetAPI()
Display = DisplayClass()
load_dotenv()

AttendingFolderID = os.getenv("AttendingFolderID")
YearText = os.getenv("YearText")
if not AttendingFolderID or not YearText:
    Display.display("No AttendingFolderID or YearText provided in the .env file. Please set them.")
    sys.exit(1)

data = [['Name', 'Balance', 'Comments']]
for school_name, school_folder_ID in storage.get_subfolders_as_dict(AttendingFolderID).items():
    yearfolder = storage.find_subfolder_id(school_folder_ID, YearText)
    if yearfolder is None:
        Display.display(f"Year folder not found for {school_name}. Skipping.")
        continue

    sheetID = storage.find_sheet_id_by_name_contains(yearfolder, f"Invoice - {school_name}")
    if sheetID is None:
        Display.display(f"Invoice sheet not found for {school_name}. Skipping.")
        continue

    if "Final Invoice" not in SheetsAPI.get_sheet_names(sheetID):
        Display.display(f"Final Invoice tab not found for {school_name}. Skipping.")
        continue

    balance, comments, name = SheetsAPI.read_cells(sheetID, ['Final Invoice!H36', 'Final Invoice!C38', 'Final Invoice!C16'])
    data.append([name, balance, comments])
    time.sleep(1)  # To avoid hitting API rate limits.

file_path = 'InvoiceData.csv'
# write the data to a CSV file
with open(file_path, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=',')
    # Write all rows at once
    writer.writerows(data)

Display.display(f"Data successfully written to {file_path}")
