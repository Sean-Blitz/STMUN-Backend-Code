import re
import string
from googleapiclient.discovery import build
from .GoogleAPIsManager import GoogleAPIs
from Infrastructure.utilities import retry_on_http_error
from ..Display.DisplayManager import DisplayClass

Display = DisplayClass()

class SheetAPI(GoogleAPIs):
    def __init__(self, SCOPES = None, CREDENTIALS_FILE = None, TOKEN_FILE = None):
        if SCOPES is None:
            super().__init__(CREDENTIALS_FILE=CREDENTIALS_FILE, TOKEN_FILE=TOKEN_FILE)
            # As defined in the parent class, if Credentials or Token file is none, it will default to the standard locations.
        elif SCOPES is not None:
            super().__init__(SCOPES=SCOPES, CREDENTIALS_FILE=CREDENTIALS_FILE, TOKEN_FILE=TOKEN_FILE)
        else:
            raise ValueError("SCOPES must be a list of scopes or None.")
        creds = self.authenticate()
        self.service = build('sheets', 'v4', credentials=creds)

    @retry_on_http_error()
    def write_values_to_sheet_from_dict(self, spreadsheet_id, cell_value_map, value_input_option="USER_ENTERED"):
        """
        Writes different values to different cells/ranges in one API call.
        Args:
            service: Authenticated Sheets service
            spreadsheet_id (str): Spreadsheet ID
            cell_value_map (dict): {
                "Sheet1!A1": "Hello",
                "Sheet1!B2": "World",
                "Sheet1!C3": "42"
            }
            value_input_option (str): 'USER_ENTERED' or 'RAW'
        """
        data = []

        for cell_range, value in cell_value_map.items():
            data.append({
                "range": cell_range,
                "values": [[value]]
            })

        body = {
            "valueInputOption": value_input_option,
            "data": data
        }

        self.service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body
        ).execute()

    def read_single_cell(self, spreadsheet_id: str, cell_range: str):
        """
        Reads a single cell from a Google Sheet.
        Args:
            spreadsheet_id (str): Spreadsheet ID
            cell_range (str): A1 notation (e.g. 'Sheet1!B2')

        Returns:
            The cell value (str, number, or None if empty)
        """
        return self.read_cells(spreadsheet_id, [cell_range])[0]

    @retry_on_http_error()
    def read_cells(self, spreadsheet_id: str, cell_list: list, value_render_option: str = "FORMATTED_VALUE"):
        """
        Reads multiple individual cells from a Google Sheet and returns their values
        in the same order as the provided cell_list.
        
        Parameters:
            spreadsheet_id (str): The ID of the Google Sheet.
            cell_list (list): List of A1-notation cell references, e.g. ["A1", "B2"].
            value_render_option (str): How values are rendered. Defaults to "FORMATTED_VALUE";
                pass "UNFORMATTED_VALUE" to get raw numbers instead of formatted text.

        Returns:
            list: Values in the same order as cell_list. Empty cells return None.
        """
        ranges = cell_list

        # Batch request for all cells
        result = self.service.spreadsheets().values().batchGet(
            spreadsheetId=spreadsheet_id,
            ranges=ranges,
            valueRenderOption=value_render_option
        ).execute()

        value_ranges = result.get("valueRanges", [])

        output = []
        for vr in value_ranges:
            values = vr.get("values", [])
            if values and values[0]:
                output.append(values[0][0])  # First row, first column
            else:
                output.append(None)  # Empty cell

        return output

    @retry_on_http_error()
    def _read_column(self, sheet_id, sheet_name, column_letter, start_row):
        """Fetches the raw values of one column from start_row down (single API call)."""
        range_string = f"{sheet_name}!{column_letter}{start_row}:{column_letter}"
        result = self.service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=range_string
        ).execute()
        return result.get('values', [])

    def get_column_until_empty(self, sheet_id, sheet_name, column_letter, start_row):
        """Returns how many contiguous non-empty values are in a column."""
        return len(self.get_column_data_until_empty(sheet_id, sheet_name, column_letter, start_row))

    def get_column_data_until_empty(self, sheet_id, sheet_name, column_letter, start_row):
        """Returns column values until the first blank cell."""
        collected_data = []
        for row in self._read_column(sheet_id, sheet_name, column_letter, start_row):
            if not row or not str(row[0]).strip():
                break
            collected_data.append(row[0])
        return collected_data

    @retry_on_http_error()
    def find_row_by_string(self, spreadsheet_id, sheet_name, column_letter, search_string):
        """
        Searches down a specific column in Google Sheets for a string value
        and returns its 1-indexed row number.
        
        Arguments:
        sheet_api: Your authorized Google Sheets API v4 service object.
        spreadsheet_id (str): The unique ID of your Google Spreadsheet.
        sheet_name (str): The name of the specific tab (e.g., 'Form Responses').
        column_letter (str): The column to search down (e.g., 'A' or 'B').
        search_string (str): The exact value you are looking for (e.g., a school name).
        
        Returns:
        int: The 1-indexed row number if found.
        None: If the string is not found in the column.
        """
        # Define the range to read the entire column (e.g., 'Form Responses!A:A')
        range_to_search = f"{sheet_name}!{column_letter}:{column_letter}"
        
        try:
            # Request the column values from the API
            request = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_to_search
            )
            response = request.execute()
            
            # Extract the list of lists. Each inner list represents a row's column value.
            column_values = response.get('values', [])
            
            # Loop through the rows to find a match
            for index, row in enumerate(column_values):
                # Check if the row has data and matches our target string (cleaned of edge spaces)
                if row and row[0].strip().lower() == search_string.strip().lower():
                    # API indices are 0-based, so row 1 is index 0. 
                    # We add 1 to return a human-readable row number for Google Sheets.
                    return index + 1
                    
            # If the loop finishes without hitting the return statement, the string wasn't found
            Display.display(f"Warning: '{search_string}' not found in column {column_letter}.")
            return None
            
        except Exception as e:
            Display.display(f"API Error searching column {column_letter}: {e}")
            return None

    def sheets_alphabet(self, n):
        """
        Takes a 0-indexed integer and returns the corresponding column letter string.
        0 -> 'A', 25 -> 'Z', 26 -> 'AA', 40 -> 'AO', 44 -> 'AS'
        """
        result = []
        while n >= 0:
            result.append(string.ascii_uppercase[n % 26])
            n = (n // 26) - 1
        return "".join(reversed(result))

    def _parse_range_start(self, range_str: str):
        """
        Parses a range like "Sheet!A1:C5" or "A1:C5" and returns the top-left cell as
        (sheet_name, zero-indexed column, one-indexed row).
        """
        sheet_name, cell_part = range_str.split("!", 1) if "!" in range_str else ("", range_str)
        start_cell = cell_part.split(":")[0]
        start_col_str = "".join(c for c in start_cell if c.isalpha()).upper()
        start_row_num = int("".join(c for c in start_cell if c.isdigit()))
        start_col_idx = 0
        for char in start_col_str:
            start_col_idx = start_col_idx * 26 + (ord(char) - ord('A') + 1)
        return sheet_name, start_col_idx - 1, start_row_num

    def get_column_odd_cells(self, sheet_id, sheet_name, column_letter, start_row):
        """Returns how many values get_column_odd_cells_data would return."""
        return len(self.get_column_odd_cells_data(sheet_id, sheet_name, column_letter, start_row))

    def get_column_odd_cells_data(self, sheet_id, sheet_name, column_letter, start_row) -> list:
        """
        Reads down a column until the first blank cell on an odd physical row.
        Blank cells on even rows are preserved as "" so indices stay aligned.
        """
        collected_data = []
        for i, row in enumerate(self._read_column(sheet_id, sheet_name, column_letter, start_row)):
            current_spreadsheet_row = start_row + i
            if not row or not str(row[0]).strip():
                if current_spreadsheet_row % 2 != 0:
                    break
                collected_data.append("")
                continue
            collected_data.append(row[0])
        return collected_data

    @retry_on_http_error()
    def read_headers_until_blank(self, spreadsheet_id, sheet_name):
        """
        Reads the first row (header) from the worksheet, stopping at the first blank cell.

        Args:
            spreadsheet_id (str): Google Sheet ID.
            sheet_name (str): Worksheet/tab name.
            service: Authenticated Google Sheets API service.

        Returns:
            List[str]: Header values from leftmost column until first blank.
        """
        # Request the entire first row
        range_name = f"{sheet_name}!1:1"  # row 1
        response = self.service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()

        rows = response.get("values", [])
        if not rows:
            return []

        header_row = rows[0]

        # Collect values until first blank
        header_values = []
        for cell in header_row:
            if cell.strip() == "":
                break
            header_values.append(cell)

        return header_values

    @retry_on_http_error()
    def read_columns_until_blank(self, spreadsheet_id, sheet_name, num_columns):
        """
        Read values from the leftmost `num_columns` columns of a Google Sheet worksheet,
        skipping the first row (header), stopping at first blank cell in each column.

        Returns:
            {1: [...], 2: [...], ...}
        """

        if not isinstance(num_columns, int) or num_columns <= 0:
            raise ValueError("num_columns must be a positive integer")

        # Request entire sheet (safe unless extremely large)
        range_name = f"{sheet_name}"

        response = self.service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()

        all_rows = response.get("values", [])

        result = {}

        for col_idx in range(num_columns):
            values = []

            # Skip header row (row index 0)
            for row in all_rows[1:]:
                cell = row[col_idx] if col_idx < len(row) else ""

                if not cell:  # Stops at first blank
                    break

                values.append(cell)

            result[col_idx + 1] = values

        return result

    @retry_on_http_error()
    def read_row_from(
        self, 
        spreadsheet_id: str, 
        sheet_name: str, 
        row_number: int, 
        start_column: str = "A"
    ) -> list:
        """
        Reads an entire row from a Google Sheet starting from a specified column.

        Parameters:
            service: Authenticated Google Sheets API service instance.
            spreadsheet_id (str): The ID of the Google Sheet.
            sheet_name (str): The name of the tab/sheet.
            row_number (int): The 1-indexed row number to read (e.g., 5).
            start_column (str): The starting column in A1 notation (e.g., "C"). Defaults to "A".

        Returns:
            list: A list of cell values for that row starting from `start_column`.
                Returns an empty list if the row or cells are empty.
        """
        # Sanitize and format the range (e.g., "'Responses'!C5:5")
        # Using 'C5:5' fetches from Column C to the last populated column in Row 5.
        range_name = f"'{sheet_name}'!{start_column.upper()}{row_number}:{row_number}"

        # Call the Google Sheets API
        result = self.service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()

        values = result.get("values", [])

        # values is a list of rows (e.g., [["val1", "val2", ...]])
        if values:
            return values[0]
        
        return []

    @retry_on_http_error()
    def clear_row_from(
        self, 
        spreadsheet_id: str, 
        sheet_name: str, 
        row_number: int, 
        start_column: str = "A", 
        num_columns: int = 26
    ) -> dict:
        """
        Clears a row in a Google Sheet by overwriting cells with empty strings ("").

        Parameters:
            service: Authenticated Google Sheets API service instance.
            spreadsheet_id (str): The ID of the Google Sheet.
            sheet_name (str): The name of the tab/sheet.
            row_number (int): The 1-indexed row number to clear (e.g., 5).
            start_column (str): The column letter to start clearing from (e.g., "B"). Defaults to "A".
            num_columns (int): How many columns to clear starting from start_column. Defaults to 26.

        Returns:
            dict: The API update response from Google Sheets.
        """
        # 1. Generate a row of empty strings based on how many columns you want to clear
        empty_row = [[""] * num_columns]

        # 2. Construct the range name (e.g., "'Assignments'!B5")
        range_name = f"'{sheet_name}'!{start_column.upper()}{row_number}"

        # 3. Call the API to overwrite the cells
        response = self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body={"values": empty_row}
        ).execute()

        return response

    @retry_on_http_error()
    def read_data_for_backup(self, spreadsheet_id: str, ranges_list: list) -> dict:
        """
        Reads multiple ranges from a Google Sheet in a single API call and maps
        every individual cell coordinate to its current value for rollback purposes.

        Parameters:
            spreadsheet_id (str): The ID of the spreadsheet.
            ranges_list (list): List of range strings (e.g., ["Assignments!A1:C5", "Overview!A1:B10"])

        Returns:
            dict: Flattened dictionary with exact cell coordinates as keys.
                Example: {"Assignments!A1": "Lincoln High", "Assignments!B1": "USA (GA)"}
        """
        if not ranges_list:
            return {}

        response = self.service.spreadsheets().values().batchGet(
            spreadsheetId=spreadsheet_id,
            ranges=ranges_list,
            valueRenderOption="FORMATTED_VALUE"
        ).execute()

        backup_map = {}
        for vr in response.get("valueRanges", []):
            range_str = vr.get("range", "")
            values = vr.get("values", [])
            if not range_str or not values:
                continue

            sheet_name, start_col_num, start_row_num = self._parse_range_start(range_str)
            prefix = f"{sheet_name}!" if sheet_name else ""
            for r_idx, row in enumerate(values):
                current_row = start_row_num + r_idx
                for c_idx, cell_value in enumerate(row):
                    backup_map[f"{prefix}{self.sheets_alphabet(start_col_num + c_idx)}{current_row}"] = cell_value

        return backup_map

    @retry_on_http_error()
    def pull_sheet_data(self, ranges, sheet_id):
        """
        Pulls all data from ranges into RAM.

        Returns:
            {
                "Remaining Assignments!D21": ["GA", "Germany"],
                "Remaining Assignments!D22": ["GA", "Germany"],
                "Remaining Assignments!D23": ["GA", "France"],
                ...
            }

        The sheet coordinate uniquely identifies each available assignment,
        so duplicate country names within the same committee are preserved.
        """
        sheet_name = "Remaining Assignments"
        full_ranges = [f"{sheet_name}!{r}" for r in ranges.values()]

        result = self.service.spreadsheets().values().batchGet(
            spreadsheetId=sheet_id,
            ranges=full_ranges
        ).execute()

        availability_map = {}
        for (committee_name, raw_range_str), value_range_obj in zip(ranges.items(), result.get('valueRanges', [])):
            rows = value_range_obj.get('values', [])
            if not rows:
                continue

            _, start_col_idx, start_row_num = self._parse_range_start(raw_range_str)

            for row_offset, row in enumerate(rows):
                for col_offset, cell_value in enumerate(row):
                    country_name = cell_value.strip()
                    if "(" in country_name:
                        country_name = country_name.split("(", 1)[0].strip()

                    if not country_name or country_name.lower() == "unassigned":
                        continue

                    current_row_abs = start_row_num + row_offset
                    current_col_abs_letter = self.sheets_alphabet(start_col_idx + col_offset)
                    availability_map[f"{sheet_name}!{current_col_abs_letter}{current_row_abs}"] = [
                        committee_name,
                        country_name
                    ]

        return availability_map

    def get_column_data(self, sheet_id, sheet_name, column_letter, start_row):
        """Reads down a column and returns every value, using "" for blank cells."""
        return [row[0] if row else "" for row in self._read_column(sheet_id, sheet_name, column_letter, start_row)]

    def get_sheet_id_by_name(self, spreadsheet_id: str, sheet_name: str) -> int:
        """Fetches the numeric sheetId (gid) for a given sheet/tab name."""
        spreadsheet = self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        for sheet in spreadsheet.get('sheets', []):
            if sheet['properties']['title'] == sheet_name:
                return sheet['properties']['sheetId']
        raise ValueError(f"Sheet with name '{sheet_name}' not found.")

    @retry_on_http_error()
    def get_sheet_names(self, spreadsheet_id: str) -> list[str]:
        """Fetches the names of all tabs in a spreadsheet, in their current order."""
        spreadsheet = self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        return [sheet['properties']['title'] for sheet in spreadsheet.get('sheets', [])]

    @retry_on_http_error()
    def rename_sheet_tab(self, spreadsheet_id: str, old_sheet_name: str, new_sheet_name: str) -> dict:
        """
        Renames a tab in a Google Sheet.

        Parameters:
            spreadsheet_id (str): The ID of the Google Sheet.
            old_sheet_name (str): The current name of the tab.
            new_sheet_name (str): The new name for the tab.

        Returns:
            dict: The API batchUpdate response.
        """
        sheet_id = self.get_sheet_id_by_name(spreadsheet_id, old_sheet_name)

        return self.service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={
                "requests": [
                    {
                        "updateSheetProperties": {
                            "properties": {
                                "sheetId": sheet_id,
                                "title": new_sheet_name,
                            },
                            "fields": "title",
                        }
                    }
                ]
            }
        ).execute()

    @retry_on_http_error()
    def copy_sheet_tab_to_front(self, spreadsheet_id: str, source_sheet_name: str, new_sheet_name: str) -> int:
        """
        Copies an existing tab (searched by name) within the same spreadsheet, renames the copy,
        and moves it to the first position (index 0).

        Parameters:
            spreadsheet_id (str): The ID of the Google Sheet.
            source_sheet_name (str): The name of the existing tab to copy.
            new_sheet_name (str): The name to give the copied tab.

        Returns:
            int: The numeric sheetId (gid) of the newly created tab.
        """
        source_sheet_id = self.get_sheet_id_by_name(spreadsheet_id, source_sheet_name)

        response = self.service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={
                "requests": [
                    {
                        "duplicateSheet": {
                            "sourceSheetId": source_sheet_id,
                            "insertSheetIndex": 0,
                            "newSheetName": new_sheet_name,
                        }
                    }
                ]
            }
        ).execute()

        return response["replies"][0]["duplicateSheet"]["properties"]["sheetId"]

    def set_cell_background_color(self, spreadsheet_id, sheet_name, row, col, red=1.0, green=1.0, blue=1.0):
        """
        Changes the background color of a specific cell in a Google Sheet.

        Args:
            service: Authenticated Google Sheets API service object.
            spreadsheet_id (str): The ID of the spreadsheet.
            sheet_id (int): The numeric ID of the specific sheet/tab (gid).
            row (int): 0-indexed row number (e.g., row 1 is index 0).
            col (int): 0-indexed column number (e.g., column A is index 0).
            red (float): Red color component from 0.0 to 1.0.
            green (float): Green color component from 0.0 to 1.0.
            blue (float): Blue color component from 0.0 to 1.0.
        """
        sheet_id = self.get_sheet_id_by_name(spreadsheet_id, sheet_name)
        body = {
            "requests": [{"repeatCell": {"range": {"sheetId": sheet_id,"startRowIndex": row,"endRowIndex": row + 1,"startColumnIndex": col,"endColumnIndex": col + 1,},
                        "cell": {"userEnteredFormat": {"backgroundColor": {"red": red,"green": green,"blue": blue,}}},
                        "fields": "userEnteredFormat.backgroundColor",}}]}

        return self.service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body
        ).execute()

    def a1_to_rowcol(self, a1_string, zero_indexed=True):
        """
        Converts an A1 notation string (e.g., "B3", "$C$10") to (row, column) numbers.
        Handles absolute '$' references automatically.
        """
        # Remove any absolute cell reference signs ($)
        clean_string = a1_string.replace('$', '').upper()
        
        # Match the column letter part and the row number part
        match = re.match(r"^([A-Z]+)([0-9]+)$", clean_string)
        if not match:
            raise ValueError(f"Invalid A1 notation format: {a1_string}")
            
        col_str, row_str = match.groups()
        
        # Convert column letters to a number (Base 26)
        col = 0
        for char in col_str:
            col = col * 26 + (ord(char) - ord('A') + 1)
            
        row = int(row_str)
        
        # Adjust for zero-indexing if requested
        if zero_indexed:
            return row - 1, col - 1
        
        return row, col
      
    def get_2d_range(self, spreadsheet_id: str, sheet_name: str, top_left: str, bottom_right: str) -> list[list]:
        """
        Reads a rectangular range from a Google Sheet and returns a 2D list of values.
        
        :param service: An authorized Google Sheets API service object
        :param spreadsheet_id: The ID of the spreadsheet
        :param sheet_name: Name of the sheet tab (e.g., "Sheet1")
        :param top_left: Top-left cell coordinate (e.g., "A1")
        :param bottom_right: Bottom-right cell coordinate (e.g., "D10")
        :return: A 2D list where each inner list represents a row of cell values
        """
        # Construct A1 notation range (e.g., "Sheet1!A1:D10")
        range_name = f"{sheet_name}!{top_left}:{bottom_right}"
        
        # Call the Sheets API
        result = self.service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
        
        # Extract row values; returns empty list if range contains no data
        rows = result.get('values', [])
        
        return rows
