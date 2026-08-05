import csv
import os
import time
from typing import List, Any
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
from ..Infrastructure import SheetAPI
from ..Infrastructure import DriveAPI

GDriveAPI = DriveAPI()
SheetsAPI = SheetAPI()

#-------------- Controls ------------
mastersheetID = input("What is the master sheet ID? Find it in the Google URL.")
mastersheet = f"docs.google.com/spreadsheets/d/{mastersheetID}"
template = "16T80NITxS63Q8ZzL9dl2tVOdMfKiYHJfxGpowbQA4CA"
#------------------------------------

def write_cell_value(letter, number, P = None, TD = None, A = None, Att = None, F=None, awd=None, info=None, T=None):
    #P is Payment 1 or 2. TD is total due. A is for conference attendance. Att is for meeting attendance. F is for finance. T is for training attendance.
    if P != None:
        return f'=IF(ISBLANK(IMPORTRANGE("{mastersheet}", "Fundraising/Deposits!{letter}{number}")), "$0", IMPORTRANGE("{mastersheet}", "Fundraising/Deposits!{letter}{number}"))'
    if TD != None:
        return f'=IF(IMPORTRANGE("{mastersheet}", "Fundraising/Deposits!{letter}{number}")="", "N/A", IMPORTRANGE("{mastersheet}", "Fundraising/Deposits!{letter}{number}"))'
    if A != None:
        return f'=IF(ISBLANK(IMPORTRANGE("{mastersheet}", "Conference Attd/Award!{letter}{number}")), FALSE, TRUE)'
    if Att != None:
        return f'=IF(IMPORTRANGE("{mastersheet}", "Thursday Meeting Attd!{letter}{number+1}")="", FALSE, TRUE)'
    if F != None:
        return f'=IF(ISBLANK(IMPORTRANGE("{mastersheet}", "Fundraising/Deposits!{letter}{number}")), "$-", IMPORTRANGE("{mastersheet}", "Fundraising/Deposits!{letter}{number}"))'
    if awd != None:
        return f'=IMPORTRANGE("{mastersheet}", "Conference Attd/Award!{letter}{number}")'
    if info != None:
        return f'=IMPORTRANGE("{mastersheet}", "Master Roster Contact Info (EDIT)!{letter}{number}")'
    if T != None:
        return f'=IF(ISBLANK(IMPORTRANGE("{mastersheet}", "Mock/Training Attd!{letter}{number}")), FALSE, TRUE)'

