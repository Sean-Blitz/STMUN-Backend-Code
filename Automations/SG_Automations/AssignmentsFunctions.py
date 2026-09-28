import os
import sys
import re
from SG_Automations.Assignments_Sheets_Adapter import Assignments_to_Sheets
from Infrastructure import DisplayClass
from Infrastructure import CSV
from Infrastructure import AirtableAPI
from SG_Automations.DataManager import ConferenceInformation, SchoolInformation, SchoolDelegates
from dotenv import load_dotenv; load_dotenv()

SheetsAPI = Assignments_to_Sheets()
Display = DisplayClass()
Storage = CSV()
SecondaryStorage = AirtableAPI()

def verify_committee_number_input(GA, Specialized, DoubleGAs):
    if '\x1b' in GA:
        # keeps only the actual digits typed
        GA = ''.join(c for c in GA if c.isdigit())
    if '\x1b' in Specialized:
        # keeps only the actual digits typed; ignores letters and ANSI escape sequences.
        Specialized = ''.join(c for c in Specialized if c.isdigit())
    GA = int(GA); Specialized = int(Specialized)
    while DoubleGAs == "yes" and GA % 2 != 0: #if no double delegate GAs and the Display.take_text_input is odd
        GA = Display.take_text_input("How many delegates to put in GA? Input must be even.")
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
    
def assign_committee(ConferenceInfo: ConferenceInformation, SchoolInfo: SchoolInformation, Delegates: SchoolDelegates, iterator, i, CommitteeTypeSelection):
    """
    Assigns delegates based on parameter of CommitteeTypeSelection, which is a string for either "GA", "Specialized", or "Crisis".
    """
    #sets up variables
    if CommitteeTypeSelection == "GA":
        committeeCount = SchoolInfo.GA_count
    elif CommitteeTypeSelection == "Specialized":
        committeeCount = SchoolInfo.Spec_count
    elif CommitteeTypeSelection == "Crisis":
        committeeCount = SchoolInfo.Crisis_count
    else:
        Display.display("Error in Committee Type Selection.")
        sys.exit()

    committee = ConferenceInfo.get_lowest_committee_percentage_for_type(CommitteeTypeSelection)
    if ConferenceInfo.committee_double_status[committee] == True and committeeCount - iterator > 1: #if double delegate committee and enough GA assignmentspots left.
        Delegates.add_delegate(committee, ConferenceInfo.committee_types[committee], country="", number=i+1)
        Delegates.add_delegate(committee, ConferenceInfo.committee_types[committee], country="", number=i+2)
        ConferenceInfo.committee_percentage_filled[committee] += (2 * 100/ ConferenceInfo.committee_spots[committee])
        i = i + 2 #skip the next delegate since we just assigned it.
        iterator = iterator + 2
    elif ConferenceInfo.committee_double_status[committee] == True and committeeCount - iterator == 1: #if double delegate commmittee and not enough GA assignment spots left
        committee = min([name for name in ConferenceInfo.committee_names if ConferenceInfo.committee_types[name] == "GA"], key = lambda name: ConferenceInfo.committee_percentage_filled[name]) 
        #only scans single del GA's. Finds another committee that is a single del GA this time.
        Delegates.add_delegate(committee, ConferenceInfo.committee_types[committee], country="", number=i+1)
        ConferenceInfo.committee_percentage_filled[committee] += (100/ ConferenceInfo.committee_spots[committee])
        i = i +1
        iterator = iterator + 1
    elif ConferenceInfo.committee_double_status[committee] == False: #if single delegate committee
        Delegates.add_delegate(committee, ConferenceInfo.committee_types[committee], country="", number=i+1)
        ConferenceInfo.committee_percentage_filled[committee] += (100/ ConferenceInfo.committee_spots[committee])
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
    return i, iterator

