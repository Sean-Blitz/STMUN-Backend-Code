import questionary
import sys
import csv
import os
import time

def select_school_to_assign(unassigned_schools):
    """
    Takes a list of unassigned schools and prompts the user to select one
    using an interactive arrow-key CLI menu.
    
    Arguments:
    unassigned_schools (list): List of school names that need assignments.
    
    Returns:
    str: The name of the school chosen by the user.
    """
    if not unassigned_schools:
        print("\n All schools have been assigned! Nothing left to process.")
        sys.exit(0)
        
    print("\n" + "="*40)
    print("SCVMUN ASSIGNMENT ENGINE - PENDING SCHOOLS")
    print("="*40)
    
    selected = questionary.select(
        "Select a school to begin their assignment process:",
        choices=unassigned_schools,
        pointer="-->",               
        use_indicator=True          
    ).ask()
    
    return selected

def get_unassigned_schools(live_schools, csv_filepath):
    """Returns schools from the sheet that aren't in the local CSV."""
    assigned = set()
    if os.path.exists(csv_filepath):
        with open(csv_filepath, mode='r', encoding='utf-8') as f:
            csvdata = csv.reader(f)
            for row in csvdata:
                if row: 
                    assigned.add(row[0].strip())
    return [s for s in live_schools if s.strip() not in assigned]
#how does this function work? Essentially, it checks if CSV exists, opens it safely, reads row by row checking first column,
#strips whitespace, appends it to the set, and uses the fact that sets already have uniqueness to compare with live_schools.

def backup_sheet_to_csv(sheet_api, spreadsheet_id, range_name, filename="unassigned_backup.csv"):
    """
    Downloads a specific range from Google Sheets to a local CSV for safety 
    using the official Google Sheets API v4.
    """
    request = sheet_api.values().get(
        spreadsheetId=spreadsheet_id, 
        range=range_name
    )
    response = request.execute()
    all_data = response.get('values', [])
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(all_data)
    
    print(f"Backup successfully saved to {filename}")

def assign_committee(CommitteeTypeSelection, Indices: dict, data: tuple, finalassignments: dict, iterator, i, singleIndices: dict, selectedSchool, committeeCount: tuple):
    """
    Assigns delegates based on parameter of CommitteeTypeSelection, which is a string for either "GA", "Specialized", or "Crisis".
    """
    #sets up variables
    if CommitteeTypeSelection == "GA":
        singleIndices = singleIndices["ga"]
        committeeCount = committeeCount[0]
    elif CommitteeTypeSelection == "Specialized":
        singleIndices = singleIndices["specialized"]
        committeeCount = committeeCount[1]
    elif CommitteeTypeSelection == "Crisis":
        singleIndices = singleIndices["crisis"]
        committeeCount = committeeCount[2]
    else:
        print("Error in Committee Type Selection.")
        return
    names, percentages, double, spots, Committeetype = data

    row = min(Indices, key = lambda x: percentages[x]) #find the lowest percentage GA committee
    committee = names[row]
    if double[row].lower() == "true" and committeeCount - iterator > 1: #if double delegate committee and enough GA assignmentspots left.
        finalassignments[f"{selectedSchool} - #{i+1}"] = [committee, Committeetype[row], ""]
        finalassignments[f"{selectedSchool} - #{i+2}"] = [committee, Committeetype[row], ""]
        percentages[row] += 2 * (100/spots[row]) #update percentage as if two delegates were added.
        i = i + 2 #skip the next delegate since we just assigned it.
        iterator = iterator + 2
    elif double[row].lower() == "true" and committeeCount - iterator == 1: #if double delegate commmittee and not enough GA assignment spots left
        row = min(singleIndices, key = lambda x: percentages[x]) #only scans single del GA's
        committee = names[row]
        finalassignments[f"{selectedSchool} - #{i+1}"] = [committee, Committeetype[row], ""]
        percentages[names.index(committee)] += (100/spots[names.index(committee)])
        i = i +1
        iterator = iterator + 1
    elif double[row].lower() == "false": #if single delegate committee
        finalassignments[f"{selectedSchool} - #{i+1}"] = [committee, Committeetype[row], ""]
        percentages[row] += (100/spots[row])
        i = i + 1
        iterator = iterator + 1
    elif iterator == 0:
        print("\033[K", end="")
        print("Error in assignment logic.")
        if input("Continue? (y/n)") == "y":
            i = i + 1
            iterator = iterator + 1
        elif input("Continue? (y/n)") == "n":
            sys.exit(0)
    else:
        print("Error in making committees for GA at values of i and iterator:", i, iterator)
        i = i + 1
    return finalassignments, i, percentages, iterator

def append_to_csv(filename, row_data):
    """
    Appends a single row of data to a specified CSV file.
    Automatically handles comma-escaping and structural formatting.
    
    Parameters:
    filename (str): The name or path of the CSV file (e.g., 'assignments_log.csv').
    row_data (list): A list of items representing the cells of the row (e.g., ['School A - #1', 'DISEC', 'Bolivia']).
    """
    # Opening with mode='a' enables appending without wiping existing data.
    # newline='' prevents standard Windows/Unix double-spacing bugs.
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(row_data)

#testing = {"1": ["DISEC", "GA", ""], "2": ["SOCHUM", "GA", ""], "3": ["UNHRC", "Specialized", ""]}
#add_assignments(testing, suggestions_matrix=[["USA", "China", "Russia"], ["Germany", "France", "UK"], ["Saudi Arabia", "South Africa", "Brazil"]])
#add_assignments(testing)
#print(testing)

#awards won should be calculated as a percentage of total participation.
