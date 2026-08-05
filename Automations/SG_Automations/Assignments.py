import os
import sys
import time

import RosterConnector
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
from Assignments_Sheets_Adapter import Assignments_to_Sheets, registration_sheet_ID
from ..Infrastructure import DisplayClass
from difflib import get_close_matches
import ServerRequests
import AssignmentsFunctions

# ---------- CONTROLS -----------
# For things related to the sheets, visit SheetsAPIManager.py to change the information.
DoubleGAs = "no" #type yes or no, depending on if there are double delegate GA's this year.
# -------------------------------

SheetsAPI = Assignments_to_Sheets()
Display = DisplayClass()
registrationSheetURL = f"https://docs.google.com/spreadsheets/d/{registration_sheet_ID}/edit"

def assign_new_schools():
    unassignedSchools = SheetsAPI.find_schools_not_yet_assigned("Responses", "Assignments")
    while unassignedSchools:
        selectedSchool = Display.select_option_with_pointer(unassignedSchools, "Select a school to begin assignments", "SCVMUN ASSIGNMENT ENGINE - PENDING SCHOOLS")
        names, percentages, spots, availableCountries, double, Committeetype, output = SheetsAPI.read_school_and_current_committees_data(selectedSchool)
        single_indices, GaIndices, SpecIndices, CrisisIndices = AssignmentsFunctions.read_committees_overview_from_sheet(Committeetype, double)
        CountryPrefs, MiddleEasternBloc, AmericanBloc, EuropeanBloc, AsianBloc, AfricanBloc, PacificBloc, SecurityCouncil, numdels = output; numdels = int(numdels)
        GA, Specialized, Crisis = AssignmentsFunctions.print_data_to_terminal_with_prompt(DoubleGAs, CountryPrefs, MiddleEasternBloc, AmericanBloc, EuropeanBloc, AsianBloc, AfricanBloc, PacificBloc, SecurityCouncil, numdels, newschool=False)

        if GA + Specialized > numdels:
            Display.display("Error: The total number of delegates does not match the expected count.")
            sys.exit()
        else:
            Display.go_one_line_up(); Display.clear_current_line(); Display.go_one_line_up(); Display.clear_current_line()
            Display.display(f"GA: {GA}, Specialized: {Specialized}, Crisis: {Crisis}")
            
            i = 0; iterator = 0
            finalassignments = {} #dictionary with a value being a list of two elements, the committee and the country assigned.
            committeeCounts = (GA, Specialized, Crisis)
            while iterator < GA:
                data = (names, percentages, double, spots, Committeetype)
                finalassignments, i, percentages, iterator = AssignmentsFunctions.assign_committee("GA", GaIndices, data, finalassignments, iterator, i, single_indices, selectedSchool, committeeCounts)
            iterator = 0
            while iterator < Specialized:
                data = (names, percentages, double, spots, Committeetype)
                finalassignments, i, percentages, iterator = AssignmentsFunctions.assign_committee("Specialized", SpecIndices, data, finalassignments, iterator, i, single_indices, selectedSchool, committeeCounts)
            iterator = 0
            if SecurityCouncil.lower() != "yes":
                CrisisInd = [idx for idx in CrisisIndices if names[idx].lower() != "security council" and names[idx].lower() != "historical crisis"]
            else:
                CrisisInd = CrisisIndices
            while iterator < Crisis:
                data = (names, percentages, double, spots, Committeetype)
                finalassignments, i, percentages, iterator = AssignmentsFunctions.assign_committee("Crisis", CrisisInd, data, finalassignments, iterator, i, single_indices, selectedSchool, committeeCounts) 
            
            GA_Names = [] ; Spec_Names = [] ; Crisis_Names = [] ; Double_Committees = set()
            all_single_indices = set(single_indices["ga"] + single_indices["specialized"] + single_indices["crisis"])
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
                if not i in all_single_indices:
                    Double_Committees.add(names[i])

            finalassignments = AssignmentsFunctions.check_committees_and_build_final_assignments(finalassignments, GA_Names, Spec_Names, Crisis_Names, Double_Committees, availableCountries)
            finalassignments, SchoolAssignmentsCells, remaining_cell_map = SheetsAPI.map_cells(finalassignments, availableCountries)
            cont = Display.take_text_input("Finished building cell maps. Push? (yes, no)")
            while cont.lower() not in {"yes", "no"}:
                cont = Display.take_text_input("Finished building cell maps. Push?")
            if cont != "yes":
                sys.exit()

            #writing to the sheet the cell maps.
            SheetsAPI.push_values(remaining_cell_map)
            SheetsAPI.push_values(SchoolAssignmentsCells)
            SheetsAPI.write_school_name_to_sheet(selectedSchool)
            
            time.sleep(5); Display.display("Checking sheet for changes...") #pause for sheet to register changes.
            percentagesChecking = SheetsAPI.read_percentages_from_overview(names)
            hashes = ServerRequests.add_new_school_or_delegates_to_existing_school_and_request_hashes(finalassignments)
            if percentagesChecking == percentages and hashes != None:
                Display.display("Percentages are correct. Here are the hashes. Moving on to next school, and placing name in completed CSV.")
                Display.display(hashes)
            else:
                Display.display("Percentage error. Please check the sheet! Here are the hashes. Moving on to next school.")
                Display.display(registrationSheetURL)
                Display.display(hashes)
            unassignedSchools.remove(selectedSchool)

            while (cont := Display.take_text_input("Generate a roster and add assignments to it? (yes/no)")) != "yes":
                cont = Display.take_text_input("Generate a roster and add assignments to it? (yes/no)")
            new_roster_ID = RosterConnector.generate_roster_and_add_assignments_to_it(finalassignments, selectedSchool)
            Display.display(f"Roster generated and assignments added. Please check it for errors: https://docs.google.com/spreadsheets/d/{new_roster_ID}/edit")

