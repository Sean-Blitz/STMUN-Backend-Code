from .GoogleAPIsManager import GoogleAPIs
from googleapiclient.discovery import build
from Infrastructure.utilities import retry_on_http_error

class DocAPI(GoogleAPIs):
    def __init__(self, SCOPES = None, CREDENTIALS_FILE = None, TOKEN_FILE = None):
        if SCOPES is None:
            super().__init__(CREDENTIALS_FILE=CREDENTIALS_FILE, TOKEN_FILE=TOKEN_FILE)
            # As defined in the parent class, if Credentials or Token file is none, it will default to the standard locations.
        elif SCOPES is not None:
            super().__init__(SCOPES=SCOPES, CREDENTIALS_FILE=CREDENTIALS_FILE, TOKEN_FILE=TOKEN_FILE)
        else:
            raise ValueError("SCOPES must be a list of scopes or None.")
        creds = self.authenticate()
        self.docs_service = build('docs', 'v1', credentials=creds)

    @retry_on_http_error()
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

    @retry_on_http_error()
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