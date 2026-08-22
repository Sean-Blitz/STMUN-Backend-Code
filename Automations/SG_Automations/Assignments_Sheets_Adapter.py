import sys
from Automations.Infrastructure import DisplayClass
from Automations.Infrastructure import SheetAPI

# ---------------- Controls --------------------
registration_sheet_ID = "1LgQxP67-pe6JW0lixWacp3ou5UV1f2vmSGVI8j5IPIs" # link to your registration Sheet, for assignments.
award_sheet_ID = "1qrqM4EdBO-aqebxhbQ-4NTXnEvpIhSkBfw9lLBY9BMw"
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

    def map_cells_for_added_delegates(self, finalassignments: dict, selectedSchool: str, new_list_of_countries_and_committees: list[list[str]]) -> tuple[dict, dict, dict]:
        schoolrow = self.find_existing_school_row_in_assignments_sheet(selectedSchool)
        availableCountries = self.available_countries_and_coordinates
        # this one appends to the row instead of overwriting it. It also reads the current number of delegates assigned to the school from the sheet, and starts from there.
        cell_map = {}
        assigned_cell_map = {}
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
                #construct school assignments cells. Search for first empty cell (displayed in Sheet)
                assigned_cell_map[f"Assignments!{SheetsAPI.sheets_alphabet(current_number+1)}{schoolrow}" if current_number <= 29 else f"Assignments!{SheetsAPI.sheets_alphabet(current_number-29)}{schoolrow + 1}"] = f"{country} ({committee})"
            current_number += 1
        for coordinate, [committee, country] in availableCountries.items():
            if [committee, country] in new_list_of_countries_and_committees:
                #just iterate through the whole availableCountries map and create a cell map while also changing values to "" for those in final assignments.
                cell_map[coordinate] = country
            elif [committee, country] not in new_list_of_countries_and_committees:
                cell_map[coordinate] = ""
        del self.available_countries_and_coordinates # makes sure that stale data is not used next time.
        return finalassignments, cell_map, assigned_cell_map

    def get_available_countries_and_backup_storage(self, selectedSchool: str):
        names = SheetsAPI.get_column_data_until_empty(registration_sheet_ID, "Overview", "A", 2) # Use this function to also detect number of committees
        raw_ranges = SheetsAPI.read_cells(registration_sheet_ID, [f"Overview!H{i+2}" for i in range(len(names))])
        ranges = {names[i]: raw_ranges[i] for i in range(len(names))}

        self.available_countries_and_coordinates = SheetsAPI.pull_sheet_data(ranges, registration_sheet_ID)  # Populate availableCountries map
        schoolrow = self.find_existing_school_row_in_assignments_sheet(selectedSchool)

        formatted_ranges = [f"Remaining Assignments!{r}" for r in raw_ranges if r] # this block of code saves a backup as a dictionary. Key: cell coordinate. Value: cell value.
        formatted_ranges.append(f"Assignments!B{schoolrow}:AE{schoolrow}")
        formatted_ranges.append(f"Assignments!B{schoolrow+1}:AE{schoolrow+1}")
        backup = SheetsAPI.read_data_for_backup(registration_sheet_ID, formatted_ranges)

        availableCountries = []
        for values in self.available_countries_and_coordinates.values():
            availableCountries.append(values)

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
        names, percentages, spots, double, Committeetype, _, _ = self.read_overview()
        row = SheetsAPI.find_row_by_string(registration_sheet_ID, "Responses", "C", selectedSchool)
        output = SheetsAPI.read_cells(registration_sheet_ID, [f"Responses!R{row}", f"Responses!S{row}", f"Responses!T{row}", f"Responses!U{row}", f"Responses!V{row}", f"Responses!W{row}", f"Responses!Y{row}", f"Responses!Q{row}"])
        #RegionBloc, CountryPref1, CountryPref2, CountryPref3, CountryPref4, CountryPref5, SecurityCouncil, numdels
        return names, percentages, spots, double, Committeetype, output

    def map_cells(self, finalassignments: dict, new_list_of_countries_and_committees: list[list[str]]):
        availableCountries = self.available_countries_and_coordinates
        new_row_in_assignment_sheet = self.find_new_school_row_in_assignments_sheet()
        cell_map = {}
        assigned_cell_map = {}
        j = 0
        for delegate, vals in finalassignments.items():
            if len(vals) == 3:
                committee = vals[0]
                country = vals[2]

                #construct school assignments cells
                assigned_cell_map[f"Assignments!{SheetsAPI.sheets_alphabet(j+1)}{new_row_in_assignment_sheet}" if j <= 29 else f"Assignments!{SheetsAPI.sheets_alphabet(j-29)}{new_row_in_assignment_sheet + 1}"] = f"{country} ({committee})"
            j += 1
        for coordinate, [committee, country] in availableCountries.items():
            if [committee, country] in new_list_of_countries_and_committees:
                cell_map[coordinate] = country
            elif [committee, country] not in new_list_of_countries_and_committees:
                cell_map[coordinate] = ""
        del self.available_countries_and_coordinates # makes sure that stale data is not used next time.
        return finalassignments, cell_map, assigned_cell_map

    def prepare_list_of_assignments_for_push(self, finalassignments: list, delegates_to_drop: list, schoolname):
        schoolrow = self.find_existing_school_row_in_assignments_sheet(schoolname)
        assigned_cell_map, remaining_cell_map = self.map_simple_cells_from_list_and_return_to_pile(finalassignments, schoolrow, delegates_to_drop)
        return assigned_cell_map, remaining_cell_map

    def map_simple_cells_from_list_and_return_to_pile(
            self, 
            finalassignments: list,
            currentRow: int, 
            delegates_to_drop: list
        ):
            """
            Takes a list of cells and a list of delegates to drop (from those cells), reads inside the delegates to drop list elements, which are strings, and find the committee.
            Then place the country assignment outside the committtee into the availableCountries sheet map, and also map the finalassignments into the assignments tab.
            
            available_countries is formatted: {cell_coordinate: [committee, country_name]}
            Returns:
                assigned_cell_map: {sheet_coordinate: "country_name (committee_name)"}
                remaining_cell_map: {sheet_coordinate: country_name}
            """
            # ------------------------------------------------------------------
            # 1. Build assigned_cell_map for the Assignments tab
            # ------------------------------------------------------------------
            assigned_cell_map = {}
            available_countries = self.available_countries_and_coordinates
            
            for j, assignment in enumerate(finalassignments):
                # Index formula across columns B to AE (30 items per row)
                col_letter = SheetsAPI.sheets_alphabet(j + 1) if j <= 29 else SheetsAPI.sheets_alphabet(j - 29)
                row_num = currentRow if j <= 29 else currentRow + 1
                cell_ref = f"Assignments!{col_letter}{row_num}"

                # Handle tuple/list formats [committee, type, country] or raw strings gracefully
                if isinstance(assignment, (list, tuple)):
                    if len(assignment) >= 3:
                        val_str = f"{assignment[2]} ({assignment[0]})" if assignment[2] else ""
                    elif len(assignment) == 2:
                        val_str = f"{assignment[0]} ({assignment[1]})"
                    else:
                        val_str = str(assignment[0]) if assignment else ""
                else:
                    val_str = str(assignment) if assignment is not None else ""

                assigned_cell_map[cell_ref] = val_str

            # ------------------------------------------------------------------
            # 2. Return dropped delegates back into available_countries pile
            # ------------------------------------------------------------------
            avail_dict = dict(available_countries)

            for delegate_str in delegates_to_drop:
                if not delegate_str:
                    continue

                # Parse "Country (Committee)" -> extracts country and committee
                if "(" in delegate_str and delegate_str.endswith(")"):
                    country, committee = delegate_str.rsplit(" (", 1)
                    committee = committee.rstrip(")")
                else:
                    country, committee = delegate_str, ""

                country = country.strip()
                committee = committee.strip()

                # Find an empty cell slot matching this committee
                matched_coord = None
                for coord, val in avail_dict.items():
                    comm_key = val[0] if len(val) > 0 else ""
                    cty_key = val[1] if len(val) > 1 else ""

                    if comm_key.strip().lower() == committee.lower() and (not cty_key or cty_key.strip().lower() in ("", "none", "unassigned")):
                        matched_coord = coord
                        break

                # Assign the country back to the open cell coordinate
                if matched_coord:
                    avail_dict[matched_coord] = [committee, country]

            # Convert available_countries into final cell map format: {sheet_coordinate: country_name}
            remaining_cell_map = {coord: val[1] for coord, val in avail_dict.items()}
            del self.available_countries_and_coordinates
            return assigned_cell_map, remaining_cell_map

    def get_school_awards_data(self, sanitized_school_name) -> str:
        """
        Read school's points from the sheet. If greater than average but below twice of average, return "good". If higher, return "great". 
        If less than average but more than half of average, return "below average", and if less than that, return "unexperienced".
        """
        sheetID = award_sheet_ID

        list_of_school_names_in_awards_sheet = SheetsAPI.get_column_data_until_empty(sheetID, "Sorted", "G", 2)
        sanitized_list_of_school_names_in_awards_sheet = [name.lower().replace("high", "").replace("school", "").replace("hs", "").replace("college", "").replace("preparatory", "").replace("prep", "").strip()
                                                for name in list_of_school_names_in_awards_sheet]

        if sanitized_school_name in sanitized_list_of_school_names_in_awards_sheet:
            row = sanitized_list_of_school_names_in_awards_sheet.index(sanitized_school_name) +2

        else:
            Display.display("Cannot find school in the awards sheet! If you would like, you can input the school's name from the sheet by manually searching here:")
            Display.display(f"https://docs.google.com/spreadsheets/d/{sheetID}/")
            school_name = Display.take_text_input("School name from sheet (type \"n\" if school does not exist)")
            if school_name != "n":
                try:
                    row = list_of_school_names_in_awards_sheet.index(school_name) +2
                except ValueError:
                    Display.display("Cannot find that school in the sheet. If you've updated that sheet while running this code, re-run this code.")
                    Display.display("Otherwise, we default to making this school a \"good\" school in ranking.")
                    return "good"
            else:
                Display.display("Now, we default to making this school a \"good\" school in ranking.")
                return "good"

        school_points = SheetsAPI.read_single_cell(sheetID, f"N{row}")
        average_points = SheetsAPI.read_single_cell(sheetID, f"N{len(list_of_school_names_in_awards_sheet)+2}")

        if school_points and average_points:
            try:
                school_points = int(school_points)
                average_points = int(average_points)
            except ValueError:
                Display.display("Check the sheet and code if the cells are properly formatted and read! Currently the cell that's being read does not contain a whole number.")
                Display.display("We will default to returning \"good\" for this school.")
                return "good"

            if school_points > average_points * 2:
                return "great"
            elif school_points > average_points:
                return "good"
            elif school_points >= average_points / 2:
                return "below average"
            elif average_points / 2 >= school_points:
                return "unexperienced"
            else:
                Display.display("School points is an unexpected value. Check the code and sheets.")
                Display.display("We will default to returning \"good\" for this school.")
                return "good"
        else:
            Display.display("Cells returned nothing or function encountered an error. Check the code and sheet.")
            Display.display("We will default to returning \"good\" for this school.")
            return "good"
