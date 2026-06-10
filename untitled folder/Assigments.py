import os
import sys
import time
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

import driveFunctions
import sheetFunctions
import AssignmentsFunctions

SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/documents']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'
registrationSheetID = "1LgQxP67-pe6JW0lixWacp3ou5UV1f2vmSGVI8j5IPIs"
registrationSheetURL = f"https://docs.google.com/spreadsheets/d/{registrationSheetID}/edit"
sheetname = "Responses"

def authenticate():
    """
    Handles OAuth login and returns valid credentials.
    """
    creds = None

    # Load existing token
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If no valid credentials, log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token for next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    return creds

creds = authenticate()
drive_service = driveFunctions.get_drive_service(creds)
sheets_service = build('sheets', 'v4', credentials=creds)

sheetSchools = sheetFunctions.get_column_data_until_empty(sheets_service, registrationSheetID, sheetname, "C", 2)
unassignedSchools = AssignmentsFunctions.get_unassigned_schools(sheetSchools, "assignedSchools.csv")
#you should import the entire unassigned positions sheet before the loop, and finish pushing back after all schools are done.

while unassignedSchools:
    selectedSchool = AssignmentsFunctions.select_school_to_assign(unassignedSchools)
    row = sheetFunctions.find_row_by_string(sheets_service, registrationSheetID, sheetname, "C", selectedSchool)
    output = sheetFunctions.read_cells(sheets_service, registrationSheetID, [f"{sheetname}!R{row}", f"{sheetname}!S{row}", f"{sheetname}!T{row}", f"{sheetname}!U{row}", f"{sheetname}!V{row}", f"{sheetname}!W{row}", f"{sheetname}!X{row}", f"{sheetname}!Y{row}", f"{sheetname}!Q{row}"])
    CountryPrefs, MiddleEasternBloc, AmericanBloc, EuropeanBloc, AsianBloc, AfricanBloc, PacificBloc, SecurityCouncil, numdels = output
    numdels = int(numdels)

    if len(output) == 9:  # check if all 9 cells have values
        names = sheetFunctions.get_column_data_until_empty(sheets_service, registrationSheetID, "Overview", "A", 2) # Use this function to also detect number of committees
        percentages = sheetFunctions.read_cells(sheets_service, registrationSheetID, [f"Overview!D{i+2}" for i in range(len(names))])
        percentages = [float(p.strip('%')) for p in percentages] # Convert "45%" to 45.0
        spots = sheetFunctions.read_cells(sheets_service, registrationSheetID, [f"Overview!C{i+2}" for i in range(len(names))])
        spots = [int(s) for s in spots] # Convert spot counts to integers
        double = sheetFunctions.read_cells(sheets_service, registrationSheetID, [f"Overview!E{i+2}" for i in range(len(names))])
        type = sheetFunctions.read_cells(sheets_service, registrationSheetID, [f"Overview!F{i+2}" for i in range(len(names))])
        ranges = sheetFunctions.read_cells(sheets_service, registrationSheetID, [f"Overview!H{i+2}" for i in range(len(names))])
        ranges = {names[i]: ranges[i] for i in range(len(names))}

        #pulls from Remaining Assignments for checking and pushing back later.
        availableCountries = AssignmentsFunctions.pull_sheet_data(sheets_service, registrationSheetID, "Remaining Assignments", ranges)

        print("Top 5 country preferences:", "\033[1m" + CountryPrefs + "\033[0m") #print country preferences in bold for visibility.
        print("Middle Eastern Bloc:", "\033[1m" + MiddleEasternBloc + "\033[0m")
        print("American Bloc:", "\033[1m" + AmericanBloc + "\033[0m")
        print("European Bloc:", "\033[1m" + EuropeanBloc + "\033[0m")
        print("Asian Bloc:", "\033[1m" + AsianBloc + "\033[0m")
        print("African Country Bloc:", "\033[1m" + AfricanBloc + "\033[0m")
        print("Pacific Country Bloc:", "\033[1m" + PacificBloc + "\033[0m")
        print("Security Council interest:", "\033[1m" + SecurityCouncil + "\033[0m")
        print("\033[1m" + str(numdels) + "\033[0m", "delegates to assign for this school.")

        GA = int(input("How many delegates to put in GA?"))
        Specialized = int(input("How many delegates to put in Specialized?"))
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
            for index, (kind, is_double) in enumerate(zip(type, double)):
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
            i = 0
            iterator = 0
            committeeCount = (GA, Specialized, Crisis)
            while iterator < GA:
                data = (names, percentages, double, spots)
                finalassignments, i, percentages = AssignmentsFunctions.assign_committee("GA", indices, data, finalassignments, iterator, i, single_indices, selectedSchool, committeeCount)
            iterator = 0
            while iterator < Specialized:
                data = (names, percentages, double, spots)
                finalassignments, i, percentages = AssignmentsFunctions.assign_committee("Specialized", indices, data, finalassignments, iterator, i, single_indices, selectedSchool, committeeCount)
            iterator = 0
            while iterator < Crisis:
                data = (names, percentages, double, spots)
                finalassignments, i, percentages = AssignmentsFunctions.assign_committee("Crisis", indices, data, finalassignments, iterator, i, single_indices, selectedSchool, committeeCount)
            print("\033[K", end="")
            print("Assignments for this school:")
            
            GA_Names = [] ; Spec_Names = [] ; Crisis_Names = [] ; Double_Committees = set()
            singleIndicies = CrisisIndices + GaIndices + SpecIndices
            for i in range(len(names)):
                if i in GaIndices:
                    GA_Names.append(names[i])
                elif i in SpecIndices:
                    Spec_Names.append(names[i])
                elif i in CrisisIndices:
                    Crisis_Names.append(names[i])
                else:
                    print("There is a committee name error.")
                    sys.exit()
                if not i in singleIndicies:
                    Double_Committees.add(names[i])

            finalassignments = AssignmentsFunctions.confirm_committees(finalassignments, GA_Names, Spec_Names, Crisis_Names, Double_Committees)
            CurrentRow = sheetFunctions.get_column_odd_cells(sheets_service, registrationSheetID, "Assignments", "A", 1) + 2
            finalassignments, remaining_cell_map, SchoolAssignmentsCells = AssignmentsFunctions.add_assignments_and_map_cells(finalassignments, availableCountries, CurrentRow, Double_Committees) #, country suggestions list) #here you can add the later data science things for suggestions.

        cont = input("Finished building cell maps. Push?")
        while cont.lower() not in {"yes", "no"}:
            cont = input("Finished building cell maps. Push?")

        #writing to the sheet the cell maps.
        sheetFunctions.write_values_to_sheet_from_dict(sheets_service, registrationSheetID, remaining_cell_map)
        sheetFunctions.write_values_to_sheet_from_dict(sheets_service, registrationSheetID, SchoolAssignmentsCells)
        sheetFunctions.write_values_to_sheet_from_dict(sheets_service, registrationSheetID, {f"Assignments!A{CurrentRow}": selectedSchool})

        #counting local percentages.
        
        time.sleep(5); print("Checking sheet for changes...") #pause for sheet to register changes.
        percentagesChecking = sheetFunctions.read_cells(sheets_service, registrationSheetID, [f"Overview!D{i+2}" for i in range(len(names))])
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

        """
        Additional improvements:
        Put things into functions, especially the while statements above.
        """