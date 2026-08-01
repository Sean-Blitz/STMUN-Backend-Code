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
import AssignmentsFunctions

# ---------- CONTROLS -----------
registrationSheetID = "1LgQxP67-pe6JW0lixWacp3ou5UV1f2vmSGVI8j5IPIs" #link to your registration Sheet
sheetname = "Responses"
DoubleGAs = "no" #type yes or no, depending on if there are double delegate GA's this year.
# -------------------------------

SheetsAPI = SheetAPI()
Display = DisplayClass()
Storage = CSV()
registrationSheetURL = f"https://docs.google.com/spreadsheets/d/{registrationSheetID}/edit"

def assign_new_schools():
    sheetSchools = SheetsAPI.get_column_data_until_empty(registrationSheetID, sheetname, "C", 2)
    unassignedSchools = Storage.find_non_overlap_string(sheetSchools, "assignedSchools.csv")
    while unassignedSchools:
        selectedSchool = Display.select_option_with_pointer(unassignedSchools, "Select a school to begin assignments", "SCVMUN ASSIGNMENT ENGINE - PENDING SCHOOLS")
        names, percentages, spots, availableCountries, single_indices, GaIndices, SpecIndices, CrisisIndices, GA, Specialized, Crisis, SecurityCouncil, numdels, double, Committeetype = AssignmentsFunctions.read_school_and_current_committees_data(sheetname, registrationSheetID, selectedSchool, DoubleGAs)

        if GA + Specialized > numdels:
            Display.display("Error: The total number of delegates does not match the expected count.")
            sys.exit()
        else:
            Display.go_one_line_up(); Display.clear_current_line(); Display.go_one_line_up(); Display.clear_current_line()
            Display.display(f"GA: {GA}, Specialized: {Specialized}, Crisis: {Crisis}")
            
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

            finalassignments, CurrentRow = AssignmentsFunctions.check_committees_and_build_final_assignments(finalassignments, GA_Names, Spec_Names, Crisis_Names, Double_Committees, availableCountries, registrationSheetID)
            finalassignments, SchoolAssignmentsCells, remaining_cell_map = SheetsAPI.map_cells(finalassignments, availableCountries, CurrentRow)
            cont = Display.take_text_input("Finished building cell maps. Push? (yes, no)")
            while cont.lower() not in {"yes", "no"}:
                cont = Display.take_text_input("Finished building cell maps. Push?")
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
    # Goal: Add delegates to a school that already exists. Scan the sheet for user Display.take_text_inputted school, then prompt user how many delegates to add. Finally, assign new delegates just like with new school registration.
    # Request for new hashes and send this new data to the database.
    
    selectedSchool = Display.take_text_input("Please input the school to add delegates to.")
    committeeCount = int(Display.take_text_input("How many delegates to add?"))

    CurrentSchools = SheetsAPI.get_column_odd_cells_data(registrationSheetID, "Assignments", "A", 2)
    while selectedSchool not in CurrentSchools:
        ClosestMatch = get_close_matches(selectedSchool, CurrentSchools, n=1, cutoff=0.6)
        Display.display(f"Display.take_text_input error. Did you mean: {ClosestMatch}?")
        selectedSchool = Display.take_text_input("Please input the school to add delegates to.")

    schoolrow = SheetsAPI.find_row_by_string(registrationSheetID, "Assignments", "A", selectedSchool)

    names, percentages, spots, availableCountries, single_indices, GaIndices, SpecIndices, CrisisIndices, GA, Specialized, Crisis, SecurityCouncil, numdels, double, Committeetype = AssignmentsFunctions.read_school_and_current_committees_data(sheetname, registrationSheetID, selectedSchool, DoubleGAs, committeeCount)
    
    i = 0; iterator = 0
    finalassignments = {} #dictionary with a value being a list of two elements, the committee and the country assigned.
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
        all_single_indices = set(single_indices["ga"] + single_indices["specialized"] + single_indices["crisis"])
        if not i in all_single_indices:
            Double_Committees.add(names[i])

    Display.display("Assignments for this school:")
    finalassignments = AssignmentsFunctions.confirm_committees(finalassignments, GA_Names, Spec_Names, Crisis_Names, Double_Committees) # a business logic function that calls display functions.

    #Data science function to generate countrySuggestionsList!
    finalassignments, availableCountries = AssignmentsFunctions.add_assignments(finalassignments, availableCountries, Double_Committees) #, countrySuggestionsList)

    finalassignments, SchoolAssignmentsCells, remaining_cell_map = SheetsAPI.map_cells_for_added_delegates(finalassignments, availableCountries, schoolrow, registrationSheetID)
    cont = Display.take_text_input("Finished building cell maps. Push? (yes, no)")
    while cont.lower() not in {"yes", "no"}:
        cont = Display.take_text_input("Finished building cell maps. Push?")
    if cont != "yes":
        sys.exit()

    #writing to the sheet the cell maps.
    SheetsAPI.write_values_to_sheet_from_dict(registrationSheetID, remaining_cell_map)
    SheetsAPI.write_values_to_sheet_from_dict(registrationSheetID, SchoolAssignmentsCells)
    SheetsAPI.write_values_to_sheet_from_dict(registrationSheetID, {f"Assignments!A{schoolrow}": selectedSchool})
    
    time.sleep(5); Display.display("Checking sheet for changes...") #pause for sheet to register changes.
    percentagesChecking = SheetsAPI.read_cells(registrationSheetID, [f"Overview!D{i+2}" for i in range(len(names))])
    percentagesChecking = [float(p.strip('%')) for p in percentagesChecking] if percentagesChecking else [] # Convert "45%" to 45.0
    if percentagesChecking == percentages:
        Display.display("Percentages are correct. Moving on to next school, and placing name in completed CSV.")
        hashes = ServerRequests.add_new_school_or_delegates_to_existing_school_and_request_hashes(finalassignments)
        Display.display(hashes)
    else:
        Display.display("Percentage error. Please check the sheet! School name placed in completed CSV.")
        Display.display(registrationSheetURL)
        cont = Display.take_text_input("Should we proceed to send new assignments to the database? (yes/no)")
        if cont == "yes":
            hashes = ServerRequests.add_new_school_or_delegates_to_existing_school_and_request_hashes(finalassignments)
            Display.display(hashes)
        else:
            Display.display("Aborting database update. Please check the sheet manually.")
            sys.exit()

