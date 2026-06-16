import base64
from .GoogleAPIsManager import GoogleAPIs
from googleapiclient.discovery import build

class GmailAPI(GoogleAPIs):
    def __init__(self):
        super().__init__(CREDENTIALS_FILE="credentials.json", TOKEN_FILE = "token.json", SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/documents'])
        creds = self.authenticate()
        self.service = build('gmail', 'v1', credentials=creds)


    def extract_strings_and_remove_label(self, message_ids):
        """
        Scans Gmail messages, extracts text between two known strings,
        and removes the 'Finances Automation' label after successful processing.

        Args:
            service: Authenticated Gmail API service
            message_ids (list[str]): Gmail message IDs to scan
            start_text (str): Text before the desired value
            end_text (str): Text after the desired value

        Returns:
            list[str]: Extracted strings
        """

        LABEL_ID = "Label_5677633099299886303" # If you ever change the label in gmail, change this too.
        start_text = "Please check the form for updates for "
        end_text = "."
        extracted_values = []

        for msg_id in message_ids:
            message = self.service.users().messages().get(
                userId="me",
                id=msg_id,
                format="full"
            ).execute()

            payload = message.get("payload", {})
            parts = payload.get("parts", [])

            body_text = ""

            # Try multipart (most emails)
            for part in parts:
                if part.get("mimeType") == "text/plain":
                    data = part["body"].get("data")
                    if data:
                        body_text = base64.urlsafe_b64decode(data).decode("utf-8")
                        break

            # Fallback for simple emails
            if not body_text:
                data = payload.get("body", {}).get("data")
                if data:
                    body_text = base64.urlsafe_b64decode(data).decode("utf-8")

            # Extract text between markers
            if start_text in body_text and end_text in body_text:
                start_index = body_text.find(start_text) + len(start_text)
                end_index = body_text.find(end_text, start_index)

                if end_index != -1:
                    extracted = body_text[start_index:end_index].strip()
                    extracted_values.append(extracted)

                    # Remove the "Finances Automation" label
                    self.service.users().messages().modify(
                        userId="me",
                        id=msg_id,
                        body={"removeLabelIds": [LABEL_ID]}
                    ).execute()

        return extracted_values

    def find_emails_from_sender_with_label(self):
        """
        Finds Gmail messages from a specific sender that have
        the 'Finances Automation' label applied.

        Args:
            service: Authenticated Gmail API service

        Returns:
            list[str]: Gmail message IDs
        """

        SENDER_EMAIL = "noreply+automations@airtableemail.com"
        LABEL_NAME = "Finances Automation"

        # Gmail search query
        query = f'from:{SENDER_EMAIL} label:"{LABEL_NAME}"'

        results = self.service.users().messages().list(
            userId="me",
            q=query
        ).execute()

        messages = results.get("messages", [])

        return [msg["id"] for msg in messages]