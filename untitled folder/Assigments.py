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

sheetSchools = sheetFunctions.get_column_data_until_empty(sheets_service, registrationSheetID, sheetname, "A", 2)
unassignedSchools = AssignmentsFunctions.get_unassigned_schools(sheetSchools, "assignedSchools.csv")
#you should import the entire unassigned positions sheet before the loop, and finish pushing back after all schools are done.

while unassignedSchools:
    selectedSchool = AssignmentsFunctions.select_school_to_assign(unassignedSchools)
    row = sheetFunctions.find_row_by_string(sheets_service, registrationSheetID, sheetname, "A", selectedSchool)
    output = sheetFunctions.read_cells(sheets_service, registrationSheetID, [f"{sheetname}!R{row}", f"{sheetname}!S{row}", f"{sheetname}!T{row}", f"{sheetname}!U{row}", f"{sheetname}!V{row}", f"{sheetname}!W{row}", f"{sheetname}!X{row}", f"{sheetname}!Y{row}", f"{sheetname}!Q{row}"])
    CountryPrefs = output[0]
    MiddleEasternBloc = output[1]
    AmericanBloc = output[2]
    EuropeanBloc = output[3]
    AsianBloc = output[4]
    AfricanBloc = output[5]
    PacificBloc = output[6]
    SecurityCouncil = output[7]
    numdels = int(output[8])
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

        print("Top 5 country preferences:", CountryPrefs)
        print("Middle Eastern Bloc:", MiddleEasternBloc)
        print("American Bloc:", AmericanBloc)
        print("European Bloc:", EuropeanBloc)
        print("Asian Bloc:", AsianBloc)
        print("African Country Bloc:", AfricanBloc)
        print("Pacific Country Bloc:", PacificBloc)
        print("Security Council interest:", SecurityCouncil)

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
            while i < GA:
                row = min(GaIndices, key = lambda x: percentages[x]) #find the lowest percentage GA committee
                committee = names[row]
                if double[row].lower() == "true" and GA - i > 1: #if double delegate committee and enough GA assignmentspots left.
                    finalassignments[f"{selectedSchool} - #{i+1}"] = [committee, type[row], ""]
                    finalassignments[f"{selectedSchool} - #{i+2}"] = [committee, type[row], ""]
                    percentages[row] += 2 * (100/spots[row]) #update percentage as if two delegates were added.
                    i = i + 2 #skip the next delegate since we just assigned it.
                elif double[row].lower() == "true" and GA - i == 1: #if double delegate commmittee and not enough GA assignment spots left
                    row = min(singleGAIndices, key = lambda x: percentages[x]) #only scans single del GA's
                    committee = names[row]
                    finalassignments[f"{selectedSchool} - #{i+1}"] = [committee, type[row], ""]
                    percentages[names.index(committee)] += (100/spots[names.index(committee)])
                    i = i +1
                elif double[row].lower() == "false": #if single delegate committee
                    finalassignments[f"{selectedSchool} - #{i+1}"] = [committee, type[row], ""]
                    percentages[row] += (100/spots[row])
                    i = i + 1
                else:
                    print("Error in assignment logic.")
                    if input("Continue? (y/n)") == "y":
                        i = i + 1
                    elif input("Continue? (y/n)") == "n":
                        sys.exit(0)
            i = 0
            while i < Specialized:
                row = min(SpecIndices, key = lambda x: percentages[x]) #find the lowest percentage Specialized committee
                committee = names[row]
                if double[row].lower() == "true" and Specialized - i > 1: #if double delegate committee and enough Specialized spots left.
                    finalassignments[f"{selectedSchool} - #{i+1}"] = [committee, type[row], ""]
                    finalassignments[f"{selectedSchool} - #{i+2}"] = [committee, type[row], ""]
                    percentages[row] += 2 * (100/spots[row]) #update percentage as if two delegates were added.
                    i = i + 2 #skip the next delegate since we just assigned it.
                elif double[row].lower() == "true" and Specialized - i == 1: #if double delegate commmittee and not enough Specialized spots left
                    row = min(singleSpecIndices, key = lambda x: percentages[x]) #only scans single del Specialized's
                    committee = names[row]
                    finalassignments[f"{selectedSchool} - #{i+1}"] = [committee, type[row], ""]
                    percentages[names.index(committee)] += (100/spots[names.index(committee)])
                    i = i +1
                elif double[row].lower() == "false": #if single delegate committee
                    finalassignments[f"{selectedSchool} - #{i+1}"] = [committee, type[row], ""]
                    percentages[row] += (100/spots[row])
                    i = i + 1
                else:
                    print("Error in assignment logic.")
                    if input("Continue? (y/n)") == "y":
                        i = i + 1
                    elif input("Continue? (y/n)") == "n":
                        sys.exit(0)
            i = 0
            while i < Crisis:
                row = min(CrisisIndices, key = lambda x: percentages[x]) #find the lowest percentage Crisis committee
                committee = names[row]
                if double[row].lower() == "true" and Crisis - i > 1: #if double delegate committee and enough Crisis spots left.
                    finalassignments[f"{selectedSchool} - #{i+1}"] = [committee, type[row], ""]
                    finalassignments[f"{selectedSchool} - #{i+2}"] = [committee, type[row], ""]
                    percentages[row] += 2 * (100/spots[row]) #update percentage as if two delegates were added.
                    i = i + 2 #skip the next delegate since we just assigned it.
                elif double[row].lower() == "true" and Crisis - i == 1: #if double delegate commmittee and not enough Crisis spots left
                    row = min(singleCrisisIndices, key = lambda x: percentages[x]) #only scans single del Crisis's
                    committee = names[row]
                    finalassignments[f"{selectedSchool} - #{i+1}"] = [committee, type[row], ""]
                    percentages[names.index(committee)] += (100/spots[names.index(committee)])
                    i = i +1
                elif double[row].lower() == "false": #if single delegate committee
                    finalassignments[f"{selectedSchool} - #{i+1}"] = [committee, type[row], ""]
                    percentages[row] += (100/spots[row])
                    i = i + 1
                else:
                    print("Error in assignment logic.")
                    if input("Continue? (y/n)") == "y":
                        i = i + 1
                    elif input("Continue? (y/n)") == "n":
                        sys.exit(0)
            print("Assignments for this school:")
            
            finalassignments = AssignmentsFunctions.confirm_committees(finalassignments, names)
            CurrentRow = sheetFunctions.get_column_odd_cells(sheets_service, registrationSheetID, "Assignments", "A", 1) + 2
            finalassignments, remaining_cell_map, SchoolAssignmentsCells = AssignmentsFunctions.add_assignments_and_map_cells(finalassignments, availableCountries, CurrentRow) #, country suggestions list) #here you can add the later data science things for suggestions.
        unassignedSchools.remove(selectedSchool)

        #writing to the sheet the cell maps.
        sheetFunctions.write_values_to_sheet_from_dict(sheets_service, registrationSheetID, remaining_cell_map)
        sheetFunctions.write_values_to_sheet_from_dict(sheets_service, registrationSheetID, SchoolAssignmentsCells)

        #counting local percentages.
        
        time.sleep(5); print("Checking sheet for changes...") #pause for sheet to register changes.
        percentagesChecking = sheetFunctions.read_cells(sheets_service, registrationSheetID, [f"Overview!D{i+2}" for i in range(len(names))])
        percentagesChecking = [float(p.strip('%')) for p in percentagesChecking] # Convert "45%" to 45.0
        if percentagesChecking == percentages:
            print("Percentages are correct. Moving on to next school, and placing name in CSV.")
        AssignmentsFunctions.append_to_csv("assignedSchools.csv", [selectedSchool])
    else:
        print("Error: Not all expected cells have values. Please check the sheet for completeness.")