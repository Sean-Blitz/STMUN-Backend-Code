import sys
import csv
import os
import time
import secrets
from pathlib import Path

# Locate the root 'Automations' directory relative to this script file
# main.py is in Automations/main_app/main.py, so parent.parent points to Automations/
AUTOMATIONS_DIR = Path(__file__).resolve().parent.parent

# Inject the path into sys.path if it isn't already present
if str(AUTOMATIONS_DIR) not in sys.path:
    sys.path.insert(0, str(AUTOMATIONS_DIR))

"""
A few notes on using this: first of all, token file needs to be with the same google account as the script and sheet owner. Otherwise, script WON'T COPY OVER.
Also, the script ID is not the same as the sheet ID. The script ID is found in the template sheet: extensions, app script, settings, scroll down.
The top of the Google Apps Script contains the mappings of the master sheet to individual sheets. If you change either, you need to update that code.
"""
from typing import List, Any
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
from Infrastructure import SheetAPI
from Infrastructure import DriveAPI
from Infrastructure import AppScriptAPI

GDriveAPI = DriveAPI()
SheetsAPI = SheetAPI()
AppScript = AppScriptAPI()

#-------------- Controls ------------
print(f"For example, if the URL is https://docs.google.com/spreadsheets/d/1a2b3c4d5e6f7g8h9i0j/edit, the ID is 1a2b3c4d5e6f7g8h9i0j")
mastersheetID = input("What is the master sheet ID? Find it in the Google URL.")
mastersheet = f"docs.google.com/spreadsheets/d/{mastersheetID}"
template = "16T80NITxS63Q8ZzL9dl2tVOdMfKiYHJfxGpowbQA4CA"
# ScriptID = input("What is the script ID? Find it in the template sheet: extensions, app script, settings, scroll down.")
#------------------------------------

def generate_sheet(i, token):
    lastname, firstname, email = SheetsAPI.read_cells(mastersheetID, [f"Master Roster Contact Info!A{i+5}", f"Master Roster Contact Info!B{i+5}", f"Master Roster Contact Info!E{i+5}"])
    if email is None or email == "":
        print(f"Warning: No email found for {firstname} {lastname}. The sheet will be generated but not shared.")
    name = f"{firstname} {lastname}"
    print(f"Generating sheet for {name}...")
    newsheet = GDriveAPI.copy_drive_file(template, new_name=f"{name} - Individualized Dashboard")
    # AppScript.attach_script_to_sheet(newsheet, ScriptID)

    dictofvalues = {"G3": token}
    print(f"Writing token to sheet for {name}...")
    SheetsAPI.write_values_to_sheet_from_dict(newsheet, dictofvalues, value_input_option="USER_ENTERED")
    print(f"Finished sheet. Link: https://docs.google.com/spreadsheets/d/{newsheet}/edit")
    return newsheet, name, email

def export_lists_to_csv(list1: List[Any], list2: List[Any], filename: str = "output.csv") -> None:
    """
    Writes two lists into two separate columns of a CSV file.
    
    Parameters:
    list1 (list): Data for the first column.
    list2 (list): Data for the second column.
    filename (str): The name of the CSV file to create.
    """
    # Check that the two lists are the same length
    if len(list1) != len(list2):
        raise ValueError(
            f"Length mismatch: list1 has {len(list1)} items, but list2 has {len(list2)} items. "
            "Both lists must be the same length."
        )
    
    # Open the file and write the data
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # Optional: Add headers if you want them (e.g., Column 1, Column 2)
        # writer.writerow(["Column A", "Column B"])
        
        # zip() pairs the elements from both lists row by row
        for row in zip(list1, list2):
            writer.writerow(row)
            
    print(f"Successfully wrote data to {filename}")

def generate_for_person(number: int) -> None:
    token = secrets.token_hex(8)
    newsheet, name, email = generate_sheet(int(number)-5, token)
    SheetsAPI.write_values_to_sheet_from_dict(mastersheetID, {f"Master Roster Contact Info!I{int(number)}": token}, value_input_option="USER_ENTERED")
    if email is not None and email != "":
        while input("Share sheets? (y/n): ").strip().lower() != "y":
            print("Please type 'y' to continue. If you wish to quit, press Ctrl+C.")
        GDriveAPI.share_spreadsheet(newsheet, email, role="writer")
    else:
        print(f"Skipping sharing for sheet {newsheet} as no email is provided.")

def main():
    print("Warning: do not use this while the sheet is updating in ANY way!")
    action = input("Would you like to generate all sheets or add one person? (all/person/remaining persons): ").strip().lower()

    if action == "all":
        peoplecount = SheetsAPI.get_column_until_empty(mastersheetID, "Master Roster Contact Info", "A", 5)
        sheetstoshare = {}
        names = []
        tokens_to_push = {}
        for i in range(peoplecount):
            token = secrets.token_hex(8)
            newsheet, name, email = generate_sheet(i, token)
            sheetstoshare[newsheet] = email
            names.append(name)
            tokens_to_push[f"Master Roster Contact Info!I{i+5}"] = token
            time.sleep(2)

        SheetsAPI.write_values_to_sheet_from_dict(mastersheetID, tokens_to_push, value_input_option="USER_ENTERED")
        while input("Share sheets? (y/n): ").strip().lower() != "y":
            print("Please type 'y' to continue. If you wish to quit, press Ctrl+C.")
        for sheet in sheetstoshare:
            if sheetstoshare[sheet] is not None and sheetstoshare[sheet] != "":
                GDriveAPI.share_spreadsheet(sheet, sheetstoshare[sheet], role="writer")
            else:
                print(f"Skipping sharing for sheet {sheet} as no email is provided.")
        sheeturls = []
        for sheet in sheetstoshare:
            sheeturls.append(f"https://docs.google.com/spreadsheets/d/{sheet}/edit")
        export_lists_to_csv(names, sheeturls, filename="names_and_emails.csv")
    elif action == "person":
        number = input("Enter the person's row number (from Master Roster Contact Info): ").strip()
        token = secrets.token_hex(8)
        newsheet, name, email = generate_sheet(int(number)-5, token)
        SheetsAPI.write_values_to_sheet_from_dict(mastersheetID, {f"Master Roster Contact Info!I{int(number)}": token}, value_input_option="USER_ENTERED")
        if email is not None and email != "":
            while input("Share sheets? (y/n): ").strip().lower() != "y":
                print("Please type 'y' to continue. If you wish to quit, press Ctrl+C.")
            GDriveAPI.share_spreadsheet(newsheet, email, role="writer")
        else:
            print(f"Skipping sharing for sheet {newsheet} as no email is provided.")
    elif action == "remaining persons":
        rows = SheetsAPI.get_column_data(mastersheetID, "Master Roster Contact Info", "I", 5)
        tokenless_rows = [i for i, val in enumerate(rows, start=5) if not val or val == ""]
        if not tokenless_rows:
            print("All persons already have tokens. No remaining persons to generate sheets for.")
            return
        for row in tokenless_rows:
            generate_for_person(row)
            time.sleep(2)  # Optional: Add a small delay to avoid overwhelming the API

    else:
        print("Invalid input. Please enter 'all' or 'person'.")

if __name__ == "__main__":
    main()

