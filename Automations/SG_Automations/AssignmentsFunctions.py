import os
import sys
import time
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
from Assignments_Sheets_Adapter import Assignments_to_Sheets
from ..Infrastructure import DisplayClass
from ..Infrastructure import CSV

SheetsAPI = Assignments_to_Sheets()
Display = DisplayClass()
Storage = CSV()

def verify_committee_number_input(GA, Specialized, DoubleGAs):
    if '\x1b' in GA:
        # keeps only the actual digits typed
        GA = ''.join(c for c in GA if c.isdigit())
    if '\x1b' in Specialized:
        # keeps only the actual digits typed; ignores letters and ANSI escape sequences.
        Specialized = ''.join(c for c in Specialized if c.isdigit())
    GA = int(GA); Specialized = int(Specialized)
    while DoubleGAs == "no" and GA % 2 != 0: #if no double delegate GAs and the Display.take_text_input is odd
        GA = Display.take_text_input("How many delegates to put in GA? Display.take_text_input must be even.")
        Specialized = Display.take_text_input("How many delegates to put in Specialized?")
        if '\x1b' in Specialized:
            # keeps only the actual digits typed; ignores letters and ANSI escape sequences.
            Specialized = ''.join(c for c in Specialized if c.isdigit())
        if '\x1b' in GA:
            # keeps only the actual digits typed
            GA = ''.join(c for c in GA if c.isdigit())
        GA = int(GA)
        Specialized = int(Specialized)
    return GA, Specialized
    
def assign_committee(CommitteeTypeSelection, Indices: list, data: tuple, finalassignments: dict, iterator, i, singleIndices: dict, selectedSchool, committeeCount: tuple):
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
        sys.exit()
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
        if Display.take_text_input("Continue? (y/n)") == "y":
            i = i + 1
            iterator = iterator + 1
        elif Display.take_text_input("Continue? (y/n)") == "n":
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

def print_data_to_terminal_with_prompt(doubleGAs, CountryPrefs, MiddleEasternBloc, AmericanBloc, EuropeanBloc, AsianBloc, AfricanBloc, PacificBloc, SecurityCouncil, numdels, newschool=True):
    Display.display("Top 5 country preferences:", "\033[1m" + CountryPrefs + "\033[0m") #Display.display country preferences in bold for visibility.
    Display.display("Middle Eastern Bloc:", "\033[1m" + MiddleEasternBloc + "\033[0m")
    Display.display("American Bloc:", "\033[1m" + AmericanBloc + "\033[0m")
    Display.display("European Bloc:", "\033[1m" + EuropeanBloc + "\033[0m")
    Display.display("Asian Bloc:", "\033[1m" + AsianBloc + "\033[0m")
    Display.display("African Country Bloc:", "\033[1m" + AfricanBloc + "\033[0m")
    Display.display("Pacific Country Bloc:", "\033[1m" + PacificBloc + "\033[0m")
    Display.display("Security Council interest:", "\033[1m" + SecurityCouncil + "\033[0m")
    if newschool == True:
        Display.display("Delegates to assign for this school:" "\033[1m" + str(numdels) + "\033[0m")

    #data science: school awards from past
    GA = Display.take_text_input("How many delegates to put in GA?")
    Specialized = Display.take_text_input("How many delegates to put in Specialized?")
    GA, Specialized = verify_committee_number_input(GA, Specialized, doubleGAs)
    Crisis = numdels - GA - Specialized
    return GA, Specialized, Crisis

def read_committees_overview_from_sheet(Committeetype, double):
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

def add_assignments(finalassignments, availableCountries, Double_Committees, suggestions_matrix=None):
    """
    Launches an interactive interface to browse and add country assignments.
    Uses true numeric shortcut mappings via text prompts.
    Uses finalassignments inside the function to check with the availability map. Checks after every new assignment Display.take_text_input from user with set logic.
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
        # --- CHECK IF ALL DELEGATES ARE ASSIGNED ---
            all_assigned = True
            for details in finalassignments.values():
                # Check if country field is missing, empty, or None
                if len(details) <= 2 or details[2] == "" or details[2] is None:
                    all_assigned = False
                    break  # Found at least one unassigned delegate, stop checking
            
            # --- DECISION LOGIC ---
            if not all_assigned:
                Display.display("ERROR: You have not fulfilled all assignments yet! Please assign all delegates.")
                continue  # Keeps the user INSIDE the while loop so they can assign remaining delegates
            else:
                Display.display("\033[K Exiting and saving changes...")
                break  # Safely breaks out of the while loop and finishes the function      

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
                
            elif user_input == 'm': #manual Display.take_text_input
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
    return finalassignments, availableCountries

def check_committees_and_build_final_assignments(finalassignments, GA_Names, Spec_Names, Crisis_Names, Double_Committees, availableCountries):
    Display.display("Assignments for this school:")
    finalassignments = confirm_committees(finalassignments, GA_Names, Spec_Names, Crisis_Names, Double_Committees)
    # a business logic function that calls display functions.

    #Data science function to generate countrySuggestionsList!
    finalassignments, availableCountries = add_assignments(finalassignments, availableCountries, Double_Committees) #, countrySuggestionsList)

    return finalassignments