def add_delegates():
    # Goal: Add delegates to a school that already exists. Scan the sheet for user Display.take_text_inputted school, then prompt user how many delegates to add. Finally, assign new delegates just like with new school registration.
    # Request for new hashes and send this new data to the database.
    
    selectedSchool = Display.take_text_input("Please input the school to add delegates to.")
    committeeCount = int(Display.take_text_input("How many delegates to add?"))

    CurrentSchools = SheetsAPI.get_list_of_current_schools_names()
    while selectedSchool not in CurrentSchools:
        ClosestMatch = get_close_matches(selectedSchool, CurrentSchools, n=1, cutoff=0.6)
        Display.display(f"Display.take_text_input error. Did you mean: {ClosestMatch}?")
        selectedSchool = Display.take_text_input("Please input the school to add delegates to.")

    names, percentages, spots, availableCountries, double, Committeetype, output = SheetsAPI.read_school_and_current_committees_data(selectedSchool)
    single_indices, GaIndices, SpecIndices, CrisisIndices = AssignmentsFunctions.read_committees_overview_from_sheet(Committeetype, double)
    CountryPrefs, MiddleEasternBloc, AmericanBloc, EuropeanBloc, AsianBloc, AfricanBloc, PacificBloc, SecurityCouncil, _ = output
    GA, Specialized, Crisis = AssignmentsFunctions.print_data_to_terminal_with_prompt(DoubleGAs, CountryPrefs, MiddleEasternBloc, AmericanBloc, EuropeanBloc, AsianBloc, AfricanBloc, PacificBloc, SecurityCouncil, committeeCount, newschool=False)
    
    i = 0; iterator = 0
    finalassignments = {} # dictionary with a value being a list of two elements, the committee and the country assigned.
    committeeCounts = (GA, Specialized, Crisis)
    while iterator < GA:
        data = (names, percentages, double, spots, Committeetype)
        finalassignments, i, percentages, iterator = AssignmentsFunctions.assign_committee("GA", GaIndices, data, finalassignments, iterator, i, single_indices, selectedSchool, committeeCounts)
    iterator = 0
    while iterator < Specialized:
        data = (names, percentages, double, spots, Committeetype)
        finalassignments, i, percentages, iterator = AssignmentsFunctions.assign_committee("Specialized", SpecIndices, data, finalassignments, iterator, i, single_indices, selectedSchool, committeeCounts)
    iterator = 0
    if SecurityCouncil.lower() != "yes":
        CrisisInd = [idx for idx in CrisisIndices if names[idx].lower() != "security council" and names[idx].lower() != "historical crisis"]
    else:
        CrisisInd = CrisisIndices
    while iterator < Crisis:
        data = (names, percentages, double, spots, Committeetype)
        finalassignments, i, percentages, iterator = AssignmentsFunctions.assign_committee("Crisis", CrisisInd, data, finalassignments, iterator, i, single_indices, selectedSchool, committeeCounts)
    
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
        all_single_indices = set(single_indices["ga"] + single_indices["specialized"] + single_indices["crisis"])
        if not i in all_single_indices:
            Double_Committees.add(names[i])

    Display.display("Assignments for this school:")
    finalassignments = AssignmentsFunctions.confirm_committees(finalassignments, GA_Names, Spec_Names, Crisis_Names, Double_Committees) # a business logic function that calls display functions.

    #Data science function to generate countrySuggestionsList!
    finalassignments, availableCountries = AssignmentsFunctions.add_assignments(finalassignments, availableCountries, Double_Committees) #, countrySuggestionsList)

    finalassignments, SchoolAssignmentsCells, remaining_cell_map = SheetsAPI.map_cells_for_added_delegates(finalassignments, availableCountries, selectedSchool)
    cont = Display.take_text_input("Finished building cell maps. Push? (yes, no)")
    while cont.lower() not in {"yes", "no"}:
        cont = Display.take_text_input("Finished building cell maps. Push?")
    if cont != "yes":
        sys.exit()

    #writing to the sheet the cell maps.
    SheetsAPI.push_values(remaining_cell_map)
    SheetsAPI.push_values(SchoolAssignmentsCells)
    SheetsAPI.write_school_name_to_sheet(selectedSchool)
    
    time.sleep(5); Display.display("Checking sheet for changes...") #pause for cloud storage system (sheets) to register changes.
    percentagesChecking = SheetsAPI.read_percentages_from_overview(names)
    if percentagesChecking == percentages:
        Display.display("Percentages are correct. Moving on to next school.")
        hashes = ServerRequests.add_new_school_or_delegates_to_existing_school_and_request_hashes(finalassignments)
        Display.display(hashes)
    else:
        Display.display("Percentage error. Please check the sheet! School name placed in completed CSV.")
        Display.display(registrationSheetURL)
        cont = Display.take_text_input("Should we proceed to send new assignments to the database? (yes/no)")
        if cont == "yes":
            hashes = ServerRequests.add_new_school_or_delegates_to_existing_school_and_request_hashes(finalassignments)
            Display.display(hashes)
            cont = Display.take_text_input("Proceed to add these delegates to the roster? (yes/no)")
            if cont == "yes":
                new_roster_ID = RosterConnector.add_delegates_to_existing_school_roster(selectedSchool, finalassignments)
                Display.display(f"Delegates added to roster. Please check it for errors: https://docs.google.com/spreadsheets/d/{new_roster_ID}/edit")
            else:
                Display.display("Aborting roster update. Please check the sheet manually.")
                sys.exit()
        else:
            Display.display("Aborting database update. Please check the sheet manually.")
            sys.exit()

