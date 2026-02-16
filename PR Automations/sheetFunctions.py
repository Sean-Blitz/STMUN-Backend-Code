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

def read_columns_until_blank(spreadsheet_id, sheet_name, num_columns, service):
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

    response = service.spreadsheets().values().get(
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

def read_headers(spreadsheet_id, sheet_name, num_columns, service):
    """
    Read the first row (header) from the worksheet, returning exactly `num_columns`
    values from the leftmost columns. Pads with empty strings if needed.
    """

    if not isinstance(num_columns, int) or num_columns <= 0:
        raise ValueError("num_columns must be a positive integer")

    # Convert column number to letter (A, B, C, ...)
    last_column_letter = string.ascii_uppercase[num_columns - 1]

    # Only request first row up to needed column
    range_name = f"{sheet_name}!A1:{last_column_letter}1"

    response = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()

    rows = response.get("values", [])

    if not rows:
        return [""] * num_columns

    header_row = rows[0]

    header_values = []
    for col_idx in range(num_columns):
        header_values.append(
            header_row[col_idx] if col_idx < len(header_row) else ""
        )

    return header_values
