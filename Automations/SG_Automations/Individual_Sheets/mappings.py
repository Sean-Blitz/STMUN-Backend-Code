import os
import time
from dotenv import load_dotenv; load_dotenv()
AttendanceSheetID = os.getenv("AttendanceSheetID")
from SG_Automations.Individual_Sheets.IndividualSheets import SheetsAPI
def write_data_to_individual_sheet(i, )
    "MasterSheetColumn_to_IndividualSheetCell": 
    
        "Master Roster Contact Info!I": "Individualized Dashboard!G3",
        "Master Roster "
    
def pull_data_from_master_sheet(start_row):
    # here are the ones where we pull an entire list from the master sheet.
    emails = SheetsAPI.get_column_data(AttendanceSheetID, "Master Roster Contact Info", "E", start_row)
    tokens = SheetsAPI.get_column_data(AttendanceSheetID, "Master Roster Contact Info", "I", start_row); time.sleep(1)
    first_names = SheetsAPI.get_column_data(AttendanceSheetID, "Master Roster Contact Info", "B", start_row)
    last_names = SheetsAPI.get_column_data(AttendanceSheetID, "Master Roster Contact Info", "A", start_row); time.sleep(1)
    names = [f"{first} {last}" for first, last in zip(first_names, last_names)]
    grades = SheetsAPI.get_column_data(AttendanceSheetID, "Master Roster Contact Info", "C", start_row)
    student_IDs = SheetsAPI.get_column_data(AttendanceSheetID, "Master Roster Contact Info", "D", start_row); time.sleep(1)

    total_points = SheetsAPI.get_column_data(AttendanceSheetID, "Overall Total Points", "E", start_row)

    carry_over = SheetsAPI.get_column_data(AttendanceSheetID, "Fundraising/Deposits", "E", start_row)
    vertical_raise = SheetsAPI.get_column_data(AttendanceSheetID, "Fundraising/Deposits", "F", start_row); time.sleep(1)
    sees_candy = SheetsAPI.get_column_data(AttendanceSheetID, "Fundraising/Deposits", "G", start_row)
    first_aid = SheetsAPI.get_column_data(AttendanceSheetID, "Fundraising/Deposits", "H", start_row); time.sleep(1)
    emergency_kits = SheetsAPI.get_column_data(AttendanceSheetID, "Fundraising/Deposits", "I", start_row)
    fundraising_balance = SheetsAPI.get_column_data(AttendanceSheetID, "Fundraising/Deposits", "J", start_row); time.sleep(1)
    fundraising_used = SheetsAPI.get_column_data(AttendanceSheetID, "Fundraising/Deposits", "K", start_row)

    gmunc_payment1 = SheetsAPI.get_column_data(AttendanceSheetID, "Fundraising/Deposits", "O", start_row)
    gmunc_payment2 = SheetsAPI.get_column_data(AttendanceSheetID, "Fundraising/Deposits", "P", start_row); time.sleep(1)
    
    cells_list = 
    SheetsAPI.read_cells(cells_list)