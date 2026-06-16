from .GoogleAPIsManager import GoogleAPIs
from googleapiclient.discovery import build

class DocAPI(GoogleAPIs):
    def __init__(self):
        super().__init__(CREDENTIALS_FILE="credentials.json", TOKEN_FILE = "token.json", SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/documents'])
        creds = self.authenticate()
        self.docs_service = build('docs', 'v1', credentials=creds)

    def fill_doc_placeholders(self, document_id, aEmail, schoolName, sheeturl):
        """
        Replaces three hardcoded placeholders in a Google Doc.

        Placeholders expected in the Doc:
        {{aEmail}}
        {{schoolName}}
        {{sheeturl}}
        """

        requests = [
            {
                "replaceAllText": {
                    "containsText": {
                        "text": "{{aEmail}}",
                        "matchCase": True
                    },
                    "replaceText": aEmail
                }
            },
            {
                "replaceAllText": {
                    "containsText": {
                        "text": "{{schoolName}}",
                        "matchCase": True
                    },
                    "replaceText": schoolName
                }
            },
            {
                "replaceAllText": {
                    "containsText": {
                        "text": "{{sheeturl}}",
                        "matchCase": True
                    },
                    "replaceText": sheeturl
                }
            }
        ]

        self.docs_service.documents().batchUpdate(
            documentId=document_id,
            body={"requests": requests}
        ).execute()