import os
import sys
import time
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

from ..Infrastructure import DriveAPI
from ..Infrastructure import SlideAPI
from ..Infrastructure import SheetAPI

BadgesPaper = SlideAPI()
CloudStorage = DriveAPI()
Spreadsheet = SheetAPI()

#------------- Controls ---------------
fileID = "1HRvv77Ud9K1GsmNzs8-g1OtB7A2112qOkKbO_RHWmoo"
sheetName = "Badges Automation"
#--------------------------------------
schoolNames = Spreadsheet.read_headers_until_blank(fileID, sheetName)
columnscount = len(schoolNames)
while "Committee" in schoolNames:
    schoolNames.remove("Committee")

schoolCount = len(schoolNames)

dictionaryofbadges = Spreadsheet.read_columns_until_blank(fileID, sheetName, columnscount)

committeeAssignments = []
countryAssignments = []
for i in range(len(dictionaryofbadges)):
    if (i+1) %2 != 0:
        countryAssignments.append(dictionaryofbadges.get(i+1, None))
        if countryAssignments[-1] is None:
            print(f"Warning: No country assignments found for column {i+1}.")
    elif (i+1) %2 == 0:
        committeeAssignments.append(dictionaryofbadges.get(i+1, None))
        if committeeAssignments[-1] is None:
            print(f"Warning: No committee assignments found for column {i+1}.")
    else:
        print("Error: column index out of expected range.")

copied_slide_id = CloudStorage.copy_drive_file("1HRvv77Ud9K1GsmNzs8-g1OtB7A2112qOkKbO_RHWmoo", new_name="SCVMUN 2027 Badges")

firstslideID = BadgesPaper.get_first_slide_id(copied_slide_id)
backsideID = BadgesPaper.get_slide_id_by_index(copied_slide_id,1)
pagesCreated = 0
badgesDone = 0  # total badges across all schools
current_slideID = None  # will point to the slide being filled

badgesDone = 0  # total badges across all schools
current_slideID = None  # will point to the slide being filled

for i in range(schoolCount):
    if i > 0:
        print("Sleeping for 10 seconds to avoid hitting API rate limits...")
        time.sleep(10)

    schoolCountryAssignments = countryAssignments[i]
    schoolCommitteeAssignments = committeeAssignments[i]

    if len(schoolCountryAssignments) != len(schoolCommitteeAssignments):
        print(f"Error: Mismatched number of country and committee assignments for {schoolNames[i]}.")
        sys.exit(1)

    schoolname = schoolNames[i]
    print(f"Processing school {i+1}/{schoolCount}: {schoolname}")

    badge_global_index = 0
    total_badges = len(schoolCountryAssignments)

    beginplaced = False  # to track if "Begin_X" has been placed for the current school
    while badge_global_index < total_badges:
        placeholders = {}

        # If no current slide yet or current slide is full, duplicate a new slide from template
        if current_slideID is None or (badgesDone % 8) == 0:
            new_slide = BadgesPaper.duplicate_slide(
                copied_slide_id,
                firstslideID  # always duplicate the pristine template
            )
            current_slideID = new_slide

            if not beginplaced: 
                if total_badges == 1:
                    begin_text = f"Single - {schoolname}"
                else:
                    begin_text = f"{total_badges} placards for {schoolname}"
            # Place "Begin_X" marker at the next available placeholder on the new slide
                BadgesPaper.replace_placeholders_on_slide(
                    copied_slide_id,
                    current_slideID if (badgesDone % 8) != 0 else new_slide,
                    {f"{{Begin_{(badgesDone % 8) + 1}}}": begin_text})
                beginplaced = True

        # Determine next empty slot on current slide
        start_placeholder_index = (badgesDone % 8) + 1

        # Fill as many badges as possible (up to placeholder 8)
        for p in range(start_placeholder_index, 9):
            if badge_global_index >= total_badges:
                break

            placeholders[f"{{Country_{p}}}"] = schoolCountryAssignments[badge_global_index]
            placeholders[f"{{Committee_{p}}}"] = schoolCommitteeAssignments[badge_global_index]
            badge_global_index += 1
            badgesDone += 1

        BadgesPaper.replace_placeholders_on_slide(
            copied_slide_id,
            current_slideID,
            placeholders
        )

    # Place "End_X" marker on the last badge of this school
    BadgesPaper.replace_placeholders_on_slide(
        copied_slide_id,
        current_slideID,
        {f"{{Begin_{(badgesDone - 1) % 8 + 1}}}": f"{schoolname} ends."}
    )


print("Reorganizing...")
time.sleep(5) #to avoid hitting API rate limits. Adjust as needed.
BadgesPaper.delete_slide(copied_slide_id, firstslideID)
BadgesPaper.move_slides_to_indexes(copied_slide_id, [backsideID], [0]) #move backside to very front before reversing, so that it ends up at the very end after reversing
BadgesPaper.reverse_all_slides(copied_slide_id)
BadgesPaper.replace_placeholders(copied_slide_id, {r"{Begin_1}": "", r"{Begin_2}": "", r"{Begin_3}": "", r"{Begin_4}": "", r"{Begin_5}": "", r"{Begin_6}": "", r"{Begin_7}": "", r"{Begin_8}": ""})
placementlist = []
numofslides = BadgesPaper.get_slide_count(copied_slide_id)

numofslidescreated, createdslideIDs = BadgesPaper.create_slide_copies(copied_slide_id, backsideID, numofslides-1)

BadgesPaper.delete_slide(copied_slide_id, backsideID)

currentSlideCount = BadgesPaper.get_slide_count(copied_slide_id)

front_count = len(createdslideIDs)

placementlist = [i for i in range(1, front_count * 2, 2)]

BadgesPaper.move_slides_to_indexes(
    copied_slide_id,
    createdslideIDs,
    placementlist
)
print(f"Inserting back slides at positions: {placementlist}")

print("Done! Here is the URL to the new slide deck: " + f"https://docs.google.com/presentation/d/{copied_slide_id}/edit")
print(f"A total of {badgesDone} badges were added across {schoolCount} schools.")

"""
how we are going to accomplish this:
Read the odd columns until blank. Storing in a list. These are country names.
Read the even columns until blank. Storing in a list. These are committee names.
When copying over to placards, iterate through the odd columns first to replace country placeholders, 
then iterate through the even columns to replace committee placeholders.

Finally, insert the backside from highest index to lowest, to avoid index shifting issues.

Use mod by 8 to find position to place "start" and "stop".

Then reverse all slides so that the order will be right. This is because we copy the top slide and copied slides happen after the original.
Get the number of slides. Since we know that there will always be one back slide, we can use that information to figure
out where to insert all the rest of the back slides.

"""    
