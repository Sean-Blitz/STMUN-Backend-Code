def fill_doc_placeholders(docs_service, document_id, aEmail, schoolName, sheeturl):
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

    docs_service.documents().batchUpdate(
        documentId=document_id,
        body={"requests": requests}
    ).execute()