import questionary
import sys
import sheetFunctions
import csv
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

def confirm_committees(finalassignments, GA_Names, Spec_Names, Crisis_Names, Double_Committees):
    """
    Launches an interactive Questionary interface allowing users to browse 
    delegates and overwrite their committee assignments in RAM.
    """
    while True:
        # 1. Construct a clean list of choices for Questionary
        # format: "#1: DISEC (GA)"
        menu_choices = []
        for delegate, details in finalassignments.items():
            current_committee = details[0]
            committee_type = details[1]
            choice_text = f"#{delegate}: {current_committee} ({committee_type})"
            menu_choices.append(choice_text)
            
        # Add a clear exit option at the bottom of the list
        menu_choices.append("Save and Exit")

        # 2. Render the primary navigation menu
        selected_choice = questionary.select(
            "Select a delegate to modify their assignment:",
            choices=menu_choices
        ).ask()

        # Handle the break condition
        if selected_choice == "Save and Exit" or selected_choice is None:
            print("Exiting modification menu...")
            break

        # 3. Parse the delegate name back out of the selected string
        # Split by the colon to isolate "School - #1"
        #delegate_key = selected_choice.split("-")[1].replace("#", "").strip()
        delegate_key = selected_choice.split(":")[0].strip() # This gets the "#1" part, but we want "School - #1"
        if delegate_key.startswith('#'):
        # Check if the hashtag belongs there (like the delegate number) 
        # or if it's an accidental duplicate/prefix on the school name.
        # If it's a prefix on the whole string, remove it:
            delegate_key = delegate_key[1:]
        current_assignment = finalassignments[delegate_key][0]

        # 4. Trigger the manual overwrite prompt
        new_committee = questionary.text(
            f"Enter new committee for {delegate_key} (Current: {current_assignment}):",
            default=current_assignment # Pre-fills the line so they can type over it
        ).ask()

        # 5. Update the master dictionary state in RAM
        if new_committee and new_committee.strip() != current_assignment:
            if new_committee in GA_Names and finalassignments[delegate_key][1].lower() == "ga":
                finalassignments[delegate_key][0] = new_committee.strip()
            elif new_committee in Spec_Names and finalassignments[delegate_key][1].lower() == "specialized":
                finalassignments[delegate_key][0] = new_committee.strip()
            elif new_committee in Crisis_Names and finalassignments[delegate_key][1].lower() == "crisis":
                finalassignments[delegate_key][0] = new_committee.strip()
            else:
                print("Your selected assignment is not the correct committee type. Please try again.")

            check_doubles(current_assignment, Double_Committees, new_committee, delegate_key)

        else:
            print("No changes made or invalid committee name entered. Please try again.")
    return finalassignments

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

