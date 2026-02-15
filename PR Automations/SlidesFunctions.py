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

def apply_value_map_to_slide(slides_service,presentation_id,slide_id,value_map):
    """
    Accepts a dictionary mapping placeholder names to replacement values.
    Applies all replacements to a single slide in one batchUpdate call.
    
    Example value_map:
        {
            "{Country_2}": "Canada",
            "{City_2}": "Toronto"
        }
    """

    requests = []

    for placeholder, value in value_map.items():
        requests.append({
            "replaceAllText": {
                "containsText": {
                    "text": placeholder,
                    "matchCase": True
                },
                "replaceText": value,
                "pageObjectIds": [slide_id]
            }
        })

    body = {"requests": requests}

    response = slides_service.presentations().batchUpdate(
        presentationId=presentation_id,
        body=body
    ).execute()

    # Return a list of occurrence counts for each placeholder
    counts = [
        reply["replaceAllText"]["occurrencesChanged"]
        for reply in response["replies"]
    ]

    return counts

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
    reply1 = response["replies"][0]["replaceAllText"]["occurrencesChanged"]
    reply2 = response["replies"][1]["replaceAllText"]["occurrencesChanged"]

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
