import os
import sys
import time
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
from Infrastructure import SheetAPI
from Infrastructure import QuestionaryClass
import AssignmentsFunctions

# ---------- CONTROLS -----------
registrationSheetID = "1LgQxP67-pe6JW0lixWacp3ou5UV1f2vmSGVI8j5IPIs" #link to your registration Sheet
sheetname = "Responses"
DoubleGAs = "no" #type yes or no, depending on if there are double delegate GA's this year.
# -------------------------------

SheetsAPI = SheetAPI()
Display = QuestionaryClass()
registrationSheetURL = f"https://docs.google.com/spreadsheets/d/{registrationSheetID}/edit"

def verify_input(GA, Specialized):
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

def confirm_committees(finalassignments, GA_Names, Spec_Names, Crisis_Names, Double_Committees):
    menu_choices = []
    for delegate, details in finalassignments.items():
        current_committee = details[0]
        committee_type = details[1]
        choice_text = f"{delegate}: {current_committee} ({committee_type})"
        menu_choices.append(choice_text)
    selected_choice = Display.display_list(menu_choices)

    if selected_choice == "exit":
        return "exit", None

    delegate_key = selected_choice.split(":")[0].strip() #read result
    current_assignment = finalassignments[delegate_key][0]
    new_committee = Display.typing_with_pre_fill(f"Enter new committee for {delegate_key} (Current: {current_assignment}):", current_assignment)

    #Helper function to check double committees.
    def check_doubles(current_assignment: str, Double_Committees: set, new_committee: str, delegate_key):
        if current_assignment in Double_Committees and new_committee in Double_Committees:
            print("The old committee was a double committee, and so is the new one. Change the other delegate!")
        elif new_committee in Double_Committees:
            print("The new committee is a double committee. You should find a pair for this delegate, if possible.")
        elif current_assignment in Double_Committees:
            print("The old committee was a double committee. Make sure pairings are still correct!")
        else:
            print(f"Updated {delegate_key} to {new_committee.strip()}")
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
            print("Your selected assignment is not the correct committee type or is not a committee name. Please try again.")
    else:
        print("No changes made or invalid committee name entered. Please try again.")
    return selected_choice, finalassignments

