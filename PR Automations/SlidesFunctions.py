def duplicate_slide(slides_service, presentation_id, slide_object_id):
    """
    Duplicates a slide in a Google Slides presentation and returns the new slide's object ID.
    """

    body = {
        "requests": [
            {
                "duplicateObject": {
                    "objectId": slide_object_id
                }
            }
        ]
    }

    response = slides_service.presentations().batchUpdate(
        presentationId=presentation_id,
        body=body
    ).execute()

    # The API returns a list of replies; the first one contains the new object ID
    new_slide_id = response["replies"][0]["duplicateObject"]["objectId"]
    return new_slide_id

def replace_placeholders(service, presentation_id, value_map):
    """
    Replace placeholders in a Google Slides presentation.

    Args:
        service: Authorized Google Slides API service instance
        presentation_id: The ID of the presentation
        value_map: Dict of {placeholder: replacement_value}
    """

    requests = []

    for placeholder, new_value in value_map.items():
        requests.append({
            "replaceAllText": {
                "containsText": {
                    "text": placeholder,
                    "matchCase": True
                },
                "replaceText": str(new_value)
            }
        })

    body = {"requests": requests}

    response = service.presentations().batchUpdate(
        presentationId=presentation_id,
        body=body
    ).execute()

    return response

def replace_two_placeholders_on_slide(slides_service,presentation_id,slide_id,old_placeholder_1,new_placeholder_1,old_placeholder_2,new_placeholder_2):
    """
    Replaces two different placeholders on a specific slide with new placeholder names.
    Only affects the slide whose ID is passed in.
    """

    body = {
        "requests": [
            {
                "replaceAllText": {
                    "containsText": {
                        "text": old_placeholder_1,
                        "matchCase": True
                    },
                    "replaceText": new_placeholder_1,
                    "pageObjectIds": [slide_id]
                }
            },
            {
                "replaceAllText": {
                    "containsText": {
                        "text": old_placeholder_2,
                        "matchCase": True
                    },
                    "replaceText": new_placeholder_2,
                    "pageObjectIds": [slide_id]
                }
            }
        ]
    }

    response = slides_service.presentations().batchUpdate(
        presentationId=presentation_id,
        body=body
    ).execute()

    # Return how many replacements were made for each placeholder
    reply1 = response.get("replies", [{}])[0].get("replaceAllText", {}).get("occurrencesChanged", 0)
    reply2 = response.get("replies", [{}])[1].get("replaceAllText", {}).get("occurrencesChanged", 0)

    return reply1, reply2

def get_first_slide_id(slides_service, presentation_id):
    """
    Returns the object ID of the first slide in a Google Slides presentation.
    """

    presentation = slides_service.presentations().get(
        presentationId=presentation_id
    ).execute()

    first_slide = presentation["slides"][0]
    return first_slide["objectId"]