def confirm_committees(Delegates: SchoolDelegates, ConferenceInfo: ConferenceInformation):
    while True:
        menu_choices = []
        for number, committee, committee_type, country in zip(Delegates.number, Delegates.committee, Delegates.committee_type, Delegates.country):
            choice_text = f"{number}: {committee} ({committee_type})"
            menu_choices.append(choice_text)
        selected_choice = Display.display_list_of_selections(menu_choices, "Select a delegate to modify committee (if desired)", "Save and Exit")

        if selected_choice == "exit":
            break

        delegate_key = selected_choice.split(":")[0].strip() #read result
        current_committee = Delegates.committee[Delegates.number.index(int(delegate_key))]
        new_committee = Display.display_list_of_selections(ConferenceInfo.committee_names, "Choose new committee", "Exit (keep same committee)")
        if new_committee == "Exit (keep same committee)":
            new_committee = current_committee

        #Helper function to check double committees.
        def check_doubles(current_assignment: str, new_committee: str, delegate_key, ConferenceInfo: ConferenceInformation):
            if current_assignment and ConferenceInfo.committee_double_status[current_assignment] == True and new_committee and ConferenceInfo.committee_double_status[new_committee] == True:
                Display.display("The old committee was a double committee, and so is the new one. Change the other delegate!")
            elif ConferenceInfo.committee_double_status[new_committee] == True:
                Display.display("The new committee is a double committee. You should find a pair for this delegate, if possible.")
            elif ConferenceInfo.committee_double_status[current_assignment] == True:
                Display.display("The old committee was a double committee. Make sure pairings are still correct!")
            else:
                Display.display(f"Updated {delegate_key} to {new_committee.strip()}")
        #------------------------------------------------------------------

        #update dictionary with new choice
        if new_committee and new_committee.strip() != current_committee and new_committee in ConferenceInfo.committee_names:
            Delegates.committee[Delegates.number.index(int(delegate_key))] = new_committee
            check_doubles(current_committee, new_committee, delegate_key, ConferenceInfo)
        else:
            Display.display("No changes made or invalid committee name entered. Please try again.")

def update_delegates(new_country: str, old_country: str | None, delegate_key: int, current_comm: str, ConferenceInfo: ConferenceInformation, Delegates: SchoolDelegates):
    # ─── MASTER DICTIONARY UPDATE ─────────────────────────────────────────
    if new_country:
        new_country = new_country.strip()
        if new_country is not None and new_country != old_country:
            if old_country is not None and old_country.strip() != "":
                # If the delegate already had an assignment, return it to availableCountries
                ConferenceInfo.available_countries.append([current_comm, old_country])
            ConferenceInfo.available_countries.remove([current_comm, new_country])  # Remove the newly assigned country from availableCountries
        # 1. Update the selected delegate
        Delegates.country[delegate_key] = new_country
            
        Display.display(f"\033[K Assigned {new_country} to {delegate_key} ({current_comm})")
    
            # 2. TWIN LINKING LOGIC FOR DOUBLE DELEGATION COMMITTEES
        if ConferenceInfo.committee_double_status[current_comm] == True:

            twin_delegate = None
            # Scan the dict for the other partner delegate in the exact same committee
            for other_delegate_number in Delegates.number:

                # Skip the one we literally just manually updated
                if other_delegate_number == delegate_key:
                    continue
                    
                # If it's the same committee, copy the country over!
                if Delegates.committee[other_delegate_number] == current_comm:
                    other_old_country = Delegates.country.get(other_delegate_number)
                    other_old_country = other_old_country.strip() if other_old_country else ""
                    if other_old_country == old_country:
                        twin_delegate = other_delegate_number
                        break # this part ensures that you only flag the other delegate once, so that there is only one twin.

            if twin_delegate is not None:
                Delegates.country[twin_delegate] = new_country
                Display.display(f"\033[K Assigned {new_country} to twin delegate {twin_delegate}")
                if old_country is not None and old_country.strip() != "":
                    # If the delegate already had an assignment, return it to availableCountries
                    ConferenceInfo.available_countries.append([current_comm, old_country])
                ConferenceInfo.available_countries.remove([current_comm, new_country])  # Remove the newly assigned country from availableCountries, for the twin delegate.

