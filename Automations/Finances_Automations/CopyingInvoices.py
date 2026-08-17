import os
import datetime
import sys
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
from Automations.Infrastructure import DriveAPI
from Automations.Infrastructure import SheetAPI

CloudStorageAPI = DriveAPI()
Sheets = SheetAPI()

#--------------------- Controls ------------------------
ParentFolderID = "1BPlHoP2G4ih7ewIRQsU0vV9ILkOSxsCv"
YearText = "SCVMUN LVI (2027)"
#-------------------------------------------------------

def inputcheck(input, valid):
    while input not in valid:
        input = input("Invalid input. " + "Continue? y/n")
    return input

Final = input("Is this the final invoice? y/n")
if Final != "y":
    From = int(input("Invoice number that you are copying from?"))
    To = int(input("Invoice number that you are copying to?"))
    if From == To or To > 3 or From > 2:
        print ("Input error.")
        sys.exit()

FolderIDs = CloudStorageAPI.get_subfolders_as_dict(ParentFolderID)
names = list(FolderIDs.keys())
toeditsheets = {}
paidschoolsheets = {}
yearfolderids = []
stop = 0
for i in range(len(names)):
    yearfolder = CloudStorageAPI.find_subfolder_id(FolderIDs[names[i]], YearText)
    if yearfolder is None:
        print(f"Could not find year folder for {names[i]}.")
        stop = 1
        continue
    else:
        yearfolderids.append(yearfolder)

if stop >= 1:
    print("Process cancelled due to missing year folders.")
    sys.exit()

if Final != "y":
    for i in range(len(FolderIDs)):
        yearfolder = yearfolderids[i]
        inputcheck(input(f"Processing {names[i]}... Continue? y/n"), ["y", "n"])
        fromsheetID = CloudStorageAPI.find_sheet_id_by_name_contains(yearfolder, f"Invoice {From}") #type: ignore
        if fromsheetID is None:
            print("Could not find source sheet.")
            continue

        payments = Sheets.read_single_unformatted_cell(fromsheetID, "Purchase order!H33")
        balance = Sheets.read_single_unformatted_cell(fromsheetID, "Purchase order!H36")
        if not balance is None and not payments is None:
            balance = int(balance)
            payments = int(payments)

        if Final != "y": #not final invoice, regular copying.
            From = int(input("Invoice number that you are copying from?"))
            To = int(input("Invoice number that you are copying to?"))
            
            if From == To or To > 3 or From > 2: #error checking.
                print ("Input error.")
                sys.exit()
            
            tosheetID = CloudStorageAPI.copy_drive_file(fromsheetID, yearfolder, f"Invoice {To} - {names[i]}")
            if payments == 0: #unpaid.
                if From == 1 and To == 2:
                    earlydelegates = int(Sheets.read_single_cell(fromsheetID, "Purchase order!B28")) #type: ignore
                    Sheets.write_values_to_sheet_from_dict(
                        tosheetID,
                        {
                            "Purchase order!C22": datetime.datetime.now().strftime("%m/%d/%Y"),
                            "Purchase order!B29": earlydelegates,
                            "Purchase order!B28": "0",
                            "Purchase order!A10": f"Invoice {To}",
                        }
                    )
                elif From == 2 and To == 3:
                    earlydelegates = int(Sheets.read_single_cell(fromsheetID, "Purchase order!B28")) #type: ignore
                    regulardelegates = int(Sheets.read_single_cell(fromsheetID, "Purchase order!B29")) #type: ignore
                    Sheets.write_values_to_sheet_from_dict(
                        tosheetID,
                        {
                            "Purchase order!C22": datetime.datetime.now().strftime("%m/%d/%Y"),
                            "Purchase order!B30": regulardelegates + earlydelegates,
                            "Purchase order!B28": "0",
                            "Purchase order!B29": "0",
                            "Purchase order!A10": f"Invoice {To}",
                        }
                    )
            elif payments != 0 and balance != 0: #partially paid.
                toeditsheets[names[i]] = tosheetID
                Sheets.write_values_to_sheet_from_dict(
                    tosheetID,
                    {
                        "Purchase order!C22": datetime.datetime.now().strftime("%m/%d/%Y"),
                        "Purchase order!A10": f"Invoice {To}",
                    })
            elif payments != 0 and balance == 0: #fully paid
                paidschoolsheets[names[i]] = tosheetID
                Sheets.write_values_to_sheet_from_dict(
                    tosheetID,
                    {
                        "Purchase order!C22": datetime.datetime.now().strftime("%m/%d/%Y"),
                        "Purchase order!A10": f"Invoice {To}",
                    })
            print("Here is the new invoice: https://docs.google.com/spreadsheets/d/" + tosheetID )


    forfunctionlist = list(toeditsheets.keys())
    print("You should manually edit these sheets:")
    for n in range (len(toeditsheets)):
        print(forfunctionlist[n] + " - " + "https://docs.google.com/spreadsheets/d/" + str(toeditsheets[forfunctionlist[n]]))

    print() #for readability
    forfunctionlist2 = list(paidschoolsheets.keys())
    print("These schools have paid in full:")

    for i in range(len(paidschoolsheets)):
        print(forfunctionlist2[i] + " - " + str(paidschoolsheets[forfunctionlist2[i]]))

elif Final == "y":
    for i in range(len(FolderIDs)):
        yearfolder = yearfolderids[i]
        if names[i] == "Santa Teresa High School":
            continue
        print(f"Processing final invoice for {names[i]}...")
        fromsheetID = CloudStorageAPI.find_sheet_id_by_name_contains(yearfolder, "Invoice 3")
        if fromsheetID is None:
            print("Could not find source sheet.")
            continue

        payments = int(Sheets.read_single_unformatted_cell(fromsheetID, "Purchase order!H33")) #type: ignore
        balance = int(Sheets.read_single_unformatted_cell(fromsheetID, "Purchase order!H36")) #type: ignore

        if payments != 0 and balance == 0:
            tosheetID = CloudStorageAPI.copy_drive_file(fromsheetID, "1lpF-H-EhDMQWBOK6xgqlhYE00E0wWiUt", f"Final Invoice - {names[i]}")
            Sheets.write_values_to_sheet_from_dict(
                tosheetID,
                {
                    "Purchase order!A10": "FINAL INVOICE",
                })
            print("Paid" )
        elif payments != 0 and balance != 0:
            tosheetID = CloudStorageAPI.copy_drive_file(fromsheetID, "1TUMtb3k4lv6ahFIxxDAeAYZReiT0RCJj", f"Final Invoice - {names[i]}")
            Sheets.write_values_to_sheet_from_dict(
                tosheetID,
                {
                    "Purchase order!A10": "FINAL INVOICE",
                })
            print("Partially Paid")
        elif payments == 0 and balance >= 0:
            tosheetID = CloudStorageAPI.copy_drive_file(fromsheetID, "11u9S7UrT6HEAqsMAyh0yZVhb0BvSLxMa", f"Final Invoice - {names[i]}")
            Sheets.write_values_to_sheet_from_dict(
                tosheetID,
                {
                    "Purchase order!A10": "FINAL INVOICE",
                })
            print(f"Unpaid")
        