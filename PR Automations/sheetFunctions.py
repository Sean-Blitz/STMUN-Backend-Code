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

def read_columns_until_blank(spreadsheet_id: str, sheet_name: str, num_columns: int, gc):
    """
    Read values from the leftmost `num_columns` columns of a Google Sheet worksheet,
    skipping the first row (header) for each column, and stop reading a column when
    the first blank cell is encountered. Returns a dict mapping 1-based column index
    (1 = leftmost column A) -> list of cell values (strings).

    Parameters:
      - spreadsheet_id: Google Sheets file ID (string)
      - sheet_name: worksheet/tab name (string)
      - num_columns: number of columns to read starting from the very left (int > 0)
      - gc: an authenticated gspread client (already configured by caller)

    Example return:
      {1: ['val_row2_colA', 'val_row3_colA'], 2: ['val_row2_colB'], 3: []}
    """
    if not isinstance(num_columns, int) or num_columns <= 0:
        raise ValueError("num_columns must be a positive integer")

    sh = gc.open_by_key(spreadsheet_id)
    ws = sh.worksheet(sheet_name)

    all_rows = ws.get_all_values()  # list of rows; each row is a list of strings
    # If sheet is completely empty, ensure we have at least an empty list for header handling
    if all_rows is None:
        all_rows = []

    result = {}
    # For each column index starting at 0 (leftmost), collect values from row 2 onward
    for col_idx in range(num_columns):
        values = []
        # iterate rows starting from second row (skip header). If there is no header row,
        # this will iterate an empty list and produce an empty values list.
        for row in all_rows[1:]:
            cell = row[col_idx] if col_idx < len(row) else ""
            if cell is None or cell == "":
                break
            values.append(cell)
        result[col_idx + 1] = values  # use 1-based column numbering for keys

    return result

def read_headers(spreadsheet_id: str, sheet_name: str, num_columns: int, gc):
    """
    Read the first row (header) from the worksheet, returning exactly `num_columns`
    values from the leftmost columns. If the header row has fewer entries than
    num_columns, the returned list is padded with empty strings.

    Parameters:
      - spreadsheet_id: Google Sheets file ID (string)
      - sheet_name: worksheet/tab name (string)
      - num_columns: number of header values to return starting from the very left (int > 0)
      - gc: an authenticated gspread client (already configured by caller)

    Returns:
      - list of strings of length num_columns (header values from columns A..)
    """
    if not isinstance(num_columns, int) or num_columns <= 0:
        raise ValueError("num_columns must be a positive integer")

    sh = gc.open_by_key(spreadsheet_id)
    ws = sh.worksheet(sheet_name)

    all_rows = ws.get_all_values() or []
    if not all_rows:
        return [""] * num_columns

    header_row = all_rows[0]
    header_values = []
    for col_idx in range(num_columns):
        header_values.append(header_row[col_idx] if col_idx < len(header_row) else "")

    return header_values
