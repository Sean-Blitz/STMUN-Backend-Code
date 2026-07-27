import os
import sys
import time
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
from ..Infrastructure import SheetAPI
from ..Infrastructure import DisplayClass
from ..Infrastructure import CSV
from difflib import get_close_matches
import ServerRequests

# ---------- CONTROLS -----------
registrationSheetID = "1LgQxP67-pe6JW0lixWacp3ou5UV1f2vmSGVI8j5IPIs" #link to your registration Sheet
sheetname = "Responses"
DoubleGAs = "no" #type yes or no, depending on if there are double delegate GA's this year.
# -------------------------------

SheetsAPI = SheetAPI()
Display = DisplayClass()
Storage = CSV()
registrationSheetURL = f"https://docs.google.com/spreadsheets/d/{registrationSheetID}/edit"

def verify_committee_number_input(GA, Specialized):
    if '\x1b' in GA:
        # keeps only the actual digits typed
        GA = ''.join(c for c in GA if c.isdigit())
    if '\x1b' in Specialized:
        # keeps only the actual digits typed; ignores letters and ANSI escape sequences.
        Specialized = ''.join(c for c in Specialized if c.isdigit())
    GA = int(GA); Specialized = int(Specialized)
    while DoubleGAs == "no" and GA % 2 != 0: #if no double delegate GAs and the input is odd
        GA = input("How many delegates to put in GA? Input must be even.")
        Specialized = input("How many delegates to put in Specialized?")
        if '\x1b' in Specialized:
            # keeps only the actual digits typed; ignores letters and ANSI escape sequences.
            Specialized = ''.join(c for c in Specialized if c.isdigit())
        if '\x1b' in GA:
            # keeps only the actual digits typed
            GA = ''.join(c for c in GA if c.isdigit())
        GA = int(GA)
        Specialized = int(Specialized)
    return GA, Specialized

def read_overview(registrationSheetID):
    names = SheetsAPI.get_column_data_until_empty(registrationSheetID, "Overview", "A", 2) # Use this function to also detect number of committees
    percentages = SheetsAPI.read_cells(registrationSheetID, [f"Overview!D{i+2}" for i in range(len(names))])
    percentages = [float(p.strip('%')) for p in percentages] # Convert "45%" to 45.0
    spots = SheetsAPI.read_cells(registrationSheetID, [f"Overview!C{i+2}" for i in range(len(names))])
    spots = [int(s) for s in spots] # Convert spot counts to integers
    double = SheetsAPI.read_cells(registrationSheetID, [f"Overview!E{i+2}" for i in range(len(names))])
    type = SheetsAPI.read_cells(registrationSheetID, [f"Overview!F{i+2}" for i in range(len(names))])
    ranges = SheetsAPI.read_cells(registrationSheetID, [f"Overview!H{i+2}" for i in range(len(names))])
    ranges = {names[i]: ranges[i] for i in range(len(names))}
    return names, percentages, spots, double, type, ranges
    
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
        Display.display("Error in Committee Type Selection.")
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
        Display.clear_current_line()
        Display.display("Error in assignment logic.")
        if input("Continue? (y/n)") == "y":
            i = i + 1
            iterator = iterator + 1
        elif input("Continue? (y/n)") == "n":
            sys.exit(0)
    else:
        Display.display("Error in making committees for GA at values of i and iterator:", i, iterator)
        i = i + 1
    return finalassignments, i, percentages, iterator