def generate_sheet(i):
    lastname = SheetsAPI.read_single_cell(mastersheetID, f"Master Roster Contact Info (EDIT)!A{i+4}")
    firstname = SheetsAPI.read_single_cell(mastersheetID, f"Master Roster Contact Info (EDIT)!B{i+4}")
    name = f"{firstname} {lastname}"
    print(f"Generating sheet for {name}...")
    newsheet = GDriveAPI.copy_drive_file(template, new_name=f"{name} - Individualized Dashboard")

    dictofvalues = {
        "B3": name,
        "B4": write_cell_value("E", i+4, info=1),
        "E3": write_cell_value("D", i+4, info=1),
        "E4": write_cell_value("C", i+4, info=1),
        "B5": f'=IMPORTRANGE("{mastersheet}", "Overall Total Points!D{i+4}")',
        "A9": write_cell_value("E", i+4, F=1),
        "B9": write_cell_value("F", i+4, F=1),
        "C9": write_cell_value("G", i+4, F=1),
        "D9": write_cell_value("H", i+4, F=1),
        "E9": write_cell_value("I", i+4, F=1),
        "F9": write_cell_value("J", i+4, F=1),
        "G9": write_cell_value("K", i+4, F=1),
        "B13": write_cell_value("O", i+4, P=1),
        "C13": write_cell_value("P", i+4, P=1),
        "D13": write_cell_value("Q", i+4, TD=1),
        "B14": write_cell_value("R", i+4, P=1),
        "C14": write_cell_value("S", i+4, P=1),
        "D14": write_cell_value("T", i+4, TD=1),
        "B15": write_cell_value("U", i+4, P=1),
        "C15": write_cell_value("V", i+4, P=1),
        "D15": write_cell_value("W", i+4, TD=1),
        "B16": write_cell_value("X", i+4, P=1),
        "B17": write_cell_value("Y", i+4, P=1),
        "C17": write_cell_value("Z", i+4, P=1),
        "D17": write_cell_value("AA", i+4, TD=1),
        "B18": write_cell_value("AB", i+4, P=1),
        "C18": write_cell_value("AC", i+4, P=1),
        "D18": write_cell_value("AD", i+4, TD=1),
        "B19": write_cell_value("AE", i+4, P=1),
        "C19": write_cell_value("AF", i+4, P=1),
        "D19": write_cell_value("AG", i+4, TD=1),
        "B20": write_cell_value("AH", i+4, P=1),
        "C20": write_cell_value("AI", i+4, P=1),
        "D20": write_cell_value("AJ", i+4, TD=1),
        "B24": write_cell_value("G", i+4, A=1),
        "B25": write_cell_value("I", i+4, A=1),
        "B26": write_cell_value("K", i+4, A=1),
        "B27": write_cell_value("O", i+4, A=1),
        "B28": write_cell_value("S", i+4, A=1),
        "B29": write_cell_value("U", i+4, A=1),
        "B30": write_cell_value("Q", i+4, A=1),
        "B31": write_cell_value("W", i+4, A=1),
        "C24": write_cell_value("H", i+4, awd=1),
        "C25": write_cell_value("J", i+4, awd=1),
        "C26": write_cell_value("L", i+4, awd=1),
        "C27": write_cell_value("P", i+4, awd=1),
        "C28": write_cell_value("T", i+4, awd=1),
        "C29": write_cell_value("V", i+4, awd=1),
        "C30": write_cell_value("R", i+4, awd=1),
        "C31": write_cell_value("X", i+4, awd=1),
        "J2": write_cell_value("E", i+4, Att=1),
        "J3": write_cell_value("F", i+4, Att=1),
        "J4": write_cell_value("G", i+4, Att=1),
        "J5": write_cell_value("H", i+4, Att=1),
        "J6": write_cell_value("I", i+4, Att=1),
        "J7": write_cell_value("J", i+4, Att=1),
        "J8": write_cell_value("K", i+4, Att=1),
        "J9": write_cell_value("L", i+4, Att=1),
        "J10": write_cell_value("M", i+4, Att=1),
        "J11": write_cell_value("N", i+4, Att=1),
        "J12": write_cell_value("O", i+4, Att=1),
        "J13": write_cell_value("P", i+4, Att=1),
        "J14": write_cell_value("Q", i+4, Att=1),
        "J15": write_cell_value("R", i+4, Att=1),
        "J16": write_cell_value("S", i+4, Att=1),
        "J17": write_cell_value("T", i+4, Att=1),
        "J18": write_cell_value("U", i+4, Att=1),
        "J19": write_cell_value("V", i+4, Att=1),
        "J20": write_cell_value("W", i+4, Att=1),
        "J21": write_cell_value("X", i+4, Att=1),
        "J22": write_cell_value("Y", i+4, Att=1),
        "J23": write_cell_value("Z", i+4, Att=1),
        "J24": write_cell_value("AA", i+4, Att=1),
        "J25": write_cell_value("AB", i+4, Att=1),
        "J26": write_cell_value("AC", i+4, Att=1),
        "J27": write_cell_value("AD", i+4, Att=1),
        "J28": write_cell_value("AE", i+4, Att=1),
        "J29": write_cell_value("AF", i+4, Att=1),
        "J30": write_cell_value("AG", i+4, Att=1),
        "J31": write_cell_value("AH", i+4, Att=1),
        "J32": write_cell_value("AI", i+4, Att=1),
        "J33": write_cell_value("AJ", i+4, Att=1),
        "J34": write_cell_value("AK", i+4, Att=1),
        "J35": write_cell_value("AL", i+4, Att=1),
        "J36": write_cell_value("AM", i+4, Att=1),
        "J37": write_cell_value("AN", i+4, Att=1),
        "J38": write_cell_value("AO", i+4, Att=1),
        "J39": write_cell_value("AP", i+4, Att=1),
        "J40": write_cell_value("AQ", i+4, Att=1),
        "M3": write_cell_value("D", i+4, T=1),
        "M4": write_cell_value("E", i+4, T=1),
        "M5": write_cell_value("F", i+4, T=1),
        "M6": write_cell_value("G", i+4, T=1),
        "M7": write_cell_value("H", i+4, T=1),
        "M8": write_cell_value("I", i+4, T=1),
        "M9": write_cell_value("J", i+4, T=1),
        "M10": write_cell_value("K", i+4, T=1),
        "M11": write_cell_value("L", i+4, T=1),
        "M12": write_cell_value("M", i+4, T=1),
        "M13": write_cell_value("N", i+4, T=1),
        "M14": write_cell_value("O", i+4, T=1),
        "M15": write_cell_value("P", i+4, T=1),
        "M16": write_cell_value("Q", i+4, T=1),
        "M17": write_cell_value("R", i+4, T=1),
        "M18": write_cell_value("S", i+4, T=1),
        "M19": write_cell_value("T", i+4, T=1),
        "M20": write_cell_value("U", i+4, T=1),
        "M21": write_cell_value("V", i+4, T=1),
        "M22": write_cell_value("W", i+4, T=1),
        "M23": write_cell_value("X", i+4, T=1),
        "M24": write_cell_value("Y", i+4, T=1),
        "M25": write_cell_value("Z", i+4, T=1),
        "M26": write_cell_value("AA", i+4, T=1),
        "M27": write_cell_value("AB", i+4, T=1),
        "M28": write_cell_value("AC", i+4, T=1),
        "M29": write_cell_value("AD", i+4, T=1),
        "M30": write_cell_value("AE", i+4, T=1),
        "M31": write_cell_value("AF", i+4, T=1),
        "M32": write_cell_value("AG", i+4, T=1),
        "M33": write_cell_value("AH", i+4, T=1),
        "M34": write_cell_value("AI", i+4, T=1),
        "M35": write_cell_value("AJ", i+4, T=1),
        "M36": write_cell_value("AK", i+4, T=1),
        "M37": write_cell_value("AL", i+4, T=1),
        "M38": write_cell_value("AM", i+4, T=1),
    }
    print(f"Writing values to sheet for {name}...")
    SheetsAPI.write_values_to_sheet_from_dict(newsheet, dictofvalues, value_input_option="USER_ENTERED")
    print(f"Finished sheet. Link: https://docs.google.com/spreadsheets/d/{newsheet}/edit")
    return newsheet, name

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

