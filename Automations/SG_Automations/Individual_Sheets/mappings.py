import os
import time
import sys
from dotenv import load_dotenv; load_dotenv()
AttendanceSheetID = os.getenv("AttendanceSheetID")
if AttendanceSheetID is None:
    raise ValueError("AttendanceSheetID is not set in the environment variables. Please ensure it is defined in the .env file.")
from SG_Automations.Individual_Sheets.IndividualSheets import SheetsAPI

def write_data_to_individual_sheet(i, ):
    pass


def pull_data_from_master_sheet(start_row):
    def read(sheet_name, column_letter, begin = start_row):
        return SheetsAPI.get_column_data(AttendanceSheetID, sheet_name, column_letter, begin)
    
    # here are the ones where we pull an entire list from the master sheet.
    emails = read("Master Roster Contact Info", "E"); time.sleep(1)
    tokens = read("Master Roster Contact Info", "I"); time.sleep(1)
    first_names = read("Master Roster Contact Info", "B"); time.sleep(1)
    last_names = read("Master Roster Contact Info", "A"); time.sleep(1)
    grades = read("Master Roster Contact Info", "C")
    student_IDs = read("Master Roster Contact Info", "D"); time.sleep(1)

    total_points = read("Overall Total Points", "E")

    carry_over = read("Fundraising/Deposits", "E")
    vertical_raise = read("Fundraising/Deposits", "F"); time.sleep(1)
    sees_candy = read("Fundraising/Deposits", "G")
    first_aid = read("Fundraising/Deposits", "H"); time.sleep(1)
    emergency_kits = read("Fundraising/Deposits", "I")
    fundraising_balance = read("Fundraising/Deposits", "J"); time.sleep(1)
    fundraising_used = read("Fundraising/Deposits", "K")

    gmunc_payment1 = read("Fundraising/Deposits", "O")
    gmunc_payment2 = read("Fundraising/Deposits", "P"); time.sleep(1)
    gmunc_applied = read("Fundraising/Deposits", "Q")
    smunc_payment1 = read("Fundraising/Deposits", "S")
    smunc_payment2 = read("Fundraising/Deposits", "T"); time.sleep(1)
    smunc_applied = read("Fundraising/Deposits", "U")
    pacmun_payment1 = read("Fundraising/Deposits", "W")
    pacmun_payment2 = read("Fundraising/Deposits", "X"); time.sleep(1)
    pacmun_applied = read("Fundraising/Deposits", "Y")
    scvmun_payment = read("Fundraising/Deposits", "AA")
    scvmun_applied = read("Fundraising/Deposits", "AB"); time.sleep(1)
    nhsmun_payment1 = read("Fundraising/Deposits", "AC")
    nhsmun_payment2 = read("Fundraising/Deposits", "AD"); time.sleep(1)
    nhsmun_applied = read("Fundraising/Deposits", "AE"); time.sleep(1)
    international_payment1 = read("Fundraising/Deposits", "AG")
    international_payment2 = read("Fundraising/Deposits", "AH")
    international_applied = read("Fundraising/Deposits", "AI"); time.sleep(1)
    bmun_payment1 = read("Fundraising/Deposits", "AK")
    bmun_payment2 = read("Fundraising/Deposits", "AL")
    bmun_applied = read("Fundraising/Deposits", "AM"); time.sleep(1)
    dmunc_payment1 = read("Fundraising/Deposits", "AO")
    dmunc_payment2 = read("Fundraising/Deposits", "AP"); time.sleep(1)
    dmunc_applied = read("Fundraising/Deposits", "AQ")

    cells_list = ["Fundraising/Deposits!AT6", "Fundraising/Deposits!AT7", "Fundraising/Deposits!AT8", "Fundraising/Deposits!AT9", "Fundraising/Deposits!AT10", "Fundraising/Deposits!AT11", "Fundraising/Deposits!AT12", "Fundraising/Deposits!AT13"] 
    SheetsAPI.read_cells(AttendanceSheetID, cells_list)

    names = [f"{first} {last}" for first, last in zip(first_names, last_names)]