def confirm_committees(finalassignments, GA_Names, Spec_Names, Crisis_Names, Double_Committees):
    while True:
        menu_choices = []
        for delegate, details in finalassignments.items():
            current_committee = details[0]
            committee_type = details[1]
            choice_text = f"{delegate}: {current_committee} ({committee_type})"
            menu_choices.append(choice_text)
        selected_choice = Display.display_list_of_selections(menu_choices, "Select a delegate to modify committee (if desired)", "Save and Exit")

        if selected_choice == "exit":
            break

        delegate_key = selected_choice.split(":")[0].strip() #read result
        current_assignment = finalassignments[delegate_key][0]
        new_committee = Display.typing_with_pre_fill(f"Enter new committee for {delegate_key} (Current: {current_assignment}):", current_assignment)

        #Helper function to check double committees.
        def check_doubles(current_assignment: str, Double_Committees: set, new_committee: str, delegate_key):
            if current_assignment in Double_Committees and new_committee in Double_Committees:
                Display.display("The old committee was a double committee, and so is the new one. Change the other delegate!")
            elif new_committee in Double_Committees:
                Display.display("The new committee is a double committee. You should find a pair for this delegate, if possible.")
            elif current_assignment in Double_Committees:
                Display.display("The old committee was a double committee. Make sure pairings are still correct!")
            else:
                Display.display(f"Updated {delegate_key} to {new_committee.strip()}")
        #------------------------------------------------------------------

        #update dictionary with new choice
        if new_committee and new_committee.strip() != current_assignment:
            if new_committee in GA_Names and finalassignments[delegate_key][1].lower() == "ga":
                finalassignments[delegate_key][0] = new_committee.strip()
                check_doubles(current_assignment, Double_Committees, new_committee, delegate_key)
            elif new_committee in Spec_Names and finalassignments[delegate_key][1].lower() == "specialized":
                finalassignments[delegate_key][0] = new_committee.strip()
                check_doubles(current_assignment, Double_Committees, new_committee, delegate_key)
            elif new_committee in Crisis_Names and finalassignments[delegate_key][1].lower() == "crisis":
                finalassignments[delegate_key][0] = new_committee.strip()
                check_doubles(current_assignment, Double_Committees, new_committee, delegate_key)
            else:
                Display.display("Your selected assignment is not the correct committee type or is not a committee name. Please try again.")
        else:
            Display.display("No changes made or invalid committee name entered. Please try again.")
    return finalassignments

def update_dictionary(new_country, finalassignments, delegate_key, current_comm, Double_Committees):
    # ─── MASTER DICTIONARY UPDATE ─────────────────────────────────────────
    if new_country:
        # 1. Update the selected delegate
        if len(finalassignments[delegate_key]) > 2:
            finalassignments[delegate_key][2] = new_country
        else:
            finalassignments[delegate_key].append(new_country)
            
        Display.display(f"\033[K Assigned {new_country} to {delegate_key} ({current_comm})")
    
            # 2. TWIN LINKING LOGIC FOR DOUBLE DELEGATION COMMITTEES
        if finalassignments[delegate_key][0] in Double_Committees:
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
                Display.display(f"\033[K Linked Assignment: Automatically matched {twin_count} partner delegate(s) in {current_comm}!")
                time.sleep(1)

    return finalassignments

