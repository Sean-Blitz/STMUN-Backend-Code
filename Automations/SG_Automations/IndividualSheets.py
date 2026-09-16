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
Note that those without any email in the sheet will not even be generated.
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
template = "13JolO1XDGI1bqeT-vwQkPrileKMaLO7MORYyKtHVZCQ"
# ScriptID = input("What is the script ID? Find it in the template sheet: extensions, app script, settings, scroll down.")
#------------------------------------

def generate_sheet(token, name):
    print(f"Generating sheet for {name}...")
    newsheet = GDriveAPI.copy_drive_file(template, new_name=f"{name} - Individualized Dashboard")
    # AppScript.attach_script_to_sheet(newsheet, ScriptID)

    dictofvalues = {"G3": token}
    print(f"Writing token to sheet for {name}...")
    SheetsAPI.write_values_to_sheet_from_dict(newsheet, dictofvalues, value_input_option="USER_ENTERED")
    print(f"Finished sheet. Link: https://docs.google.com/spreadsheets/d/{newsheet}/edit")
    return newsheet, name

def generate_for_person(number: int):
    token = secrets.token_hex(8)
    first_name = SheetsAPI.read_single_cell(mastersheetID, f"Master Roster Contact Info!B{int(number)}")
    last_name = SheetsAPI.read_single_cell(mastersheetID, f"Master Roster Contact Info!A{int(number)}")
    name = f"{first_name} {last_name}"
    newsheet, name = generate_sheet(token, name)
    email = SheetsAPI.read_single_cell(mastersheetID, f"Master Roster Contact Info!E{int(number)}")
    SheetsAPI.write_values_to_sheet_from_dict(mastersheetID, {f"Master Roster Contact Info!I{int(number)}": token}, value_input_option="USER_ENTERED")

    return newsheet, name, email

def main():
    print("Warning: do not use this while the sheet is updating in ANY way!")
    action = input("Would you like to generate all sheets or add one person? (all/person/remaining persons): ").strip().lower()

    if action == "all":
        lastnames = SheetsAPI.get_column_data(mastersheetID, "Master Roster Contact Info", "A", 5)
        firstnames = SheetsAPI.get_column_data(mastersheetID, "Master Roster Contact Info", "B", 5)
        names = [f"{first} {last}" for first, last in zip(firstnames, lastnames)]
        emails = SheetsAPI.get_column_data(mastersheetID, "Master Roster Contact Info", "E", 5)
        count = min(len(lastnames), len(firstnames), len(names), len(emails))
        
        sheetstoshare = {}
        tokens_to_push = {}
        for i in range(count):
            if emails[i] is None or emails[i] == "":
                print(f"No email found for {firstnames[i]} {lastnames[i]}. Skipping this person.")
                continue  # Skip this iteration if email is missing, as nothing will be shared anyways
            token = secrets.token_hex(8)
            newsheet, name = generate_sheet(token, names[i])
            sheetstoshare[newsheet] = emails[i]
            tokens_to_push[f"Master Roster Contact Info!I{i+5}"] = token
            time.sleep(1)

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
    elif action == "person":
        number = input("What is the row number of the person in the master sheet? (Starting from 5): ").strip()
        newsheet, name, email = generate_for_person(int(number))
        if email is not None and email != "":
            while input("Share sheets? (y/n): ").strip().lower() != "y":
                print("Please type 'y' to continue. If you wish to quit, press Ctrl+C.")
            GDriveAPI.share_spreadsheet(newsheet, email, role="writer")
        else:
            print(f"Skipping sharing for sheet {newsheet} as no email is provided.")
    elif action == "remaining persons":
        rows = SheetsAPI.get_column_data(mastersheetID, "Master Roster Contact Info", "I", 5)
        tokenless_indexes = [i for i, val in enumerate(rows) if not val or val == ""]
        if not tokenless_indexes:
            print("All persons already have tokens. No remaining persons to generate sheets for.")
            return

        emails = SheetsAPI.get_column_data(mastersheetID, "Master Roster Contact Info", "E", 5)
        lastnames = SheetsAPI.get_column_data(mastersheetID, "Master Roster Contact Info", "A", 5)
        firstnames = SheetsAPI.get_column_data(mastersheetID, "Master Roster Contact Info", "B", 5)
        names = [f"{first} {last}" for first, last in zip(firstnames, lastnames)]
        sheetstoshare = {}
        tokens = {}
        for index in tokenless_indexes:
            if emails[index] is None or emails[index] == "":
                print(f"No email found for {names[index]}. Skipping this person.")
                continue  # Skip this iteration if email is missing, as nothing will be shared anyways
            token = secrets.token_hex(8)
            newsheet, name = generate_sheet(token, names[index])
            sheetstoshare[newsheet] = emails[index]
            tokens[f"Master Roster Contact Info!I{index + 5}"] = token
            time.sleep(1)
        SheetsAPI.write_values_to_sheet_from_dict(mastersheetID, tokens, value_input_option="USER_ENTERED")

        while input("Share sheets? (y/n): ").strip().lower() != "y":
            print("Please type 'y' to continue. If you wish to quit, press Ctrl+C.")
        for newsheet, email in sheetstoshare.items():
            if email is not None and email != "":
                GDriveAPI.share_spreadsheet(newsheet, email, role="writer")

    else:
        print("Invalid input. Please enter 'all' or 'person'.")

if __name__ == "__main__":
    main()