def print_data_to_terminal(RegionBloc, CountryPrefs, SecurityCouncil, numdels, newschool=True):
    Display.display("Region block most preferred:", "\033[1m" + RegionBloc + "\033[0m") #Display.display country preferences in bold for visibility.
    for i, country in enumerate(CountryPrefs):
        Display.display(f"Country preference {i + 1}:", "\033[1m" + country + "\033[0m")
    Display.display("Security Council interest:", "\033[1m" + SecurityCouncil + "\033[0m")
    if newschool == True:
        Display.display("Delegates to assign for this school:" "\033[1m" + str(numdels) + "\033[0m")

def get_input_for_committee_assignment_counts(doubleGAs, SchoolInfo: SchoolInformation):
    GA = Display.take_text_input("How many delegates to put in GA?")
    Specialized = Display.take_text_input("How many delegates to put in Specialized?")
    GA, Specialized = verify_committee_number_input(GA, Specialized, doubleGAs)
    Crisis = SchoolInfo.numdels - GA - Specialized
    if GA + Specialized > SchoolInfo.numdels:
        raise ValueError("The total number of delegates assigned to GA and Specialized exceeds the total number of delegates for the school.")
    SchoolInfo.GA_count = GA
    SchoolInfo.Spec_count = Specialized
    SchoolInfo.Crisis_count = Crisis
    Display.display(f"GA: {GA}, Specialized: {Specialized}, Crisis: {Crisis}")

def add_assignments(Delegates: SchoolDelegates, ConferenceInfo: ConferenceInformation):
    """
    Launches an interactive interface to browse and add country assignments.
    Uses true numeric shortcut mappings via text prompts.
    Uses finalassignments inside the function to check with the availability map. Checks after every new assignment Display.take_text_input from user with set logic.
    If in availability map, edit finalassignments.
    Passes back finalassignments, and edits the global availability dictionary. 
    finalassignments is formatted: {"School - #": ["committee", "type", "country"]}
    availableCountries is formatted as a 2D list: [["committee", "country_name"], ...]
    Finally, creates cell maps at the very end for assigned and unassigned.
    """

    while True:
        menu_choices = []
        for number in Delegates.number:
            current_comm = Delegates.committee[number]
            comm_type = Delegates.committee_type[number]
            current_country = Delegates.country.get(number) if Delegates.country.get(number) else "Unassigned"
            menu_choices.append(f"{number} │ {current_comm} ({comm_type}) - {current_country}")
            
        selected_choice = Display.display_list_of_selections(menu_choices, "Select a delegate to give assignments", "Confirm Assignments")

        if selected_choice == "exit" or selected_choice is None:
        # --- CHECK IF ALL DELEGATES ARE ASSIGNED ---
            all_assigned = True
            for number in Delegates.number:
                # Check if country field is missing, empty, or None
                if number not in Delegates.country or Delegates.country[number] is None or Delegates.country[number].strip() == "":
                    all_assigned = False
                    break  # Found at least one unassigned delegate, stop checking
            if not all_assigned:
                Display.display("ERROR: You have not fulfilled all assignments yet! Please assign all delegates.")
                continue  # Keeps the user INSIDE the while loop so they can assign remaining delegates
            else:
                Display.display("\033[K Exiting and saving changes...")
                break  # Safely breaks out of the while loop and finishes the function      

        delegate_key = int(selected_choice.split(" │ ")[0].strip())
        current_comm = Delegates.committee[delegate_key]

        old_country = Delegates.country.get(delegate_key) # safely returns None if not assigned yet

        current_suggestions = []
        selected_option = selected_choice.split(" │ ")[0].strip()
        current_suggestions = Delegates.suggestions.get(selected_option)

        new_country = None

        # ─── CASE 1: NO SUGGESTIONS MATRIX EXISTS ─────────────────────────────────────
        if not current_suggestions:
            Display.go_one_line_up(); Display.clear_current_line()
            input = Display.typing_with_pre_fill(f"Enter country assignment for {delegate_key} in {current_comm}:", "")

            lookup_pair = [current_comm.strip(), input.strip()]
            while not lookup_pair in ConferenceInfo.available_countries:
                Display.display("Entered country is not in the list of available countries. Try checking spelling or capitalization.")
                input = Display.typing_with_pre_fill(f"Enter country assignment for {delegate_key} in {current_comm}:", "")

            new_country = input.strip()

        # ─── CASE 2: SUGGESTIONS MATRIX EXISTS (THE SHORTCUT ENGINE) ──────────────────
        else:
            Display.go_one_line_up(); Display.clear_current_line()
            
            # 1. Display.display out the available options as a clear text menu block
            Display.display(f"Suggestions for {delegate_key} ({current_comm}):")
            for i, country in enumerate(current_suggestions[0]):
                Display.display(f"  [{i + 1}] {country}")
            Display.display("  [M] Type a custom country manually")
            Display.display("  [B] Go back to main menu")

            Display.display("These are the countries that are preferred by the school and available for this committee. You may type these in manually.")
            for country in current_suggestions[1]:
                Display.display(f"  {country}")
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

                    lookup_pair = [current_comm.strip(), raw_input.strip()]
                    if lookup_pair in ConferenceInfo.available_countries:
                        new_country = raw_input.strip()
                        break
                    else:
                        Display.display("Country not available. Check spelling/capitalization.")
                    
            else:
                # Validate if the user actually typed a valid option integer
                try:
                    selection_idx = int(user_input) - 1
                    if 0 <= selection_idx < len(current_suggestions[0]):
                        suggested_name = current_suggestions[0][selection_idx]
                        lookup_pair = [current_comm.strip(), suggested_name.strip()]
                        
                        # FIXED: Tuple evaluation instead of zip()
                        if lookup_pair in ConferenceInfo.available_countries: 
                            new_country = suggested_name
                        else:
                            Display.display("Selected country is no longer available. Please try again.")
                            Display.press_any_key_to_continue()
                    else:
                        Display.display("Invalid suggestion option number.")
                        Display.press_any_key_to_continue()
                except ValueError:
                    Display.display("Please type a valid number or menu shortcut character.")

        if type(new_country) is not str:
            raise ValueError(f"Invalid country assignment for delegate {delegate_key}. Expected a string, got {type(new_country)}.")
        update_delegates(new_country, old_country, delegate_key, current_comm, ConferenceInfo, Delegates)