def drop_delegates():
    #Goal: delete delegates from the assignments sheet and move them back to the original pool. Ask user for which school and Display.display all delegate options for drop. Confirm drop, read assignments sheet, then delete them from the assignments sheet.
    # Finally, insert them back into the original pool by reading their committee name, and slotting them back to the first empty cell. Request that these assignments be deleted from the database.
    selectedSchool = Display.take_text_input("Please input the school to drop delegates from.")
    CurrentSchools = SheetsAPI.get_list_of_current_schools_names()
    availableCountries, backup = SheetsAPI.get_available_countries_and_backup_storage(selectedSchool)
    while selectedSchool not in CurrentSchools: #closest match logic for input errors.
        ClosestMatch = get_close_matches(selectedSchool, CurrentSchools, n=1, cutoff=0.6)
        Display.display(f"Display.take_text_input error. Did you mean: {ClosestMatch}?")
        selectedSchool = Display.take_text_input("Please input the school to drop delegates from.")

    list_of_assignments = SheetsAPI.get_existing_assignments_as_list(selectedSchool)

    if list_of_assignments is not None:
        final_list_of_assignments = []
        seen_empty = False
        for assignment in list_of_assignments:
            if assignment and assignment != "":
                final_list_of_assignments.append(assignment)
                if seen_empty == True:
                    print("There is a hole or error in the sheets assignment list! There cannot be an empty cell except for the last few cells.")
            else:
                seen_empty = True

        Display.display("Click exit if you want to cancel the operation. Otherwise, selected the delegates with arrow keys and space. Hit enter to finish.")
        delegates_to_drop = Display.display_list_of_selections_multi_select(final_list_of_assignments, "Select delegate(s) to drop from the school", "Exit")

        if delegates_to_drop == "exit" or not delegates_to_drop:
            Display.display("Operation cancelled. No delegates were dropped.")
            sys.exit()

        for assignment in delegates_to_drop:
            final_list_of_assignments.remove(assignment)
        Display.display(f"Final list of assignments: {final_list_of_assignments}")

        cont = Display.take_text_input("Proceed with dropping the delegates and updating the sheet? (y/n)")
        if cont == "n":
            Display.display("Aborting drop operation.")
            sys.exit()

        SheetsAPI.clear_assignments_currently_in_storage_for_school(selectedSchool)
        
        assigned_cell_map, remaining_cell_map = SheetsAPI.prepare_list_of_assignments_for_push(final_list_of_assignments, availableCountries, delegates_to_drop, selectedSchool)

        SheetsAPI.push_values(assigned_cell_map)
        SheetsAPI.push_values(remaining_cell_map)
        #push back the new assignments to the sheet, and return the dropped delegates to the original pool.

        deleted_hashes = ServerRequests.drop_delegates_from_school_and_delete_hashes(delegates_to_drop)
        if deleted_hashes != {}:
            for delegate, hash_value in deleted_hashes.items():
                Display.display(f"Deleted {delegate} with hash: {hash_value}")
            school_roster_ID = RosterConnector.find_existing_school_roster_ID(selectedSchool)
            Display.display(f"Go into the roster and delete the delegates manually: https://docs.google.com/spreadsheets/d/{school_roster_ID}/edit")
        else:
            Display.display("No delegates were deleted. Please check the server response for errors.")
            SheetsAPI.push_values(backup)
            sys.exit()
        
    else:
        print("The sheet for the school's assignments came back empty. Check the Assignments sheet.")
        sys.exit()


"""
Improvements:
- In the function add_assignments, live update availableCountries instead of waiting until map_cells to do it. This allows better data tracking for later features.
- Prevent duplicate countries from existing in memory by checking finalassignments. This will also be helped by live updating availableCountries.
"""