def add_assignments(finalassignments, availableCountries, currentRow, Double_Committees, suggestions_matrix=None):
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
            
        selected_choice = Display.display_list_of_selections(menu_choices, "Select a delegate to give assignments", "Confirm Assignments")

        if selected_choice == "exit" or selected_choice is None:
            Display.display("\033[K Exiting and saving changes...")
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
            Display.go_one_line_up(); Display.clear_current_line()
            input = Display.typing_with_pre_fill(f"Enter country assignment for {delegate_key} in {current_comm}:", "")

            while not (current_comm, input.strip()) in availableCountries:
                Display.display("Entered country is not in the list of available countries. Try checking spelling or capitalization.")
                input = Display.typing_with_pre_fill(f"Enter country assignment for {delegate_key} in {current_comm}:", "")

            new_country = input.strip()

        # ─── CASE 2: SUGGESTIONS MATRIX EXISTS (THE SHORTCUT ENGINE) ──────────────────
        else:
            Display.go_one_line_up(); Display.clear_current_line()
            
            # 1. Display.display out the available options as a clear text menu block
            Display.display(f"Suggestions for {delegate_key} ({current_comm}):")
            for i, country in enumerate(current_suggestions):
                Display.display(f"  [{i + 1}] {country}")
            Display.display("  [M] Type a custom country manually")
            Display.display("  [B] Go back to main menu")

            # 2. Collect a single clean text input instead of a selection menu
            user_input = Display.typing_with_pre_fill("Select an option number/shortcut:", "")

            # Clean up the Display.displayed list block from the terminal to keep things immaculate
            # (clears the prompt + your options + the header line)
            for i in range(len(current_suggestions) + 3):
                Display.go_one_line_up(); Display.clear_current_line()

            if not user_input:
                continue

            user_input = user_input.strip().lower()

            # 3. Route the shortcut command
            if user_input == 'b':
                continue
                
            elif user_input == 'm': #manual input
                while True:
                    raw_input = Display.typing_with_pre_fill(f"Enter country assignment for {delegate_key} in {current_comm}:", "")

                    lookup_pair = (current_comm.strip(), raw_input.strip())
                    if lookup_pair in availableCountries:
                        new_country = raw_input.strip()
                        break
                    else:
                        Display.display("Country not available. Check spelling/capitalization.")
                    
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
                            Display.display("Selected country is no longer available. Please try again.")
                            Display.press_any_key_to_continue()
                    else:
                        Display.display("Invalid suggestion option number.")
                        Display.press_any_key_to_continue()
                except ValueError:
                    Display.display("Please type a valid number or menu shortcut character.")
        finalassignments = update_dictionary(new_country, finalassignments, delegate_key, current_comm, Double_Committees)
    valueslist = list(finalassignments.values())
    for i in range(len(valueslist)):
        if valueslist[i][2] == "" or valueslist[i][2] == None:
            Display.display("ERROR: You have not fulfilled all assignments yet!!!")
            add_assignments(finalassignments, availableCountries, currentRow, Double_Committees, suggestions_matrix)


    return finalassignments, availableCountries, currentRow

def print_data_to_terminal_with_prompt(CountryPrefs, MiddleEasternBloc, AmericanBloc, EuropeanBloc, AsianBloc, AfricanBloc, PacificBloc, SecurityCouncil, numdels):
    Display.display("Top 5 country preferences:", "\033[1m" + CountryPrefs + "\033[0m") #Display.display country preferences in bold for visibility.
    Display.display("Middle Eastern Bloc:", "\033[1m" + MiddleEasternBloc + "\033[0m")
    Display.display("American Bloc:", "\033[1m" + AmericanBloc + "\033[0m")
    Display.display("European Bloc:", "\033[1m" + EuropeanBloc + "\033[0m")
    Display.display("Asian Bloc:", "\033[1m" + AsianBloc + "\033[0m")
    Display.display("African Country Bloc:", "\033[1m" + AfricanBloc + "\033[0m")
    Display.display("Pacific Country Bloc:", "\033[1m" + PacificBloc + "\033[0m")
    Display.display("Security Council interest:", "\033[1m" + SecurityCouncil + "\033[0m")
    Display.display("Delegates to assign for this school:" "\033[1m" + str(numdels) + "\033[0m")

    #data science: school awards from past
    GA = input("How many delegates to put in GA?")
    Specialized = input("How many delegates to put in Specialized?")
    GA, Specialized = verify_committee_number_input(GA, Specialized)
    Crisis = numdels - GA - Specialized
    return GA, Specialized, Crisis

def read_committees_overview_from_sheet(GA, Specialized, Crisis, Committeetype, double):
    Display.go_one_line_up(); Display.clear_current_line(); Display.go_one_line_up(); Display.clear_current_line()
    Display.display(f"GA: {GA}, Specialized: {Specialized}, Crisis: {Crisis}")

    indices = {"ga": [], "specialized": [], "crisis": []}
    single_indices = {"ga": [], "specialized": [], "crisis": []}
    for index, (kind, is_double) in enumerate(zip(Committeetype, double)):
        kind = kind.lower().replace(".", "").strip()  # Normalize the committee type string

        if kind in indices:
            indices[kind].append(index)

            if is_double.lower() == "false":
                single_indices[kind].append(index)

    GaIndices = indices["ga"]
    SpecIndices = indices["specialized"]
    CrisisIndices = indices["crisis"]

    return single_indices, GaIndices, SpecIndices, CrisisIndices

