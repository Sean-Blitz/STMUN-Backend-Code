import csv
import os
import time
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
from Automations.Infrastructure import DriveAPI
from Automations.Infrastructure import SheetAPI
#These four are other .py files with the proper functions called here.

storage = DriveAPI()
SheetsAPI = SheetAPI()

#-------------------------------- Main Script ----------------------------#
folderID = ['1HEfiWYpQKMCVeRheuj7fo0cUmZ6Rh6vA']
#Change folderIDs from year to year.

for i in range(len(folderID)): #each folder (technically only one right now. Can modify above to scan more.)
    allsheetIDs = storage.list_google_sheet_ids(folderID[i])
    balance = []
    comments = []
    name = []
    data = [['Name', 'Balance', 'Comments']]
    for j in range(len(allsheetIDs)): #each sheet
        sheetID = allsheetIDs[j]
        cell_values = SheetsAPI.read_cells(sheetID, ['Purchase order!H36', 'Purchase order!C38', 'Purchase order!C16'])
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