def main():
    print("Warning: do not use this while the sheet is updating in ANY way!")
    action = input("Would you like to generate all sheets or add one person? (all/person): ").strip().lower()

    if action == "all":
        peoplecount = SheetsAPI.get_column_until_empty(mastersheetID, "Master Roster Contact Info (EDIT)", "A", 4)
        sheetstoshare = {}
        names = []
        for i in range(peoplecount):
            newsheet, name = generate_sheet(i)
            email = SheetsAPI.read_single_cell(mastersheetID, f"Master Roster Contact Info (EDIT)!E{i+4}")
            sheetstoshare[newsheet] = email
            names.append(name)
            time.sleep(5)
        print("Please make sure you have gone through all the sheets and enabled connections!")
        for sheet in sheetstoshare:
            GDriveAPI.share_spreadsheet(sheet, sheetstoshare[sheet], role="commenter")
        sheeturls = []
        for sheet in sheetstoshare:
            sheeturls.append(f"https://docs.google.com/spreadsheets/d/{sheet}/edit")
        export_lists_to_csv(names, sheeturls, filename="names_and_emails.csv")
    elif action == "person":
        number = input("Enter the person's row number (from Master Roster Contact Info): ").strip()
        newsheet, name = generate_sheet(int(number)-4)
        email = SheetsAPI.read_single_cell(mastersheetID, f"Master Roster Contact Info (EDIT)!E{int(number)}")
        GDriveAPI.share_spreadsheet(newsheet, email, role="commenter")
    else:
        print("Invalid input. Please enter 'all' or 'person'.")

if __name__ == "__main__":
    main()