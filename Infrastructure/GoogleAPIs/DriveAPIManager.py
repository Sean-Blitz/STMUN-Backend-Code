from googleapiclient.discovery import build
import re
from .GoogleAPIsManager import GoogleAPIs

class DriveAPI(GoogleAPIs):
    def __init__(self):
        super().__init__(CREDENTIALS_FILE="credentials.json", TOKEN_FILE = "token.json", SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/documents'])
        creds = self.authenticate()
        self.service = build('drive', 'v3', credentials=creds)
    
    def create_drive_folder(self, name, mime_type, parent_id=None):
        """
        Creates a folder (or any Drive file type).

        Args:
            service: Authenticated Drive service
            name (str): Folder name
            mime_type (str): MIME type
            parent_id (str, optional): Parent folder ID

        Returns:
            str: Created file/folder ID
        """
        metadata = {
            'name': name,
            'mimeType': mime_type
        }

        if parent_id:
            metadata['parents'] = [parent_id]

        file = self.service.files().create(
            body=metadata,
            fields='id'
        ).execute()

        return file['id']

    def copy_drive_file(self, file_id, destination_folder_id = None, new_name=None):
        """
        Copies a file in Google Drive.

        Args:
            service: Authenticated Drive service
            file_id (str): ID of the file to copy
            destination_folder_id (str): Folder ID where the copy will go
            new_name (str, optional): New name for the copied file

        Returns:
            str: ID of the copied file
        """
        if destination_folder_id == None:
            metadata = {
            }
        else:
            metadata = {
                'parents': [destination_folder_id]
            }

        if new_name:
            metadata['name'] = new_name

        copied_file = self.service.files().copy(
            fileId=file_id,
            body=metadata,
            fields='id'
        ).execute()

        return copied_file['id']

    def find_subfolder_id(self, parent_folder_id, search_string):
        """
        Finds a single subfolder in a given parent folder whose name contains the search string.

        Args:
            service: Authenticated Google Drive service
            parent_folder_id (str): ID of the parent folder
            search_string (str): Substring to look for in the folder name

        Returns:
            str: ID of the first matching subfolder, or None if not found
        """
        query = (
            f"'{parent_folder_id}' in parents "
            f"and mimeType='application/vnd.google-apps.folder' "
            f"and trashed=false"
        )

        results = self.service.files().list(
            q=query,
            spaces='drive',
            fields="files(id, name)"
        ).execute()

        folders = results.get('files', [])

        for f in folders:
            if search_string.lower() in f['name'].lower():
                return f['id']

        return None  # No match found

    def move_drive_folder(self, folder_id, new_parent_folder_id):
        """
        Moves a folder into another folder in Google Drive.

        Args:
            service: Authenticated Drive service
            folder_id (str): ID of the folder to move
            new_parent_folder_id (str): ID of the destination folder

        Returns:
            str: The moved folder ID
        """
        # 1. Get the folder's current parents
        file = self.service.files().get(
            fileId=folder_id,
            fields="parents"
        ).execute()

        previous_parents = ",".join(file.get("parents", []))

        # 2. Move the folder
        moved_folder = self.service.files().update(
            fileId=folder_id,
            addParents=new_parent_folder_id,
            removeParents=previous_parents,
            fields="id, parents"
        ).execute()

        return moved_folder["id"]

    def share_doc_with_user(self, document_id, email, role="writer"):
        """
        Shares a Google Doc with another Google account.

        Args:
            drive_service: Authenticated Drive API service
            document_id (str): Google Doc file ID
            email (str): Email address to share with
            role (str): "reader", "commenter", or "writer"
        """

        permission = {
            "type": "user",
            "role": role,
            "emailAddress": email
        }

        self.service.permissions().create(
            fileId=document_id,
            body=permission,
            sendNotificationEmail=True
        ).execute()


    def get_subfolders_as_dict(self, PARENT_FOLDER_ID):
        """
        Returns a dictionary of subfolder names to IDs inside a designated Drive folder,
        ignoring a specific subfolder by name.
        """

        # HARD-CODED VALUES
        IGNORE_FOLDER_NAME = "Santa Teresa High School"

        folders = {}

        page_token = None
        while True:
            response = self.service.files().list(
                q=(
                    f"'{PARENT_FOLDER_ID}' in parents and "
                    "mimeType = 'application/vnd.google-apps.folder' and "
                    "trashed = false"
                ),
                fields="nextPageToken, files(id, name)",
                pageToken=page_token
            ).execute()

            for folder in response.get("files", []):
                name = folder["name"]
                if name != IGNORE_FOLDER_NAME:
                    folders[name] = folder["id"]

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return folders

    def find_sheet_id_by_name_contains(self, folder_id, name_contains):
        """
        Searches a specific Drive folder for a Google Sheet whose name
        contains the given keyword and returns its file ID.

        Args:
            drive_service: Authenticated Google Drive API service
            folder_id (str): ID of the folder to search within
            name_contains (str): Substring to match in the sheet name

        Returns:
            str or None: Google Sheet file ID
        """

        query = (
            f"'{folder_id}' in parents and "
            "mimeType = 'application/vnd.google-apps.spreadsheet' and "
            f"name contains '{name_contains}' and "
            "trashed = false"
        )

        response = self.service.files().list(
            q=query,
            fields="files(id, name)"
        ).execute()

        files = response.get("files", [])
        if not files:
            return None

        # Assume only one match
        return files[0]["id"]

    def list_google_sheet_ids(self, folder_id: str, service) -> list:
        """
        Returns a list of Google Sheet file IDs inside a Google Drive folder.

        Parameters:
            folder_id (str): The ID of the Google Drive folder.
            service_account_file (str): Path to your service account JSON key.

        Returns:
            list: A list of Google Sheet file IDs.
        """

        # Query for Google Sheets inside the folder
        query = (
            f"'{folder_id}' in parents and "
            "mimeType='application/vnd.google-apps.spreadsheet' and "
            "trashed = false"
        )

        sheet_ids = []
        page_token = None

        while True:
            response = service.files().list(
                q=query,
                fields="nextPageToken, files(id, name)",
                pageToken=page_token
            ).execute()

            for file in response.get("files", []):
                sheet_ids.append(file["id"])

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return sheet_ids

    def share_spreadsheet(self, file_id, email, role="commenter"):
        """
        Shares a Google Sheet/File with a specific email address.

        Args:
            service: Authenticated Drive API service instance.
            file_id (str): The ID of the spreadsheet to share.
            email (str): The email address of the student/user.
            role (str): 'reader', 'commenter', or 'writer' (editor). 
                        Defaults to 'commenter'.
        """
        try:
            # Create the permission object
            new_permission = {
                'type': 'user',
                'role': role,
                'emailAddress': email
            }

            # Execute the permission creation
            # sendNotificationEmail=True will send an email to the user letting them know
            permission = self.service.permissions().create(
                fileId=file_id,
                body=new_permission,
                fields='id',
                sendNotificationEmail=True 
            ).execute()

            print(f"Successfully shared with {email} as {role}. Permission ID: {permission.get('id')}")
            return permission

        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def copy_drive_file_with_number(self, original_file_id, destination_folder_id, new_name_template, sName):
        """
        Copies a Drive file and extracts a number from the original file name.

        Args:
            service: Authenticated Drive service
            original_file_id (str): ID of the source file
            destination_folder_id (str): Destination folder ID
            new_name_template (str): f-string-style template, e.g. "Invoice Copy {n}"
            sName (str): School name to append to the new file name

        Returns:
            tuple: (new_file_id (str), extracted_number (str or None))
        """
        # 1. Get original file name
        file = self.service.files().get(
            fileId=original_file_id,
            fields="name"
        ).execute()

        original_name = file["name"]

        # 2. Extract first number from name
        match = re.search(r"\d+", original_name)
        extracted_number = match.group() if match else None

        # 3. Build new name
        if extracted_number:
            new_name = new_name_template.format(n=extracted_number)
            new_name = new_name + f" - {sName}"
        else:
            new_name = new_name_template.format(n="")

        # 4. Copy file
        metadata = {
            "name": new_name,
            "parents": [destination_folder_id]
        }

        copied_file = self.service.files().copy(
            fileId=original_file_id,
            body=metadata,
            fields="id"
        ).execute()

        return copied_file["id"]