def main():
    sheetSchools = SheetsAPI.get_column_data_until_empty(registrationSheetID, sheetname, "C", 2)
    unassignedSchools = AssignmentsFunctions.get_unassigned_schools(sheetSchools, "assignedSchools.csv")

    while unassignedSchools:
        selectedSchool = AssignmentsFunctions.select_school_to_assign(unassignedSchools)
        row = SheetsAPI.find_row_by_string(registrationSheetID, sheetname, "C", selectedSchool)
        output = SheetsAPI.read_cells(registrationSheetID, [f"{sheetname}!R{row}", f"{sheetname}!S{row}", f"{sheetname}!T{row}", f"{sheetname}!U{row}", f"{sheetname}!V{row}", f"{sheetname}!W{row}", f"{sheetname}!X{row}", f"{sheetname}!Y{row}", f"{sheetname}!Q{row}"])
        CountryPrefs, MiddleEasternBloc, AmericanBloc, EuropeanBloc, AsianBloc, AfricanBloc, PacificBloc, SecurityCouncil, numdels = output
        numdels = int(numdels)

        if len(output) == 9:  # check if all 9 cells have values
            names, percentages, spots, double, Committeetype, ranges = SheetsAPI.read_overview(registrationSheetID)

            #pulls from Remaining Assignments for checking and pushing back later.
            availableCountries = SheetsAPI.pull_sheet_data(registrationSheetID, "Remaining Assignments", ranges)

            print("Top 5 country preferences:", "\033[1m" + CountryPrefs + "\033[0m") #print country preferences in bold for visibility.
            print("Middle Eastern Bloc:", "\033[1m" + MiddleEasternBloc + "\033[0m")
            print("American Bloc:", "\033[1m" + AmericanBloc + "\033[0m")
            print("European Bloc:", "\033[1m" + EuropeanBloc + "\033[0m")
            print("Asian Bloc:", "\033[1m" + AsianBloc + "\033[0m")
            print("African Country Bloc:", "\033[1m" + AfricanBloc + "\033[0m")
            print("Pacific Country Bloc:", "\033[1m" + PacificBloc + "\033[0m")
            print("Security Council interest:", "\033[1m" + SecurityCouncil + "\033[0m")
            print("\033[1m" + str(numdels) + "\033[0m", "delegates to assign for this school.")
            
            #data science: school awards from past
            GA = input("How many delegates to put in GA?")
            Specialized = input("How many delegates to put in Specialized?")
            GA, Specialized = verify_input(GA, Specialized)

            if GA + Specialized > numdels:
                print("Error: The total number of delegates does not match the expected count.")
                sys.exit()
            else:
                finalassignments = {} #dictionary with a value being a list of two elements, the committee and the country assigned.
                Crisis = numdels - GA - Specialized
                print("\033[F", end=""); print("\033[F", end=""); print("\033[K", end=""); print("\033[K", end="") #goes 2 lines up and deletes previous 2 lines.
                print(f"GA: {GA}, Specialized: {Specialized}, Crisis: {Crisis}")

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
                singleGAIndices = single_indices["ga"]
                singleSpecIndices = single_indices["specialized"]
                singleCrisisIndices = single_indices["crisis"]
                i = 0; iterator = 0
                committeeCount = (GA, Specialized, Crisis)
                while iterator < GA:
                    data = (names, percentages, double, spots, Committeetype)
                    finalassignments, i, percentages, iterator = AssignmentsFunctions.assign_committee("GA", GaIndices, data, finalassignments, iterator, i, single_indices, selectedSchool, committeeCount) #type: ignore
                iterator = 0
                while iterator < Specialized:
                    data = (names, percentages, double, spots, Committeetype)
                    finalassignments, i, percentages, iterator = AssignmentsFunctions.assign_committee("Specialized", SpecIndices, data, finalassignments, iterator, i, single_indices, selectedSchool, committeeCount) #type: ignore
                iterator = 0
                if SecurityCouncil.lower() != "yes":
                    CrisisInd = [idx for idx in CrisisIndices if names[idx].lower() != "security council" and names[idx].lower() != "historical crisis"]
                while iterator < Crisis:
                    data = (names, percentages, double, spots, Committeetype)
                    finalassignments, i, percentages, iterator = AssignmentsFunctions.assign_committee("Crisis", CrisisInd, data, finalassignments, iterator, i, single_indices, selectedSchool, committeeCount) #type: ignore
                print("\033[K", end="")
                print("Assignments for this school:")
                
                GA_Names = [] ; Spec_Names = [] ; Crisis_Names = [] ; Double_Committees = set()
                singleIndices = singleCrisisIndices + singleGAIndices + singleSpecIndices
                for i in range(len(names)): #build the lists above to pass into functions for verification.
                    if i in GaIndices:
                        GA_Names.append(names[i])
                    elif i in SpecIndices:
                        Spec_Names.append(names[i])
                    elif i in CrisisIndices:
                        Crisis_Names.append(names[i])
                    else:
                        print("There is a committee name error.")
                        sys.exit()
                    if not i in singleIndices:
                        Double_Committees.add(names[i])

                while True:
                    selected_choice, finalassignments = confirm_committees(finalassignments, GA_Names, Spec_Names, Crisis_Names, Double_Committees)
                    #a business logic function that calls display functions.
                    if selected_choice == "exit":
                        break
                CurrentRow = SheetsAPI.get_column_odd_cells( registrationSheetID, "Assignments", "A", 1) + 2
                finalassignments, availableCountries, currentRow = AssignmentsFunctions.add_assignments(finalassignments, availableCountries, CurrentRow, Double_Committees) #, country suggestions list) #here you can add the later data science things for suggestions.
                finalassignments, SchoolAssignmentsCells, remaining_cell_map = SheetsAPI.map_cells(finalassignments, availableCountries, currentRow)
            cont = input("Finished building cell maps. Push? (yes, no)")
            while cont.lower() not in {"yes", "no"}:
                cont = input("Finished building cell maps. Push?")

            #writing to the sheet the cell maps.
            SheetsAPI.write_values_to_sheet_from_dict(registrationSheetID, remaining_cell_map)
            SheetsAPI.write_values_to_sheet_from_dict(registrationSheetID, SchoolAssignmentsCells)
            SheetsAPI.write_values_to_sheet_from_dict(registrationSheetID, {f"Assignments!A{CurrentRow}": selectedSchool})

            #counting local percentages.
            
            time.sleep(5); print("Checking sheet for changes...") #pause for sheet to register changes.
            percentagesChecking = SheetsAPI.read_cells(registrationSheetID, [f"Overview!D{i+2}" for i in range(len(names))])
            percentagesChecking = [float(p.strip('%')) for p in percentagesChecking] # Convert "45%" to 45.0
            if percentagesChecking == percentages:
                print("Percentages are correct. Moving on to next school, and placing name in CSV.")
            else:
                print("Percentage error. Please check the sheet!")
                print(registrationSheetURL)
            AssignmentsFunctions.append_to_csv("assignedSchools.csv", [selectedSchool])
            unassignedSchools.remove(selectedSchool)
        else:
            print("Error: Not all expected cells have values. Please check the sheet for completeness.")
            sys.exit()
    
if __name__ == "__main__":
    main()

"""
Improvements:
Put business logic in main
Split up main function into smaller parts
Fix percentage error
Single Del GA's ?? Allow for single del assignment (user confirmation before twin logic if odd number goes into GA)
System for drops and additions? -- Leave to Sahaj? -- Start with a questionary prompt for adding schools, dropping delegates, adding delegates.
Split up questionary logic. Questionary function should only receive a list and return the selection. No knowledge of business logic. Make it a generator to preserve while loop?
Link assignments up to sheets provided to schools

"""