def sync_with_secondary_storage(SchoolInfo: SchoolInformation, Delegates: SchoolDelegates):
    """
    Syncs finalassignments with Airtable using requests. 
    Parses delegate keys, searches for record IDs, updates 'Committee Assigned' via 
    select_dropdown_option_raw, and updates 'Country' text field via REST API.
    """
    base_id = os.getenv("AirtableBaseID")
    table_name = os.getenv("AirtableTableName")
    if base_id is None or table_name is None:
        raise RuntimeError("Airtable base ID or table name not set in environment variables.")

    for delegate_key, committee, country in zip(Delegates.number, Delegates.committee.values(), Delegates.country.values()):

        # Parse "School Name - #1"
        school_name = SchoolInfo.schoolname

        if '\'' in school_name or '\"' in school_name:
            school_name = school_name.replace('\'', '\\\'').replace('\"', '\\\"')

        # Retrieve record_id from Airtable
        record_id = SecondaryStorage.find_airtable_record_id(base_id=base_id, table_name=table_name, school_name=school_name, delegate_num=str(delegate_key))

        if not record_id:
            print(f"Warning: No matching record found for '{school_name}' (Delegate #{delegate_key})")
            continue

        # 1. Update 'Committee Assigned' using your dropdown helper method
        if committee:
            SecondaryStorage.link_record_by_name(
                base_id=base_id,
                main_table_name=table_name,
                record_id=record_id,
                field_name="Committee Assigned",
                target_table_name = "Committees",
                target_name_field = "Committee Name",
                search_string = committee
            )

        # 2. Update 'Country' (text field) via HTTP PATCH request
        if country:
            SecondaryStorage.update_airtable_text_field(base_id=base_id, table_name=table_name, record_id=record_id, field_name="Country", value=country)