def assign_new_schools():
    sheetSchools = SheetsAPI.get_column_data_until_empty(registrationSheetID, sheetname, "C", 2)
    unassignedSchools = Storage.find_non_overlap_string(sheetSchools, "assignedSchools.csv")
    while unassignedSchools:
        selectedSchool = Display.select_option_with_pointer(unassignedSchools, "Select a school to begin assignments", "SCVMUN ASSIGNMENT ENGINE - PENDING SCHOOLS")
        row = SheetsAPI.find_row_by_string(registrationSheetID, sheetname, "C", selectedSchool)
        output = SheetsAPI.read_cells(registrationSheetID, [f"{sheetname}!R{row}", f"{sheetname}!S{row}", f"{sheetname}!T{row}", f"{sheetname}!U{row}", f"{sheetname}!V{row}", f"{sheetname}!W{row}", f"{sheetname}!X{row}", f"{sheetname}!Y{row}", f"{sheetname}!Q{row}"])
        CountryPrefs, MiddleEasternBloc, AmericanBloc, EuropeanBloc, AsianBloc, AfricanBloc, PacificBloc, SecurityCouncil, numdels = output
        numdels = int(numdels)

        #pulls from Remaining Assignments for checking and pushing back later.

        GA, Specialized, Crisis= print_data_to_terminal_with_prompt(CountryPrefs, MiddleEasternBloc, AmericanBloc, EuropeanBloc, AsianBloc, AfricanBloc, PacificBloc, SecurityCouncil, numdels)

        if GA + Specialized > numdels:
            Display.display("Error: The total number of delegates does not match the expected count.")
            sys.exit()
        else:
            names, percentages, spots, double, Committeetype, ranges = read_overview(registrationSheetID)
            availableCountries = SheetsAPI.pull_sheet_data(registrationSheetID, "Remaining Assignments", ranges)
            single_indices, GaIndices, SpecIndices, CrisisIndices = read_committees_overview_from_sheet(GA, Specialized, Crisis, Committeetype, double)
            
            i = 0; iterator = 0
            finalassignments = {} #dictionary with a value being a list of two elements, the committee and the country assigned.
            committeeCount = (GA, Specialized, Crisis)
            while iterator < GA:
                data = (names, percentages, double, spots, Committeetype)
                finalassignments, i, percentages, iterator = assign_committee("GA", GaIndices, data, finalassignments, iterator, i, single_indices, selectedSchool, committeeCount) #type: ignore
            iterator = 0
            while iterator < Specialized:
                data = (names, percentages, double, spots, Committeetype)
                finalassignments, i, percentages, iterator = assign_committee("Specialized", SpecIndices, data, finalassignments, iterator, i, single_indices, selectedSchool, committeeCount) #type: ignore
            iterator = 0
            if SecurityCouncil.lower() != "yes":
                CrisisInd = [idx for idx in CrisisIndices if names[idx].lower() != "security council" and names[idx].lower() != "historical crisis"]
            else:
                CrisisInd = CrisisIndices
            while iterator < Crisis:
                data = (names, percentages, double, spots, Committeetype)
                finalassignments, i, percentages, iterator = assign_committee("Crisis", CrisisInd, data, finalassignments, iterator, i, single_indices, selectedSchool, committeeCount) #type: ignore
            
            GA_Names = [] ; Spec_Names = [] ; Crisis_Names = [] ; Double_Committees = set()
            for i in range(len(names)): #build the lists above to pass into functions for verification.
                if i in GaIndices:
                    GA_Names.append(names[i])
                elif i in SpecIndices:
                    Spec_Names.append(names[i])
                elif i in CrisisIndices:
                    Crisis_Names.append(names[i])
                else:
                    Display.display("There is a committee name error.")
                    sys.exit()
                if not i in single_indices:
                    Double_Committees.add(names[i])

            Display.clear_current_line()
            Display.display("Assignments for this school:")
            finalassignments = confirm_committees(finalassignments, GA_Names, Spec_Names, Crisis_Names, Double_Committees)
            # a business logic function that calls display functions.
            CurrentRow = SheetsAPI.get_column_odd_cells(registrationSheetID, "Assignments", "A", 1) + 2

            #Data science function to generate countrySuggestionsList!
            finalassignments, availableCountries, currentRow = add_assignments(finalassignments, availableCountries, CurrentRow, Double_Committees) #, countrySuggestionsList)
            finalassignments, SchoolAssignmentsCells, remaining_cell_map = SheetsAPI.map_cells(finalassignments, availableCountries, currentRow)
            cont = input("Finished building cell maps. Push? (yes, no)")
            while cont.lower() not in {"yes", "no"}:
                cont = input("Finished building cell maps. Push?")
            if cont != "yes":
                sys.exit()

            #writing to the sheet the cell maps.
            SheetsAPI.write_values_to_sheet_from_dict(registrationSheetID, remaining_cell_map)
            SheetsAPI.write_values_to_sheet_from_dict(registrationSheetID, SchoolAssignmentsCells)
            SheetsAPI.write_values_to_sheet_from_dict(registrationSheetID, {f"Assignments!A{CurrentRow}": selectedSchool})
            
            time.sleep(5); Display.display("Checking sheet for changes...") #pause for sheet to register changes.
            percentagesChecking = SheetsAPI.read_cells(registrationSheetID, [f"Overview!D{i+2}" for i in range(len(names))])
            percentagesChecking = [float(p.strip('%')) for p in percentagesChecking] # Convert "45%" to 45.0
            hashes = ServerRequests.add_new_school_or_delegates_to_existing_school_and_request_hashes(finalassignments)
            if percentagesChecking == percentages and hashes != None:
                Display.display("Percentages are correct. Here are the hashes. Moving on to next school, and placing name in completed CSV.")
                Display.display(hashes)
            else:
                Display.display("Percentage error. Please check the sheet! School name placed in completed CSV; here are the hashes. Moving on to next school.")
                Display.display(registrationSheetURL)
                Display.display(hashes)
            Storage.append_to_csv("assignedSchools.csv", [selectedSchool])
            unassignedSchools.remove(selectedSchool)

def add_delegates():
    #Goal: Add delegates to a school that already exists. Scan the sheet for user inputted school, then prompt user how many delegates to add. Finally, assign new delegates just like with new school registration.
    # Request for new hashes and send this new data to the database.
    
    SchooltoAdd = input("Please input the school to add delegates to.")

    CurrentSchools = [] #now get those schools from the Google Sheets

    if SchooltoAdd not in CurrentSchools:
        ClosestMatch = get_close_matches(SchooltoAdd, CurrentSchools, n=1, cutoff=0.6)
        Display.display(f"Input error. Did you mean: {ClosestMatch}?")
    pass
def drop_delegates():
    #Goal: delete delegates from the assignments sheet and move them back to the original pool. Ask user for which school and Display.display all options for drop. Confirm drop, then delete them from the assignments sheet.
    # Finally, insert them back into the original pool by reading their committee name, and slotting them back to the first empty cell. Request that these assignments be deleted from the database.
    pass

"""
Improvements:
Split up main function into smaller parts
Fix percentage error
System for drops and additions? Start with a questionary prompt for adding schools, dropping delegates, adding delegates.
Link assignments up to sheets provided to schools
Code a reusable function that reads headers and returns column value from sheets, to allow for database-like reading?

"""