def add_assignments_and_map_cells(finalassignments, availableCountries, currentRow, Double_Committees, suggestions_matrix=None):
    """
    Launches an interactive interface to browse and add country assignments.
    Uses true numeric shortcut mappings via text prompts.
    Uses finalassignments inside the function to check with the availability map. Checks after every new assignment input from user with set logic.
    If in availability map, edit finalassignments.
    Passes back finalassignments, and edits the global availability dictionary. 
    finalassignments is formatted: {"School - #": ["committee", "type", "country"]}
    availableCountries is formatted: {("committee", "country_name"): "sheet_coordinate"}
    Finally, creates cell maps at the very end for assigned and unassigned.
    """
    delegate_keys = list(finalassignments.keys())

    while True:
        menu_choices = []
        for delegate in delegate_keys:
            current_comm = finalassignments[delegate][0]
            comm_type = finalassignments[delegate][1]
            current_country = finalassignments[delegate][2] if len(finalassignments[delegate]) > 2 else "Unassigned"
            menu_choices.append(f"{delegate} │ {current_comm} ({comm_type}) - {current_country}")
            
        menu_choices.append("Confirm Assignments")

        selected_choice = questionary.select(
            "Select a delegate to assign a country:",
            choices=menu_choices
        ).ask()

        if selected_choice == "Confirm Assignments" or selected_choice is None:
            print("\033[KExiting and saving changes...")
            break

        delegate_key = selected_choice.split(" │ ")[0].strip()
        delegate_index = delegate_keys.index(delegate_key)
        current_comm = finalassignments[delegate_key][0]

        current_suggestions = []
        if suggestions_matrix and delegate_index < len(suggestions_matrix):
            current_suggestions = suggestions_matrix[delegate_index]

        new_country = None

        # ─── CASE 1: NO SUGGESTIONS MATRIX EXISTS ─────────────────────────────────────
        if not current_suggestions:
            print("\033[F\033[K", end="") 
            raw_input = questionary.text(
                f"Enter country assignment for {delegate_key} in {current_comm}:",
                default=""
            ).ask()

            while not (current_comm, raw_input.strip()) in availableCountries:
                print("Entered country is not in the list of available countries. Try checking spelling or capitalization.")
                raw_input = questionary.text(
                    f"Enter country assignment for {delegate_key} in {current_comm}:",
                    default=""
                ).ask()

            new_country = raw_input.strip()

        # ─── CASE 2: SUGGESTIONS MATRIX EXISTS (THE SHORTCUT ENGINE) ──────────────────
        else:
            print("\033[F\033[K", end="") # Wipe the previous select prompt line
            
            # 1. Print out the available options as a clear text menu block
            print(f"Suggestions for {delegate_key} ({current_comm}):")
            for i, country in enumerate(current_suggestions):
                print(f"  [{i + 1}] {country}")
            print("  [M] Type a custom country manually")
            print("  [B] Go back to main menu")

            # 2. Collect a single clean text input instead of a selection menu
            user_input = questionary.text("Select an option number/shortcut:").ask()

            # Clean up the printed list block from the terminal to keep things immaculate
            # (clears the prompt + your options + the header line)
            for _ in range(len(current_suggestions) + 3):
                print("\033[F\033[K", end="")

            if not user_input:
                continue

            user_input = user_input.strip().lower()

            # 3. Route the shortcut command
            if user_input == 'b':
                continue
                
            elif user_input == 'm':
                while True:
                    raw_input = questionary.text(
                        f"Enter country assignment for {delegate_key} in {current_comm}:",
                        default=""
                    ).ask()

                    lookup_pair = (current_comm.strip(), raw_input.strip())
                    if lookup_pair in availableCountries:
                        new_country = raw_input.strip()
                        break
                    else:
                        print("Country not available. Check spelling/capitalization.")
                    
            else:
                # Validate if the user actually typed a valid option integer
                try:
                    selection_idx = int(user_input) - 1
                    if 0 <= selection_idx < len(current_suggestions):
                        suggested_name = current_suggestions[selection_idx]
                        lookup_pair = (current_comm.strip(), suggested_name.strip())
                        
                        # FIXED: Tuple evaluation instead of zip()
                        if lookup_pair in availableCountries: 
                            new_country = suggested_name
                        else:
                            print("Selected country is no longer available. Please try again.")
                            questionary.press_any_key_to_continue().ask()
                    else:
                        print("Invalid suggestion option number.")
                        questionary.press_any_key_to_continue().ask()
                except ValueError:
                    print("Please type a valid number or menu shortcut character.")

        finalassignments = update_dictionary(new_country, finalassignments, delegate_key, current_comm, Double_Committees)
    
    finalassignments, cell_map, assigned_cell_map = map_cells(finalassignments, availableCountries, currentRow)

    return finalassignments, cell_map, assigned_cell_map

def update_dictionary(new_country, finalassignments, delegate_key, current_comm, Double_Committees):
    # ─── MASTER DICTIONARY UPDATE ─────────────────────────────────────────
    if new_country:
        # 1. Update the selected delegate
        if len(finalassignments[delegate_key]) > 2:
            finalassignments[delegate_key][2] = new_country
        else:
            finalassignments[delegate_key].append(new_country)
            
        print(f"\033[K Assigned {new_country} to {delegate_key} ({current_comm})")

        # 2. AUTOMATIC TWIN LINKING LOGIC FOR DOUBLE DELEGATIONS
        if finalassignments[delegate_key][1] in Double_Committees:
            twin_count = 0
            
            # Scan the dict for the other partner delegate in the exact same committee
            for other_delegate, details in finalassignments.items():
                # Skip the one we literally just manually updated
                if other_delegate == delegate_key:
                    continue
                    
                # If it's the same committee, copy the country over!
                if details[0] == current_comm:
                    if len(finalassignments[other_delegate]) > 2:
                        finalassignments[other_delegate][2] = new_country
                    else:
                        finalassignments[other_delegate].append(new_country)
                    twin_count += 1
            
            if twin_count > 0:
                print(f"\033[K Linked Assignment: Automatically matched {twin_count} partner delegate(s) in {current_comm}!")
    return finalassignments

