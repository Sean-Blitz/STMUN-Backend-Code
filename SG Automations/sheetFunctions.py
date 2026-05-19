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