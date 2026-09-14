from .GoogleAPIsManager import GoogleAPIs
from googleapiclient.discovery import build

class DocAPI(GoogleAPIs):
    def __init__(self):
        super().__init__(SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/documents', "https://www.googleapis.com/auth/script.projects"])
        creds = self.authenticate()
        self.docs_service = build('docs', 'v1', credentials=creds)

    def fill_doc_placeholders(self, document_id, aEmail, schoolName, sheeturl, headDelegateEmail):
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
            },
            {
                "replaceAllText": {
                    "containsText": {
                        "text": "{{headDelegateEmail}}",
                        "matchCase": True
                    },
                    "replaceText": headDelegateEmail
                }
            }
        ]

        self.docs_service.documents().batchUpdate(
            documentId=document_id,
            body={"requests": requests}
        ).execute()

    def fill_doc_placeholders_from_dictionary(self, document_id, replacements: dict):
        """
        Replaces placeholders in a Google Doc based on a dictionary of replacements.
        """
        requests = []

        for placeholder, replacement in replacements.items():
            requests.append({
                "replaceAllText": {
                    "containsText": {
                        "text": placeholder,
                        "matchCase": True
                    },
                    "replaceText": replacement
                }
            })

        self.docs_service.documents().batchUpdate(
            documentId=document_id,
            body={"requests": requests}
        ).execute()