def map_cells(finalassignments: dict, availableCountries, currentRow):
    cell_map = {}
    assigned_cell_map = {}
    checkingSet = set()
    j = 0
    for delegate, vals in finalassignments.items():
        if len(vals) == 3:
            committee = vals[0]
            country = vals[2]
            checkingSet.add(f"{committee.lower()}, {country.lower()}")

            #construct school assignments cells
            assigned_cell_map[f"Assignments!{sheetFunctions.sheets_alphabet(j+1)}{currentRow}" if j <= 29 else f"Assignments!{sheetFunctions.sheets_alphabet(j-29)}{currentRow + 1}"] = f"{country} ({committee})"
        j += 1
    for (committee, country), coordinate in availableCountries.items():
        if (f"{committee.lower()}, {country.lower()}") in checkingSet:
            #just iterate through the whole availableCountries map and create a cell map while also changing values to "" for those in final assignments.
            cell_map[coordinate] = ""
        elif (f"{committee.lower()}, {country.lower()}") not in checkingSet:
            cell_map[coordinate] = country
    return finalassignments, cell_map, assigned_cell_map

def pull_sheet_data(sheet_service, sheet_id, sheet_name, ranges):
    """
    Pulls all data from Remaining Assignments sheet into RAM.
    Assumes each range contains only a pile of country names.
    Maps (committee, country_name) -> absolute_coordinate in a dictionary.
    """
    full_ranges = [f"{sheet_name}!{r}" for r in ranges.values()]
    
    # Execute ONE bulk network pull for all grid blocks
    result = sheet_service.spreadsheets().values().batchGet(
        spreadsheetId=sheet_id,
        ranges=full_ranges
    ).execute()
    
    value_ranges = result.get('valueRanges', [])
    availability_map = {}
    
    # Helper to convert column indexes back to Excel letters
    def col_to_letter(col_idx):
        letter = ""
        while col_idx >= 0:
            letter = chr(col_idx % 26 + 65) + letter
            col_idx = (col_idx // 26) - 1
        return letter

    # Process each committee block
    for (committee_name, raw_range_str), value_range_obj in zip(ranges.items(), value_ranges):
        
        rows = value_range_obj.get('values', [])
        if not rows:
            continue
            
        # Parse the top-left starting corner of this specific bounding box
        start_cell = raw_range_str.split(':')[0]
        start_col_str = ''.join([c for c in start_cell if c.isalpha()]).upper()
        start_row_num = int(''.join([c for c in start_cell if c.isdigit()]))
        
        # Convert start column letter to a base-0 index
        start_col_idx = 0
        for char in start_col_str:
            start_col_idx = start_col_idx * 26 + (ord(char) - ord('A') + 1)
        start_col_idx -= 1 

        # Loop through every cell in the returned matrix
        for row_offset, row in enumerate(rows):
            for col_offset, cell_value in enumerate(row):
                
                # Strip and read the text
                country_name = cell_value.strip()
                
                # Ignore empty cells or placeholders
                if not country_name or country_name.lower() in ["", "unassigned"]:
                    continue
                    
                # Calculate the exact row and column for THIS specific cell
                current_row_abs = start_row_num + row_offset
                current_col_abs_letter = col_to_letter(start_col_idx + col_offset)
                
                absolute_coordinate = f"{sheet_name}!{current_col_abs_letter}{current_row_abs}"
                
                # Save to your validation lookup map
                availability_map[(committee_name, country_name)] = absolute_coordinate

    return availability_map

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

def check_doubles(current_assignment: str, Double_Committees: set, new_committee: str, delegate_key):
    if current_assignment in Double_Committees and new_committee in Double_Committees:
        print("The old committee was a double committee, and so is the new one. Change the other delegate!")
    elif new_committee in Double_Committees:
        print("The new committee is a double committee. You should find a pair for this delegate, if possible.")
    elif current_assignment in Double_Committees:
        print("The old committee was a double committee. Make sure pairings are still correct!")
    else:
        print(f"Updated {delegate_key} to {new_committee.strip()}")

#testing = {"1": ["DISEC", "GA", ""], "2": ["SOCHUM", "GA", ""], "3": ["UNHRC", "Specialized", ""]}
#add_assignments(testing, suggestions_matrix=[["USA", "China", "Russia"], ["Germany", "France", "UK"], ["Saudi Arabia", "South Africa", "Brazil"]])
#add_assignments(testing)
#print(testing)

#awards won should be calculated as a percentage of total participation.
