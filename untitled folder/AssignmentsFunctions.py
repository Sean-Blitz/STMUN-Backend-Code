import questionary
import sys
import csv
import time
import os

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
    print("  SCVMUN ASSIGNMENT ENGINE - PENDING SCHOOLS")
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

def find_lowest_pct_committee(committees_data, c_type="GA", req_double=False, req_spots=1):
    """Greedy algorithm: Finds the committee of requested type with lowest % full."""
    eligible = []
    for name, data in committees_data.items():
        if data['type'] == c_type and data['is_double'] == req_double:
            if (data['capacity'] - data['filled']) >= req_spots:
                eligible.append((name, data['pct']))
    
    if not eligible:
        return None
    return min(eligible, key=lambda x: x[1])[0]

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

#awards won should be calculated as a percentage of total participation.