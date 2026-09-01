import os

from Infrastructure import SheetAPI
from Infrastructure import DisplayClass
from Infrastructure import DriveAPI
from Infrastructure import DocAPI
from dotenv import load_dotenv; load_dotenv()

SheetsAPI = SheetAPI()
Display = DisplayClass()
Drive = DriveAPI()
Docs = DocAPI()

# ------------- Controls -----------------------
AttendingFolderID = os.getenv("AttendingFolderID")
model_roster_sheet_ID = os.getenv("model_roster_sheet_ID")
email_folder_ID = os.getenv("RosterEmailsFolderID")
email_template_ID = os.getenv("EmailTemplateID")
YearName = os.getenv("YearName") 

def generate_roster_and_add_assignments_to_it(finalassignments: dict[str, list], schoolname: str):
    """
    Takes finalassignments, a dictionary with the delegate number and name as the string, and a list with the committee, committeetype, and country in the dictionary, and puts it in a roster.

    First move the roster into the school's folder, rename it, and then add the assignments to the roster.
    """
    school_folder_ID = Drive.find_subfolder_id(AttendingFolderID, schoolname)
    if school_folder_ID is None:
        raise RuntimeError(f"Could not find folder for school '{schoolname}'.")

    this_year_folder_ID = Drive.find_subfolder_id(school_folder_ID, YearName)
    if this_year_folder_ID is None:
        raise RuntimeError(f"Could not find folder for year '{YearName}' in school '{schoolname}'.")

    # Copy the model roster into the school's folder
    new_roster_ID = Drive.copy_drive_file(model_roster_sheet_ID, this_year_folder_ID, f"{schoolname} Roster")
    if new_roster_ID is None:
        raise RuntimeError(f"Could not copy roster for school '{schoolname}'.")

    # Add the assignments to the new roster
    cell_map_of_committee = {}
    i = 0
    for school_name_and_number, [committee, committeetype, country] in finalassignments.items():
        cell_map_of_committee[f"D{i+21}"] = f"{country} ({committee})"
        i += 1
    SheetsAPI.write_values_to_sheet_from_dict(new_roster_ID, cell_map_of_committee)
    SheetsAPI.write_values_to_sheet_from_dict(new_roster_ID, {"B16": schoolname})

    return new_roster_ID, this_year_folder_ID

def add_delegates_to_existing_school_roster(schoolname: str, new_delegates: dict[str, list]):
    """
    Finds the roster ID for this school, reads down the roster the find the next row, and add the new delegates to the roster.
    """
    school_folder_ID = Drive.find_subfolder_id(AttendingFolderID, schoolname)
    if school_folder_ID is None:
        raise RuntimeError(f"Could not find folder for school '{schoolname}'.")

    this_year_folder_ID = Drive.find_subfolder_id(school_folder_ID, YearName)
    if this_year_folder_ID is None:
        raise RuntimeError(f"Could not find folder for year '{YearName}' in school '{schoolname}'.")

    school_roster_ID = Drive.find_sheet_id_by_name_contains(this_year_folder_ID, f"{schoolname} Roster")
    if school_roster_ID is None:
        raise RuntimeError(f"Could not find roster for school '{schoolname}'.")

    # Read the roster to find the next available row
    row = SheetsAPI.get_column_until_empty(school_roster_ID, "Sheet1", "C", 21) + 21  # Start reading from row 21
    doublecheckrow = SheetsAPI.get_column_until_empty(school_roster_ID, "Sheet1", "D", 21) + 21

    if row != doublecheckrow:
        raise RuntimeError(f"Row mismatch when adding delegates to roster for school '{schoolname}'. Check the roster for errors.")

    # Add the new delegates to the roster
    cell_map_of_school_name_and_number = {}
    cell_map_of_committee = {}
    cell_map_of_country = {}
    i = row
    for school_name_and_number, [committee, committeetype, country] in new_delegates.items():
        cell_map_of_committee[f"D{i+21}"] = f"{country} ({committee})"
        i += 1
    SheetsAPI.write_values_to_sheet_from_dict(school_roster_ID, cell_map_of_committee)

    return school_roster_ID

def find_existing_school_roster_ID(schoolname: str):
    """
    Finds the roster ID for this school
    """
    school_folder_ID = Drive.find_subfolder_id(AttendingFolderID, schoolname)
    if school_folder_ID is None:
        raise RuntimeError(f"Could not find folder for school '{schoolname}'.")

    this_year_folder_ID = Drive.find_subfolder_id(school_folder_ID, YearName)
    if this_year_folder_ID is None:
        raise RuntimeError(f"Could not find folder for year '{YearName}' in school '{schoolname}'.")

    school_roster_ID = Drive.find_sheet_id_by_name_contains(this_year_folder_ID, f"{schoolname} Roster")
    if school_roster_ID is None:
        raise RuntimeError(f"Could not find roster for school '{schoolname}'.")

    return school_roster_ID

def draft_email_for_school_and_share_roster(schoolname: str, advisorEmail, HeadDelegateEmail, roster_ID: str, this_year_folder_ID: str):
    """
    Drafts an email in Google Docs by replacing placeholders. Adds a new Google Docs file.
    """
    if email_template_ID is None:
        raise RuntimeError("Email template ID not found in environment variables.")

    new_email_doc_ID = Drive.copy_drive_file(email_template_ID, email_folder_ID, f"{schoolname} Email Draft")
    if new_email_doc_ID is None:
        raise RuntimeError(f"Could not copy email draft for school '{schoolname}'.")

    # Replace placeholders in the new email document
    replacements = {
        "{{SCHOOL_NAME}}": schoolname,
        "{{ADVISOR_EMAIL}}": advisorEmail,
        "{{HEAD_DELEGATE_EMAIL}}": HeadDelegateEmail,
        "{{ROSTER_LINK}}": f"https://docs.google.com/spreadsheets/d/{roster_ID}",
        "{{FOLDER_LINK}}": f"https://drive.google.com/drive/folders/{this_year_folder_ID}"
    }
    Docs.fill_doc_placeholders_from_dictionary(new_email_doc_ID, replacements)

    Drive.share_spreadsheet(roster_ID, advisorEmail, role="writer")
    Drive.share_spreadsheet(roster_ID, HeadDelegateEmail, role="writer")

    return new_email_doc_ID