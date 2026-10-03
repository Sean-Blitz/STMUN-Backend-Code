"""
Note: this script WILL take a long time to run just to set up, as it is pulling a significant amount of data at the start.
"""
import sys
from pathlib import Path

# Locate the root 'Automations' directory relative to this script file
# parent.parent points to Automations folder.
AUTOMATIONS_DIR = Path(__file__).resolve().parent.parent

# Inject the path into sys.path if it isn't already present
if str(AUTOMATIONS_DIR) not in sys.path:
    sys.path.insert(0, str(AUTOMATIONS_DIR))

import os
import time
from dotenv import load_dotenv; load_dotenv()
from Infrastructure import SheetAPI
from Infrastructure import DriveAPI
from Infrastructure import DisplayClass; Display = DisplayClass()

SheetsAPI = SheetAPI()
Drive = DriveAPI()
AttendanceSheetID = os.environ["AttendanceSheetID"]
drive_folder_ID = os.environ["drive_folder_ID"]
template_file_id = os.environ["individualized_dashboard_template_file_id"]
thursday_meeting_column_indicator = "Thu"
wednesday_meeting_column_indicator = "Wed"

class IndividualSheetData:
    def __init__(self):
        self.gmunc_cost = os.environ["GMUNCcost"]
        self.smunc_cost = os.environ["SMUNCcost"]
        self.pacmun_cost = os.environ["PACMUNcost"]
        self.scvmun_cost = os.environ["SCVMUNcost"]
        self.nhsmun_cost = os.environ["NHSMUNcost"]
        self.international_cost = os.environ["Internationalcost"]
        self.bmunc_cost = os.environ["BMUNcost"]
        self.dmunc_cost = os.environ["DMUNCcost"]
        self.thursday_meetings_column_in_individual_sheet = "J"
        self.wednesday_meetings_column_in_individual_sheet = "M"
        self.wednesday_meetings_date_column_in_individual_sheet = "L"
        self.thursday_meetings_date_column_in_individual_sheet = "I"

    def write_data_to_individual_sheet(self, attendance_sheet_index, sheet_id):
        data_dict = {
            "B3": self.names[attendance_sheet_index],
            "B4": self.emails[attendance_sheet_index],
            "E3": self.student_IDs[attendance_sheet_index],
            "E4": self.grades[attendance_sheet_index],
            "A9": self.carry_over[attendance_sheet_index],
            "B9": self.vertical_raise[attendance_sheet_index] if self.vertical_raise else "",
            "C9": self.sees_candy[attendance_sheet_index] if self.sees_candy else "",
            "D9": self.first_aid[attendance_sheet_index] if self.first_aid else "",
            "E9": self.emergency_kits[attendance_sheet_index] if self.emergency_kits else "",
            "F9": self.fundraising_balance[attendance_sheet_index] if self.fundraising_balance else "",
            "G9": self.fundraising_used[attendance_sheet_index] if self.fundraising_used else "",
            "B13": self.gmunc_payment1[attendance_sheet_index] if self.gmunc_payment1 else "",
            "C13": self.gmunc_payment2[attendance_sheet_index] if self.gmunc_payment2 else "",
            "D13": self.gmunc_applied[attendance_sheet_index] if self.gmunc_applied else "",
            "E13": self.gmunc_cost,
            "B14": self.smunc_payment1[attendance_sheet_index] if self.smunc_payment1 else "",
            "C14": self.smunc_payment2[attendance_sheet_index] if self.smunc_payment2 else "",
            "D14": self.smunc_applied[attendance_sheet_index] if self.smunc_applied else "",
            "E14": self.smunc_cost,
            "B15": self.pacmun_payment1[attendance_sheet_index] if self.pacmun_payment1 else "",
            "C15": self.pacmun_payment2[attendance_sheet_index] if self.pacmun_payment2 else "",
            "D15": self.pacmun_applied[attendance_sheet_index] if self.pacmun_applied else "",
            "E15": self.pacmun_cost,
            "B16": self.scvmun_payment[attendance_sheet_index] if self.scvmun_payment else "",
            "C16": self.scvmun_applied[attendance_sheet_index] if self.scvmun_applied else "",
            "E16": self.scvmun_cost,
            "B17": self.nhsmun_payment1[attendance_sheet_index] if self.nhsmun_payment1 else "",
            "C17": self.nhsmun_payment2[attendance_sheet_index] if self.nhsmun_payment2 else "",
            "D17": self.nhsmun_applied[attendance_sheet_index] if self.nhsmun_applied else "",
            "E17": self.nhsmun_cost,
            "B18": self.international_payment1[attendance_sheet_index] if self.international_payment1 else "",
            "C18": self.international_payment2[attendance_sheet_index] if self.international_payment2 else "",
            "D18": self.international_applied[attendance_sheet_index] if self.international_applied else "",
            "E18": self.international_cost,
            "B19": self.bmun_payment1[attendance_sheet_index] if self.bmun_payment1 else "",
            "C19": self.bmun_payment2[attendance_sheet_index] if self.bmun_payment2 else "",
            "D19": self.bmun_applied[attendance_sheet_index] if self.bmun_applied else "",
            "E19": self.bmunc_cost,
            "B20": self.dmunc_payment1[attendance_sheet_index] if self.dmunc_payment1 else "",
            "C20": self.dmunc_payment2[attendance_sheet_index] if self.dmunc_payment2 else "",
            "D20": self.dmunc_applied[attendance_sheet_index] if self.dmunc_applied else "",
            "E20": self.dmunc_cost,
            "B24": self.gmunc_attendance[attendance_sheet_index] if self.gmunc_attendance else "",
            "C24": self.gmunc_award[attendance_sheet_index] if self.gmunc_award else "",
            "D24": self.gmunc_points[attendance_sheet_index] if self.gmunc_points else "",
            "B25": self.smunc_attendance[attendance_sheet_index] if self.smunc_attendance else "",
            "C25": self.smunc_award[attendance_sheet_index] if self.smunc_award else "",
            "D25": self.smunc_points[attendance_sheet_index] if self.smunc_points else "",
            "B26": self.pacmun_attendance[attendance_sheet_index] if self.pacmun_attendance else "",
            "C26": self.pacmun_award[attendance_sheet_index] if self.pacmun_award else "",
            "D26": self.pacmun_points[attendance_sheet_index] if self.pacmun_points else "",
            "B27": self.scvmun_attendance[attendance_sheet_index] if self.scvmun_attendance else "",
            "C27": self.scvmun_award[attendance_sheet_index] if self.scvmun_award else "",
            "D27": self.scvmun_points[attendance_sheet_index] if self.scvmun_points else "",
            "B28": self.nhsmun_attendance[attendance_sheet_index] if self.nhsmun_attendance else "",
            "C28": self.nhsmun_award[attendance_sheet_index] if self.nhsmun_award else "",
            "D28": self.nhsmun_points[attendance_sheet_index] if self.nhsmun_points else "",
            "B29": self.international_attendance[attendance_sheet_index] if self.international_attendance else "",
            "C29": self.international_award[attendance_sheet_index] if self.international_award else "",
            "D29": self.international_points[attendance_sheet_index] if self.international_points else "",
            "B30": self.bmun_attendance[attendance_sheet_index] if self.bmun_attendance else "",
            "C30": self.bmun_award[attendance_sheet_index] if self.bmun_award else "",
            "D30": self.bmun_points[attendance_sheet_index] if self.bmun_points else "",
            "B31": self.dmunc_attendance[attendance_sheet_index] if self.dmunc_attendance else "",
            "C31": self.dmunc_award[attendance_sheet_index] if self.dmunc_award else "",
            "D31": self.dmunc_points[attendance_sheet_index] if self.dmunc_points else "",
        }
        thursday_length = len(self.thursday_attendances[attendance_sheet_index])
        wednesday_length = len(self.training_attendances[attendance_sheet_index])

        for coord, value in data_dict.items():
            if value is None:
                data_dict[coord] = ""  # Replace None with an empty string
        for i in range(thursday_length):
            data_dict[f"{self.thursday_meetings_column_in_individual_sheet}{i+2}"] = self.thursday_attendances[attendance_sheet_index][i]
        for i in range(wednesday_length):
            data_dict[f"{self.wednesday_meetings_column_in_individual_sheet}{i+2}"] = self.training_attendances[attendance_sheet_index][i]
        for i in range(len(self.training_attendance_dates)):
            data_dict[f"{self.wednesday_meetings_date_column_in_individual_sheet}{i+2}"] = self.training_attendance_dates[i]
        for i in range(len(self.thursday_attendance_dates)):
            data_dict[f"{self.thursday_meetings_date_column_in_individual_sheet}{i+2}"] = self.thursday_attendance_dates[i]

        SheetsAPI.write_values_to_sheet_from_dict(sheet_id, data_dict)

    def read_sheet_setup(self, start_row):
        general_meeting_header_row = SheetsAPI.read_row_from(AttendanceSheetID, "Thursday Meeting Attd", start_row -1, "E"); time.sleep(2)
        general_meeting_count = len([cell for cell in general_meeting_header_row if cell == thursday_meeting_column_indicator])
        training_header_row = SheetsAPI.read_row_from(AttendanceSheetID, "Mock/Training Attd", start_row -1, "E"); time.sleep(2)
        training_count = len([cell for cell in training_header_row if cell == wednesday_meeting_column_indicator])
        general_end_column = SheetsAPI.sheets_alphabet(general_meeting_count + 4)
        training_end_column = SheetsAPI.sheets_alphabet(training_count + 4)
        return general_end_column, training_end_column, general_meeting_count, training_count

    def pull_data_from_master_sheet(self, start_row):
        number_of_names = len(SheetsAPI.get_column_data(AttendanceSheetID, "Master Roster Contact Info", "B", start_row))
        def read(sheet_name, column_letter, begin = start_row):
            list = SheetsAPI.get_column_data(AttendanceSheetID, sheet_name, column_letter, begin)
            if len(list) < number_of_names:
                Display.display(f"Note: The number of entries in column {column_letter} of sheet '{sheet_name}' is less than the number of names. Filling missing entries with empty strings.")
                list.extend([""] * (number_of_names - len(list)))
            elif len(list) > number_of_names:
                Display.display(f"Note: The number of entries in column {column_letter} of sheet '{sheet_name}' is greater than the number of names. Truncating extra entries.")
                list = list[:number_of_names]
            return list
        
        # here are the ones where we pull an entire list from the master sheet.
        self.emails = read("Master Roster Contact Info", "E"); time.sleep(1)
        self.tokens = read("Master Roster Contact Info", "I"); time.sleep(1)
        self.first_names = read("Master Roster Contact Info", "B"); time.sleep(1)
        self.last_names = read("Master Roster Contact Info", "A"); time.sleep(1)
        self.grades = read("Master Roster Contact Info", "C")
        self.student_IDs = read("Master Roster Contact Info", "D"); time.sleep(2)

        self.total_points = read("Overall Total Points", "E")

        self.carry_over = read("Fundraising/Deposits", "E")
        self.vertical_raise = read("Fundraising/Deposits", "F"); time.sleep(1)
        self.sees_candy = read("Fundraising/Deposits", "G")
        self.first_aid = read("Fundraising/Deposits", "H"); time.sleep(2)
        self.emergency_kits = read("Fundraising/Deposits", "I")
        self.fundraising_balance = read("Fundraising/Deposits", "J"); time.sleep(1)
        self.fundraising_used = read("Fundraising/Deposits", "K")

        self.gmunc_payment1 = read("Fundraising/Deposits", "O")
        self.gmunc_payment2 = read("Fundraising/Deposits", "P"); time.sleep(1)
        self.gmunc_applied = read("Fundraising/Deposits", "Q")
        self.smunc_payment1 = read("Fundraising/Deposits", "S")
        self.smunc_payment2 = read("Fundraising/Deposits", "T"); time.sleep(2)
        self.smunc_applied = read("Fundraising/Deposits", "U")
        self.pacmun_payment1 = read("Fundraising/Deposits", "W")
        self.pacmun_payment2 = read("Fundraising/Deposits", "X"); time.sleep(1)
        self.pacmun_applied = read("Fundraising/Deposits", "Y")
        self.scvmun_payment = read("Fundraising/Deposits", "AA")
        self.scvmun_applied = read("Fundraising/Deposits", "AB"); time.sleep(1)
        self.nhsmun_payment1 = read("Fundraising/Deposits", "AC")
        self.nhsmun_payment2 = read("Fundraising/Deposits", "AD"); time.sleep(2)
        self.nhsmun_applied = read("Fundraising/Deposits", "AE")
        self.international_payment1 = read("Fundraising/Deposits", "AG")
        self.international_payment2 = read("Fundraising/Deposits", "AH")
        self.international_applied = read("Fundraising/Deposits", "AI"); time.sleep(1)
        self.bmun_payment1 = read("Fundraising/Deposits", "AK")
        self.bmun_payment2 = read("Fundraising/Deposits", "AL")
        self.bmun_applied = read("Fundraising/Deposits", "AM"); time.sleep(1)
        self.dmunc_payment1 = read("Fundraising/Deposits", "AO")
        self.dmunc_payment2 = read("Fundraising/Deposits", "AP"); time.sleep(1)
        self.dmunc_applied = read("Fundraising/Deposits", "AQ")

        self.gmunc_attendance = read("Conference Attd/Award", "F"); time.sleep(1)
        self.gmunc_award = read("Conference Attd/Award", "G")
        self.gmunc_points = read("Conference Attd/Award", "H"); time.sleep(2)
        self.smunc_attendance = read("Conference Attd/Award", "I")
        self.smunc_award = read("Conference Attd/Award", "J"); time.sleep(1)
        self.smunc_points = read("Conference Attd/Award", "K")
        self.pacmun_attendance = read("Conference Attd/Award", "L")
        self.pacmun_award = read("Conference Attd/Award", "M") 
        self.pacmun_points = read("Conference Attd/Award", "N")
        self.scvmun_attendance = read("Conference Attd/Award", "Q"); time.sleep(2)
        self.scvmun_award = read("Conference Attd/Award", "R")
        self.scvmun_points = read("Conference Attd/Award", "S"); time.sleep(1)
        self.nhsmun_attendance = read("Conference Attd/Award", "W")
        self.nhsmun_award = read("Conference Attd/Award", "X"); time.sleep(1)
        self.nhsmun_points = read("Conference Attd/Award", "Y")
        self.international_attendance = read("Conference Attd/Award", "Z"); time.sleep(1)
        self.international_award = read("Conference Attd/Award", "AA")
        self.international_points = read("Conference Attd/Award", "AB"); time.sleep(2)
        self.bmun_attendance = read("Conference Attd/Award", "T")
        self.bmun_award = read("Conference Attd/Award", "U"); time.sleep(1)
        self.bmun_points = read("Conference Attd/Award", "V")
        self.dmunc_attendance = read("Conference Attd/Award", "AC"); time.sleep(1)
        self.dmunc_award = read("Conference Attd/Award", "AD")
        self.dmunc_points = read("Conference Attd/Award", "AE"); time.sleep(2)
        time.sleep(20)  # Sleep for 20 seconds to avoid hitting API rate limits

        general_end_column, training_end_column, general_meeting_count, training_count = self.read_sheet_setup(start_row)
        self.thursday_attendances = SheetsAPI.get_2d_range(AttendanceSheetID, "Thursday Meeting Attd", f"F{start_row}", f"{general_end_column}{len(self.first_names) + start_row-1}"); time.sleep(1)
        self.training_attendances = SheetsAPI.get_2d_range(AttendanceSheetID, "Mock/Training Attd", f"F{start_row}", f"{training_end_column}{len(self.first_names) + start_row-1}"); time.sleep(1)
        
        self.training_attendance_dates = SheetsAPI.read_row_from(AttendanceSheetID, "Mock/Training Attd", start_row-2, "F")[:training_count]; time.sleep(1)
        self.thursday_attendance_dates = SheetsAPI.read_row_from(AttendanceSheetID, "Thursday Meeting Attd", start_row-2, "F")[:general_meeting_count]; time.sleep(1)

        self.names = [f"{first} {last}" for first, last in zip(self.first_names, self.last_names)]

def main():
    data = IndividualSheetData()
    data.pull_data_from_master_sheet(start_row=5)
    for i, name in enumerate(data.names):
        individual_sheet_name = f"{name} - Individualized Dashboard"
        sheet_id = Drive.find_sheet_id_by_name_contains(drive_folder_ID, individual_sheet_name)
        if sheet_id is None:
            sheet_id = Drive.copy_drive_file(file_id=template_file_id, new_name=f"{name} - Individualized Dashboard", destination_folder_id=drive_folder_ID)
            Drive.share_spreadsheet(sheet_id, data.emails[data.names.index(name)], role="commenter")
            data.write_data_to_individual_sheet(data.names.index(name), sheet_id)
            Display.display(f"{i+1} - Created, populated, and shared sheet for {name}.")
        else:
            data.write_data_to_individual_sheet(data.names.index(name), sheet_id)
            Display.display(f"{i+1} - Populated existing sheet for {name}.")
        time.sleep(3)  # Sleep for 3 seconds to avoid hitting API rate limits

if __name__ == "__main__":
    main()