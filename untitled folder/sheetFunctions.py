import string
def write_values_to_sheet_from_dict(service, spreadsheet_id, cell_value_map, value_input_option="USER_ENTERED"):
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

    service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body
    ).execute()

def read_single_cell(service, spreadsheet_id, cell_range):
    """
    Reads a single cell from a Google Sheet.

    Args:
        service: Authenticated Sheets service
        spreadsheet_id (str): Spreadsheet ID
        cell_range (str): A1 notation (e.g. 'Sheet1!B2')

    Returns:
        The cell value (str, number, or None if empty)
    """
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=cell_range
    ).execute()

    values = result.get("values", [])

    if not values or not values[0]:
        return None

    return values[0][0]

def read_single_unformatted_cell(service, spreadsheet_id, cell_range):
    """
    Reads a single cell from a Google Sheet (unformatted value).

    Returns:
        Number, bool, string, or None
    """
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=cell_range,
        valueRenderOption="UNFORMATTED_VALUE"
    ).execute()

    values = result.get("values", [])

    if not values or not values[0]:
        return None

    return values[0][0]

from googleapiclient.discovery import build

def read_cells(service, spreadsheet_id: str, cell_list: list):
    """
    Reads multiple individual cells from a Google Sheet and returns their values
    in the same order as the provided cell_list.

    Parameters:
        service: Authenticated Google Sheets API service instance.
        spreadsheet_id (str): The ID of the Google Sheet.
        cell_list (list): List of A1-notation cell references, e.g. ["A1", "B2"].

    Returns:
        list: Values in the same order as cell_list. Empty cells return None.
    """

    # Batch request for all cells
    result = service.spreadsheets().values().batchGet(
        spreadsheetId=spreadsheet_id,
        ranges=cell_list
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

from googleapiclient.discovery import build

def get_column_until_empty(service, sheet_id, sheet_name, column_letter, start_row):
    """
    Reads down a specific column in Google Sheets and returns all values 
    until it hits an empty cell.
    """    
    # 2. Construct the range string (e.g., "Sheet1!A2:A" fetches to the bottom)
    range_string = f"{sheet_name}!{column_letter}{start_row}:{column_letter}"
    
    # 3. Make a single API call to fetch the data
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=sheet_id, range=range_string).execute()
    
    # The API returns a list of lists, like [['Data1'], ['Data2'], [], ['Data4']]
    values = result.get('values', [])
    
    collected_data = []
    
    # 4. Loop through the fetched values and stop at the first blank
    for row in values:
        # Google Sheets API represents an empty cell either as an empty list `[]` 
        # or a list containing an empty string `['']`
        if not row or not str(row[0]).strip():
            break  # Exit the loop as soon as an empty cell is found
            
        collected_data.append(row[0])
        
    return len(collected_data)

def get_column_data_until_empty(service, sheet_id, sheet_name, column_letter, start_row):
    """
    Reads down a specific column in Google Sheets and returns all values 
    until it hits an empty cell.
    """    
    # 2. Construct the range string (e.g., "Sheet1!A2:A" fetches to the bottom)
    range_string = f"{sheet_name}!{column_letter}{start_row}:{column_letter}"
    
    # 3. Make a single API call to fetch the data
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=sheet_id, range=range_string).execute()
    
    # The API returns a list of lists, like [['Data1'], ['Data2'], [], ['Data4']]
    values = result.get('values', [])
    
    collected_data = []
    
    # 4. Loop through the fetched values and stop at the first blank
    for row in values:
        # Google Sheets API represents an empty cell either as an empty list `[]` 
        # or a list containing an empty string `['']`
        if not row or not str(row[0]).strip():
            break  # Exit the loop as soon as an empty cell is found
            
        collected_data.append(row[0])
        
    return collected_data

def find_row_by_string(sheet_api, spreadsheet_id, sheet_name, column_letter, search_string):
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
        request = sheet_api.values().get(
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
        print(f"Warning: '{search_string}' not found in column {column_letter}.")
        return None
        
    except Exception as e:
        print(f"API Error searching column {column_letter}: {e}")
        return None
    
def sheets_alphabet(n):
    """
    Takes a number as input and returns the corresponding column letter.
    """
    alphabet = string.ascii_uppercase
    result = ""
    if n >= 0 and n <= 25:
        result = alphabet[n]
    if n > 25:
        result = alphabet[(n//26)-1] + alphabet[n % 26]
    return result

def get_column_odd_cells(service, sheet_id, sheet_name, column_letter, start_row):
    """
    Reads down a specific column in Google Sheets and returns all values 
    until it hits an empty odd cell.
    """    
    range_string = f"{sheet_name}!{column_letter}{start_row}:{column_letter}"
    
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=sheet_id, range=range_string).execute()
    
    values = result.get('values', [])
    collected_data = []
    
    for i in range(len(values)):
        # Calculate the actual physical spreadsheet row number
        current_spreadsheet_row = start_row + i
        
        # Safe check: first see if the row list is completely empty
        is_empty = False
        if not values[i] or len(values[i]) == 0:
            is_empty = True
        elif not str(values[i][0]).strip():
            is_empty = True
            
        # If it's empty, check if the PHYSICAL spreadsheet row is odd
        if is_empty:
            if current_spreadsheet_row % 2 != 0:
                break  # Stop tracking immediately if it's an empty odd row!
            else:
                # If it's an empty EVEN row, your rules say keep going.
                # We append a blank placeholder string so your index matches up.
                collected_data.append("")
                continue

        # If it's not empty, grab the cell data safely
        collected_data.append(values[i][0])
        
    return len(collected_data)