def drop_delegates():
    #Goal: delete delegates from the assignments sheet and move them back to the original pool. Ask user for which school and Display.display all delegate options for drop. Confirm drop, read assignments sheet, then delete them from the assignments sheet.
    # Finally, insert them back into the original pool by reading their committee name, and slotting them back to the first empty cell. Request that these assignments be deleted from the database.
    selectedSchool = Display.take_text_input("Please input the school to drop delegates from.")
    CurrentSchools = SheetsAPI.get_column_odd_cells_data(registrationSheetID, "Assignments", "A", 2)
    names, percentages, spots, double, Committeetype, ranges, raw_ranges = AssignmentsFunctions.read_overview(registrationSheetID)
    availableCountries = SheetsAPI.pull_sheet_data(registrationSheetID, "Remaining Assignments", ranges)
    while selectedSchool not in CurrentSchools: #closest match logic for input errors.
        ClosestMatch = get_close_matches(selectedSchool, CurrentSchools, n=1, cutoff=0.6)
        Display.display(f"Display.take_text_input error. Did you mean: {ClosestMatch}?")
        selectedSchool = Display.take_text_input("Please input the school to drop delegates from.")
    
    schoolrow = SheetsAPI.find_row_by_string(registrationSheetID, "Assignments", "A", selectedSchool)
    if schoolrow is None:
        Display.display(f"Error: Could not find the row for {selectedSchool} in the Assignments sheet.")
        sys.exit()

    formatted_ranges = [f"Remaining Assignments!{r}" for r in raw_ranges if r] # this block of code saves a backup as a dictionary. Key: cell coordinate. Value: cell value.
    raw_ranges.append(f"Assignments!B{schoolrow}:AE{schoolrow}")
    raw_ranges.append(f"Assignments!B{schoolrow+1}:AE{schoolrow+1}")
    backup = SheetsAPI.create_state_backup(registrationSheetID, raw_ranges)

    row1 = SheetsAPI.read_row_from(registrationSheetID, "Assignments", schoolrow, "B") or []
    row2 = SheetsAPI.read_row_from(registrationSheetID, "Assignments", schoolrow + 1, "B") or []
    list_of_assignments = row1 + row2  # Combine both rows, treating None as empty list

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

        SheetsAPI.clear_row_from(registrationSheetID, "Assignments", schoolrow, start_column='B', num_columns=30); SheetsAPI.clear_row_from(registrationSheetID, "Assignments", schoolrow + 1, start_column='B', num_columns=30) # wipe the rows clean before pushing back
        
        assigned_cell_map, remaining_cell_map = SheetsAPI.map_simple_cells_from_list_and_return_to_pile(final_list_of_assignments, availableCountries, schoolrow, delegates_to_drop) #type:ignore

        SheetsAPI.write_values_to_sheet_from_dict(registrationSheetID, assigned_cell_map)
        SheetsAPI.write_values_to_sheet_from_dict(registrationSheetID, remaining_cell_map)
        #push back the new assignments to the sheet, and return the dropped delegates to the original pool.

        deleted_hashes = ServerRequests.drop_delegates_from_school_and_delete_hashes(delegates_to_drop) #type:ignore
        if deleted_hashes != {}:
            for delegate, hash_value in deleted_hashes.items():
                Display.display(f"Deleted {delegate} with hash: {hash_value}")
        else:
            Display.display("No delegates were deleted. Please check the server response for errors.")
            SheetsAPI.write_values_to_sheet_from_dict(registrationSheetID, backup)
            sys.exit()
        
    else:
        print("The sheet for the school's assignments came back empty. Check the Assignments sheet.")
        sys.exit()


        
"""
Improvements:
Split up main function into smaller parts
Fix percentage error
Link assignments up to sheets provided to schools.
"""