import os

from Infrastructure.GoogleAPIs.DriveAPIManager import DriveAPI
from Infrastructure.GoogleAPIs.SheetsAPIManager import SheetAPI
from dotenv import load_dotenv; load_dotenv()

SheetsAPI = SheetAPI()

todolist_sheetname = "To-Do List"
assignments_made = "Assignments"
roster_link = "Roster"
roster_sent = "Roster Sent"
invoice_column_names = ["Invoice 1", "Invoice 2", "Invoice 3", "Final Invoice"]
invoice_sent_column_names = ["Sent (1)", "Sent (2)", "Sent (3)", "Sent (F)"]
invoice_email_col_name = "Email Doc"
countries_assigned_col_name = "Countries Assigned"

class TodoList():
    def __init__(self):
        self.drive = DriveAPI()
        self.sheet = SheetAPI()
        self.todolist_sheet_id = os.getenv("todolist_sheet_id")
        self.headers = self.__get_header_columns_list()

    def __get_header_columns_list(self):
        """Pre-condition: header row must have no blanks before the last header."""
        return SheetsAPI.read_headers_until_blank(self.todolist_sheet_id, todolist_sheetname)

    def __get_header_column(self, header_name):
        """Pre-condition: header row must have no blanks before the last header."""
        index = self.headers.index(header_name)
        return SheetsAPI.sheets_alphabet(index)

    def __place_value_in_cell(self, row, column, value):
        """Places a value in a specific cell in the to-do list."""
        cell_address = f"{column}{row}"
        cell_value_map = {cell_address: value}
        SheetsAPI.write_values_to_sheet_from_dict(spreadsheet_id=self.todolist_sheet_id, cell_value_map=cell_value_map)

    def __mark_or_unmark_to_do(self, school_row, col_number, todo=True):
        """Marks a school as to do in the to-do list."""
        # Find column letter for to_do header
        cell = f"{col_number}{school_row}"
        row, col = SheetsAPI.a1_to_rowcol(cell) # returns 0 indexed int conversions
        if todo == True:
            SheetsAPI.set_cell_background_color(self.todolist_sheet_id, row, col, 1.0, 1.0, 0.0)  # Yellow color
        elif todo == False:
            SheetsAPI.set_cell_background_color(self.todolist_sheet_id, row, col, 1.0, 1.0, 1.0)  # White color
        else:
            raise ValueError("Invalid value for variable 'todo'. Must be True or False.")

    def flag_assignments_made_and_place_roster_link(self, school_name, link):
        """Flags that assignments have been made for a school in the sheet to-do list."""
        # Find column letters for both headers
        school_row = SheetsAPI.find_row_by_string(self.todolist_sheet_id, todolist_sheetname, "A", school_name)
        assignments_col = self.__get_header_column(assignments_made)
        roster_link_col = self.__get_header_column(roster_link)
        roster_sent_col = self.__get_header_column(roster_sent)

        # Construct A1 notation cell references using school_row
        assignments_cell = f"{assignments_col}{school_row}"
        roster_link_cell = f"{roster_link_col}{school_row}"

        # Map cell addresses to their new values (True checks the checkbox in Sheets)
        cell_value_map = {assignments_cell: True,roster_link_cell: link}

        # Write both updates to the spreadsheet in a single API call
        SheetsAPI.write_values_to_sheet_from_dict(spreadsheet_id=self.todolist_sheet_id,cell_value_map=cell_value_map)
        self.__mark_or_unmark_to_do(school_row, assignments_col, todo=False)  # Unmark the to-do for assignments made
        self.__mark_or_unmark_to_do(school_row, roster_sent_col, todo=True) # Mark the to-do for roster sent
        return school_row

    def flag_roster_sent(self, school_row):
        """Flags that the roster has been sent for a school in the sheet to-do list."""
        # Find column letter for roster_sent header
        roster_sent_col = self.__get_header_column(roster_sent)

        self.__place_value_in_cell(school_row, roster_sent_col, True)
        self.__mark_or_unmark_to_do(school_row, roster_sent_col, todo=False) # Unmark the to-do for roster sent

    def place_invoice_link_in_todolist(self, school_name, invoice_number, link):
        """Places the invoice link in the to-do list for a specific school. Final Invoice is invoice_number 4."""
        school_row = SheetsAPI.find_row_by_string(self.todolist_sheet_id, todolist_sheetname, "A", school_name)
        # Find column letter for roster_link header, based on invoice number
        invoice_column = invoice_column_names[invoice_number - 1]  # Adjust for 0-based index
        invoice_link_col = self.__get_header_column(invoice_column)
        invoice_email_link_col = self.__get_header_column(invoice_email_col_name)

        self.__place_value_in_cell(school_row, invoice_link_col, link)
        self.__mark_or_unmark_to_do(school_row, invoice_email_link_col, todo=True)  # Mark the to-do for invoice email sending

    def place_countries_assigned_in_todolist(self, school_name, countries: set):
        """Places the countries assigned in the to-do list for a specific school."""
        school_row = SheetsAPI.find_row_by_string(self.todolist_sheet_id, todolist_sheetname, "A", school_name)
        # Find column letter for roster_link header
        country_col = self.__get_header_column(countries_assigned_col_name)

        # Convert set of countries to a comma-separated string
        countries_str = ", ".join(sorted(countries))

        self.__place_value_in_cell(school_row, country_col, countries_str)