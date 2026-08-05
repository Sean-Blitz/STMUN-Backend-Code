from ..Infrastructure import DisplayClass
from ..Infrastructure import SheetAPI
import sys

# ---------------- Controls --------------------
registration_sheet_ID = "1LgQxP67-pe6JW0lixWacp3ou5UV1f2vmSGVI8j5IPIs" # link to your registration Sheet, for assignments.
registrationSheetResponsesName = "Responses" # Name of the tab in the registration sheet that contains the responses.
# ----------------------------------------------

SheetsAPI = SheetAPI()
Display = DisplayClass()

class Assignments_to_Sheets:
    def find_schools_not_yet_assigned(self, registrationSheetName, assignmentsSheetName) -> list[str] | None:
        """
        Compares the list of schools in the registration sheet with those already assigned in the assignments sheet.

        Parameters:
            sheet_id (str): The ID of the Google Sheet.
            registrationSheetName (str): The name of the registration sheet/tab.
            assignmentsSheetName (str): The name of the assignments sheet/tab.
        """

        # 1. Read all schools from the registration sheet (assuming they are in column C)
        registration_range = f"{registrationSheetName}!C2:C"  # Skip header
        registration_response = SheetsAPI.service.spreadsheets().values().get(
            spreadsheetId=registration_sheet_ID,
            range=registration_range
        ).execute()
        registered_schools = {row[0].strip() for row in registration_response.get("values", []) if row}

        # 2. Read all assigned schools from the assignments sheet (assuming they are in column A)
        assigned_schools = SheetsAPI.get_column_odd_cells_data(registration_sheet_ID, assignmentsSheetName, "A", 2)  # Skip header
        assigned_schools = {school.strip() for school in assigned_schools if school}

        # 3. Determine which schools are registered but not yet assigned
        unassigned_schools = registered_schools - assigned_schools

        return list(unassigned_schools) if unassigned_schools else None

    def read_percentages_from_overview(self, names: list[str]) -> list[float]:
        """
        Reads the percentages from the Overview sheet and returns them as a dictionary.
        Assumes the Overview sheet stores percentages from D2 and onwards (down to the length of the committee names)
        """
        percentagesChecking = SheetsAPI.read_cells(registration_sheet_ID, [f"Overview!D{i+2}" for i in range(len(names))])
        percentagesChecking = [float(p.strip('%')) for p in percentagesChecking] # Convert "45%" to 45.0

        return percentagesChecking

    def push_values(self, dict_to_push: dict[str, str]) -> None:
        """
        Pushes values to the Google Sheet based on a dictionary mapping of cell addresses to values.

        Parameters:
            dict_to_push (dict): A dictionary where keys are cell addresses (e.g., "A1") and values are the corresponding values to write.
        """
        SheetsAPI.write_values_to_sheet_from_dict(registration_sheet_ID, dict_to_push)

    def get_list_of_current_schools_names(self) -> list[str]:
        """
        Retrieves the current list of school names from the assignments sheet.

        Returns:
            list[str]: A list of school names currently in the assignments sheet.
        """
        return SheetsAPI.get_column_odd_cells_data(registration_sheet_ID, "Assignments", "A", 2)  # Skip header

    def write_school_name_to_sheet(self, school_name: str) -> None:
        """
        Writes a school name to the assignments sheet at the specified row.

        Parameters:
            school_name (str): The name of the school to write.
            row_number (int): The row number where the school name should be written.
        """
        row_number = self.find_new_school_row_in_assignments_sheet()
        cell_address = f"Assignments!A{row_number}"
        SheetsAPI.write_values_to_sheet_from_dict(registration_sheet_ID, {cell_address: school_name})

    def find_new_school_row_in_assignments_sheet(self) -> int:
        new_row_in_assignment_sheet = SheetsAPI.get_column_odd_cells(registration_sheet_ID, "Assignments", "A", 1) + 2
        return new_row_in_assignment_sheet

    def find_existing_school_row_in_assignments_sheet(self, school_name: str) -> int:
        if (schoolrow:= SheetsAPI.find_row_by_string(registration_sheet_ID, "Assignments", "A", school_name)) is None:
            Display.display(f"Error: Could not find the row for {school_name} in the Assignments sheet.")
            sys.exit()
        return schoolrow

    def map_cells_for_added_delegates(self, finalassignments: dict, availableCountries, selectedSchool: str):
        schoolrow = self.find_existing_school_row_in_assignments_sheet(selectedSchool)
        # this one appends to the row instead of overwriting it. It also reads the current number of delegates assigned to the school from the sheet, and starts from there.
        cell_map = {}
        assigned_cell_map = {}
        checkingSet = set()
        current_number = SheetsAPI.read_single_cell(registration_sheet_ID, [f"Assignments!A{schoolrow+1}"])
        if current_number is not None:
            current_number = int(current_number)
        else:
            print(f"Warning: Could not read the current number from Assignments!A{schoolrow+1}. Please check the sheet.")
            sys.exit(1)
        for delegate, vals in finalassignments.items():
            if len(vals) == 3:
                committee = vals[0]
                country = vals[2]
                checkingSet.add(f"{committee.lower()}, {country.lower()}")

                #construct school assignments cells. Search for first empty cell (displayed in Sheet)
                assigned_cell_map[f"Assignments!{SheetsAPI.sheets_alphabet(current_number+1)}{schoolrow}" if current_number <= 29 else f"Assignments!{SheetsAPI.sheets_alphabet(current_number-29)}{schoolrow + 1}"] = f"{country} ({committee})"
            current_number += 1
        for (committee, country), coordinate in availableCountries.items():
            if (f"{committee.lower()}, {country.lower()}") in checkingSet:
                #just iterate through the whole availableCountries map and create a cell map while also changing values to "" for those in final assignments.
                cell_map[coordinate] = ""
            elif (f"{committee.lower()}, {country.lower()}") not in checkingSet:
                cell_map[coordinate] = country
        return finalassignments, cell_map, assigned_cell_map

    def get_available_countries_and_backup_storage(self, selectedSchool: str):
        names = SheetsAPI.get_column_data_until_empty(registration_sheet_ID, "Overview", "A", 2) # Use this function to also detect number of committees
        raw_ranges = SheetsAPI.read_cells(registration_sheet_ID, [f"Overview!H{i+2}" for i in range(len(names))])
        ranges = {names[i]: raw_ranges[i] for i in range(len(names))}

        availableCountries = SheetsAPI.pull_sheet_data(ranges, registration_sheet_ID)  # Populate availableCountries map
        schoolrow = self.find_existing_school_row_in_assignments_sheet(selectedSchool)

        formatted_ranges = [f"Remaining Assignments!{r}" for r in raw_ranges if r] # this block of code saves a backup as a dictionary. Key: cell coordinate. Value: cell value.
        formatted_ranges.append(f"Assignments!B{schoolrow}:AE{schoolrow}")
        formatted_ranges.append(f"Assignments!B{schoolrow+1}:AE{schoolrow+1}")
        backup = SheetsAPI.read_data_for_backup(registration_sheet_ID, formatted_ranges)

        return availableCountries, backup

    def get_existing_assignments_as_list(self, selectedSchool: str):
        """
        Retrieves the existing assignments for a given school from the Assignments sheet.

        Parameters:
            selectedSchool (str): The name of the school to retrieve assignments for."""

        schoolrow = self.find_existing_school_row_in_assignments_sheet(selectedSchool)
        row1 = SheetsAPI.read_row_from(registration_sheet_ID, "Assignments", schoolrow, "B") or []
        row2 = SheetsAPI.read_row_from(registration_sheet_ID, "Assignments", schoolrow + 1, "B") or []

        # Combine the two rows into a single list of assignments
        existing_assignments = row1 + row2

        return existing_assignments

    def clear_assignments_currently_in_storage_for_school(self, selectedSchool: str):
        """
        Clears the existing assignments for a given school in the Assignments sheet.

        Parameters:
            selectedSchool (str): The name of the school to clear assignments for.
        """
        schoolrow = self.find_existing_school_row_in_assignments_sheet(selectedSchool)
        SheetsAPI.clear_row_from(registration_sheet_ID, "Assignments", schoolrow, "B", num_columns=30)
        SheetsAPI.clear_row_from(registration_sheet_ID, "Assignments", schoolrow + 1, "B", num_columns=30)

    def read_overview(self):
        names = SheetsAPI.get_column_data_until_empty(registration_sheet_ID, "Overview", "A", 2) # Use this function to also detect number of committees
        percentages = SheetsAPI.read_cells(registration_sheet_ID, [f"Overview!D{i+2}" for i in range(len(names))])
        percentages = [float(p.strip('%')) for p in percentages] # Convert "45%" to 45.0
        spots = SheetsAPI.read_cells(registration_sheet_ID, [f"Overview!C{i+2}" for i in range(len(names))])
        spots = [int(s) for s in spots] # Convert spot counts to integers
        double = SheetsAPI.read_cells(registration_sheet_ID, [f"Overview!E{i+2}" for i in range(len(names))])
        type = SheetsAPI.read_cells(registration_sheet_ID, [f"Overview!F{i+2}" for i in range(len(names))])
        raw_ranges = SheetsAPI.read_cells(registration_sheet_ID, [f"Overview!H{i+2}" for i in range(len(names))])
        ranges = {names[i]: raw_ranges[i] for i in range(len(names))}
        return names, percentages, spots, double, type, ranges, raw_ranges

    def read_school_and_current_committees_data(self, selectedSchool):
        names, percentages, spots, double, Committeetype, ranges, raw_ranges = self.read_overview()
        availableCountries = SheetsAPI.pull_sheet_data(ranges, registration_sheet_ID)
        row = SheetsAPI.find_row_by_string(registration_sheet_ID, "Responses", "C", selectedSchool)
        output = SheetsAPI.read_cells(registration_sheet_ID, [f"Responses!R{row}", f"Responses!S{row}", f"Responses!T{row}", f"Responses!U{row}", f"Responses!V{row}", f"Responses!W{row}", f"Responses!X{row}", f"Responses!Y{row}", f"Responses!Q{row}"])
        
        return names, percentages, spots, availableCountries, double, Committeetype, output

    def map_cells(self, finalassignments: dict, availableCountries):
        new_row_in_assignment_sheet = self.find_new_school_row_in_assignments_sheet()
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
                assigned_cell_map[f"Assignments!{SheetsAPI.sheets_alphabet(j+1)}{new_row_in_assignment_sheet}" if j <= 29 else f"Assignments!{SheetsAPI.sheets_alphabet(j-29)}{new_row_in_assignment_sheet + 1}"] = f"{country} ({committee})"
            j += 1
        for (committee, country), coordinate in availableCountries.items():
            if (f"{committee.lower()}, {country.lower()}") in checkingSet:
                #just iterate through the whole availableCountries map and create a cell map while also changing values to "" for those in final assignments.
                cell_map[coordinate] = ""
            elif (f"{committee.lower()}, {country.lower()}") not in checkingSet:
                cell_map[coordinate] = country
        return finalassignments, cell_map, assigned_cell_map

    def prepare_list_of_assignments_for_push(self, finalassignments: list, availableCountries: dict, delegates_to_drop: list, schoolname):
        schoolrow = self.find_existing_school_row_in_assignments_sheet(schoolname)
        assigned_cell_map, remaining_cell_map = SheetsAPI.map_simple_cells_from_list_and_return_to_pile(finalassignments, availableCountries, schoolrow, delegates_to_drop)
        return assigned_cell_map, remaining_cell_map

    