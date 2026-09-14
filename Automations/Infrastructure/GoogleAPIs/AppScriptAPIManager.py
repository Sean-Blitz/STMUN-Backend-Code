from .GoogleAPIsManager import GoogleAPIs
from googleapiclient.discovery import build
from Infrastructure.utilities import retry_on_http_error

class AppScriptAPI(GoogleAPIs):
    def __init__(self):
        super().__init__(SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/documents', "https://www.googleapis.com/auth/script.projects"])
        creds = self.authenticate()
        self.service = build('script', 'v1', credentials=creds)

    @retry_on_http_error()
    def attach_script_to_sheet(self, new_sheet_id: str, TEMPLATE_SCRIPT_ID: str):
        """Copies the Apps Script code from the template project into a new sheet."""
        
        # 1. Fetch the files (Code.gs, appsscript.json, etc.) from the template script
        template_content = self.service.projects().getContent(
            scriptId=TEMPLATE_SCRIPT_ID
        ).execute()

        # 2. Create a new container-bound script project inside the new sheet
        new_project = self.service.projects().create(
            body={
                "title": "Member Dashboard Sync",
                "parentId": new_sheet_id
            }
        ).execute()

        new_script_id = new_project['scriptId']

        # 3. Push the template's code files into the new script project
        self.service.projects().updateContent(
            scriptId=new_script_id,
            body={
                "files": template_content.get('files', [])
            }
        ).execute()

        print(f"Successfully attached Apps Script project to sheet {new_sheet_id}")
        return new_script_id