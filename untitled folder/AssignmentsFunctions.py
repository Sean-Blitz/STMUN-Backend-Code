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

def confirm_committees(finalassignments, names):
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
        delegate_key = selected_choice.split(":")[0].replace("#", "").strip()
        current_assignment = finalassignments[delegate_key][0]

        # 4. Trigger the manual overwrite prompt
        new_committee = questionary.text(
            f"Enter new committee for {delegate_key} (Current: {current_assignment}):",
            default=current_assignment # Pre-fills the line so they can type over it
        ).ask()

        # 5. Update the master dictionary state in RAM
        if new_committee and new_committee.strip() != current_assignment and new_committee in names:
            finalassignments[delegate_key][0] = new_committee.strip()
            print(f"Updated {delegate_key} to {new_committee.strip()}")
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

def add_assignments(finalassignments, suggestions_matrix=None):
    """
    Launches an interactive interface to browse and add country assignments.
    Uses true numeric shortcut mappings via text prompts.
    """
    delegate_keys = list(finalassignments.keys())

    while True:
        menu_choices = []
        for delegate in delegate_keys:
            current_comm = finalassignments[delegate][0]
            comm_type = finalassignments[delegate][1]
            current_country = finalassignments[delegate][2] if len(finalassignments[delegate]) > 2 else "Unassigned"
            menu_choices.append(f"{delegate} │ {current_comm} ({comm_type}) - {current_country}")
            
        menu_choices.append("Save and Exit")

        selected_choice = questionary.select(
            "Select a delegate to assign a country:",
            choices=menu_choices
        ).ask()

        if selected_choice == "Save and Exit" or selected_choice is None:
            print("\033[KExiting and saving changes...")
            break

        delegate_key = selected_choice.split(" │ ")[0].strip()
        delegate_index = delegate_keys.index(delegate_key)
        current_comm = finalassignments[delegate_key][0]

        current_suggestions = []
        if suggestions_matrix and delegate_index < len(suggestions_matrix):
            current_suggestions = suggestions_matrix[delegate_index]

        new_country = None

        # ─── CASE 1: NO SUGGESTIONS EXIST ─────────────────────────────────────
        if not current_suggestions:
            print("\033[F\033[K", end="") 
            raw_input = questionary.text(
                f"Enter country assignment for {delegate_key} in {current_comm}:",
                default=""
            ).ask()
            if raw_input and raw_input.strip():
                new_country = raw_input.strip()

        # ─── CASE 2: SUGGESTIONS EXIST (THE SHORTCUT ENGINE) ──────────────────
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
                raw_input = questionary.text(
                    f"Enter custom country assignment for {delegate_key}:",
                    default=""
                ).ask()
                if raw_input and raw_input.strip():
                    new_country = raw_input.strip()
                    
            else:
                # Validate if the user actually typed a valid option integer
                try:
                    selection_idx = int(user_input) - 1
                    if 0 <= selection_idx < len(current_suggestions):
                        new_country = current_suggestions[selection_idx]
                    else:
                        print("Invalid suggestion option number.")
                except ValueError:
                    print("Please type a valid number or menu shortcut character.")

        # ─── MASTER DICTIONARY UPDATE ─────────────────────────────────────────
        if new_country:
            if len(finalassignments[delegate_key]) > 2:
                finalassignments[delegate_key][2] = new_country
            else:
                finalassignments[delegate_key].append(new_country)
                
            print(f"\033[K Assigned {new_country} to {delegate_key} ({current_comm})")

    return finalassignments

#testing = {"1": ["DISEC", "GA", ""], "2": ["SOCHUM", "GA", ""], "3": ["UNHRC", "Specialized", ""]}
#add_assignments(testing, suggestions_matrix=[["USA", "China", "Russia"], ["Germany", "France", "UK"], ["Saudi Arabia", "South Africa", "Brazil"]])
#add_assignments(testing)
#print(testing)

#awards won should be calculated as a percentage of total participation.
