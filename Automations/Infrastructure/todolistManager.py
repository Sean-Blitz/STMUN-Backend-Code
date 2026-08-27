
import os

from Infrastructure.GoogleAPIs.DriveAPIManager import DriveAPI
from Infrastructure.GoogleAPIs.SheetsAPIManager import SheetAPI
from dotenv import load_dotenv; load_dotenv()

class todolist():
    def __init__(self):
        self.drive = DriveAPI()
        self.sheet = SheetAPI()
        self.todolist_sheet_id = os.getenv("todolist_sheet_id")

    def flag_assignments_made(self, schoolname, link):
        pass

    def flag_roster_made_with_link(self, schoolname, link):
        pass

    def flag_roster_sent(self, schoolname, link):
        pass

    def flag_invoice_made_with_link(self, schoolname, link):
        pass

    def place_invoice_email_link_in_todolist(self, schoolname, link):
        pass