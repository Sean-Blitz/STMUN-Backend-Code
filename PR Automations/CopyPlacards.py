import os
import time
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
import string
from typing import List, Union, Dict
import driveFunctions
import SlidesFunctions
import sheetFunctions
import AuthenticationFunctions

drive_service, sheets_service, slides_service, docs_service, gmail_service = AuthenticationFunctions.authenticate()

committeenames = sheetFunctions.read_headers_until_blank("1LgQxP67-pe6JW0lixWacp3ou5UV1f2vmSGVI8j5IPIs", "Placards Automation", sheets_service)
committeescount = len(committeenames)

dictionaryofplacards = sheetFunctions.read_columns_until_blank("1LgQxP67-pe6JW0lixWacp3ou5UV1f2vmSGVI8j5IPIs", "Placards Automation", committeescount, sheets_service)


newslidesURL = []
for i in range(len(dictionaryofplacards)): # Iterate through each committee. You are on file level here.
    if i > 0:
        time.sleep(2) #to avoid hitting API rate limits. Adjust as needed.
    
    committeename = committeenames[i]
    
    # Copy the template slide and rename it
    copied_slide_id = driveFunctions.copy_drive_file(
        drive_service,
        '191sgGYyUZ8NKz9e92JHeLLR_ilo9KJTuH2nQColZDAY',  
        new_name=committeename
    )

    firstslideID = SlidesFunctions.get_first_slide_id(
        slides_service,
        copied_slide_id
    )

    if len(dictionaryofplacards[i+1]) % 2 != 0:
        pagelength = (len(dictionaryofplacards[i+1]) // 2) + 1
    else:
        pagelength = len(dictionaryofplacards[i+1]) // 2
    
    pageIDs = [firstslideID]
    print(f"Creating {pagelength-1} pages...")
    for j in range(pagelength-1): #you are on page level now. Copying pages here. Minus one because there is already a page.
        pageIDs.append(SlidesFunctions.duplicate_slide(
            slides_service,
            copied_slide_id,
            firstslideID 
        ))

    print("Adding new placeholders...")
    for c, page_id in enumerate(pageIDs):
        newnumber = c*2 + 1
        SlidesFunctions.replace_two_placeholders_on_slide(
            slides_service,
            copied_slide_id,
            page_id,  # important: use each slide's ID
            "{COUNTRY_1}",
            f"{{COUNTRY_{newnumber}}}",
            "{COUNTRY_2}",
            f"{{COUNTRY_{newnumber + 1}}}"
        )
    
    print("Building value map...")
    value_map = {} #building a dictionary to map new placeholder names to actual names from placardnames.
    placardnames = dictionaryofplacards[i+1]
    for idx, name in enumerate(placardnames):
        placeholder_number = idx + 1
        value_map[f"{{COUNTRY_{placeholder_number}}}"] = name

    print("Applying names...")
    SlidesFunctions.replace_placeholders(
        slides_service,
        copied_slide_id,
        value_map= value_map
    )

    print("Done with " + committeename)
    newslidesURL.append("https://docs.google.com/presentation/d/" + copied_slide_id)

print("\nAll done! Here are the URLs to the new slides:")
for url in newslidesURL:
    print(url)