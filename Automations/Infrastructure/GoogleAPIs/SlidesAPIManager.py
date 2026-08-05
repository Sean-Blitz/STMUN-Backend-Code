from GoogleAPIsManager import GoogleAPIs
from googleapiclient.discovery import build

class SlideAPI(GoogleAPIs):
    def __init__(self):
        super().__init__(CREDENTIALS_FILE="credentials.json", TOKEN_FILE = "token.json", SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/documents'])
        creds = self.authenticate()
        self.self = build('slides', 'v1', credentials=creds)

    
    def duplicate_slide(self, presentation_id, slide_object_id):
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

        response = self.presentations().batchUpdate(
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

    def replace_two_placeholders_on_slide(self,presentation_id,slide_id,old_placeholder_1,new_placeholder_1,old_placeholder_2,new_placeholder_2):
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

        response = self.presentations().batchUpdate(
            presentationId=presentation_id,
            body=body
        ).execute()

        # Return how many replacements were made for each placeholder
        reply1 = response.get("replies", [{}])[0].get("replaceAllText", {}).get("occurrencesChanged", 0)
        reply2 = response.get("replies", [{}])[1].get("replaceAllText", {}).get("occurrencesChanged", 0)

        return reply1, reply2

    def get_first_slide_id(self, presentation_id):
        """
        Returns the object ID of the first slide in a Google Slides presentation.
        """

        presentation = self.presentations().get(
            presentationId=presentation_id
        ).execute()

        first_slide = presentation["slides"][0]
        return first_slide["objectId"]

    def create_slide_copies(self, presentation_id, template_slide_id, number_of_copies):
        """
        Duplicates a template slide N times.

        Returns:
            (count_created, [list_of_slide_ids])
        """

        created_slide_ids = []

        for i in range(number_of_copies):
            new_slide_id = self.duplicate_slide(
                presentation_id,
                template_slide_id
            )
            created_slide_ids.append(new_slide_id)

        return len(created_slide_ids), created_slide_ids

    def move_slides_to_indexes(self, presentation_id, slide_ids, target_indexes):
        if len(slide_ids) != len(target_indexes):
            raise ValueError("slide_ids and target_indexes must match length.")

        # Sort by target index ascending
        moves = sorted(zip(slide_ids, target_indexes), key=lambda x: x[1])

        for i, (slide_id, target_index) in enumerate(moves):
            # Get current slide count before move
            presentation = self.presentations().get(presentationId=presentation_id).execute()
            current_slide_count = len(presentation.get("slides", []))

            # Cap target_index at the end
            if target_index > current_slide_count:
                target_index = current_slide_count

            request = {
                "requests": [
                    {
                        "updateSlidesPosition": {
                            "slideObjectIds": [slide_id],
                            "insertionIndex": target_index
                        }
                    }
                ]
            }

            self.presentations().batchUpdate(
                presentationId=presentation_id,
                body=request
            ).execute()

        print("Finished moving slides.")

    def get_slide_id_by_index(self, presentation_id, index):
        """
        Returns the objectId of the slide at the given index.

        Args:
            self: Authenticated Google Slides API service.
            presentation_id (str): ID of the presentation.
            index (int): 0-based slide index.

        Returns:
            str: The slide's objectId.
        """

        if not isinstance(index, int) or index < 0:
            raise ValueError("Index must be a non-negative integer.")

        presentation = self.presentations().get(
            presentationId=presentation_id
        ).execute()

        slides = presentation.get("slides", [])

        if index >= len(slides):
            raise IndexError(
                f"Index {index} out of range. Presentation has {len(slides)} slides."
            )

        return slides[index]["objectId"]

    def replace_placeholders_on_slide(
        self,
        presentation_id,
        slide_id,
        value_map
    ):
        """
        Replaces placeholders on a single slide only.

        Args:
            self: Authenticated Google Slides API service
            presentation_id (str): ID of the presentation
            slide_id (str): Object ID of the slide to modify
            value_map (dict): {placeholder_text: replacement_text}

        Example value_map:
            {
                "{COUNTRY_1}": "France",
                "{COUNTRY_2}": "Germany"
            }
        """

        if not value_map:
            return

        requests = []

        for placeholder, new_value in value_map.items():
            requests.append({
                "replaceAllText": {
                    "containsText": {
                        "text": placeholder,
                        "matchCase": True
                    },
                    "replaceText": new_value,
                    "pageObjectIds": [slide_id]  # 🔥 restrict to this slide only
                }
            })

        body = {"requests": requests}

        self.presentations().batchUpdate(
            presentationId=presentation_id,
            body=body
        ).execute()

    def get_slide_count(self, presentation_id):
        """
        Returns the number of slides in a Google Slides presentation.

        Args:
            self: Authenticated Google Slides API service
            presentation_id (str): ID of the presentation

        Returns:
            int: Number of slides
        """

        presentation = self.presentations().get(
            presentationId=presentation_id,
            fields="slides(objectId)"  # only fetch slide IDs (faster)
        ).execute()

        slides = presentation.get("slides", [])
        return len(slides)

    def reverse_all_slides(self, presentation_id):
        """
        Reverses the order of all slides in a presentation.
        """

        # Get slide IDs in current order
        presentation = self.presentations().get(
            presentationId=presentation_id,
            fields="slides(objectId)"
        ).execute()

        slides = presentation.get("slides", [])
        slide_ids = [slide["objectId"] for slide in slides]

        if len(slide_ids) <= 1:
            return

        reversed_ids = list(reversed(slide_ids))

        requests = []

        # Move each slide to its new position
        for new_index, slide_id in enumerate(reversed_ids):
            requests.append({
                "updateSlidesPosition": {
                    "slideObjectIds": [slide_id],
                    "insertionIndex": new_index
                }
            })

        self.presentations().batchUpdate(
            presentationId=presentation_id,
            body={"requests": requests}
        ).execute()

    def delete_slide(self, presentation_id, slide_id):
        """
        Deletes a slide from a presentation using its object ID.

        Args:
            self: Authenticated Google Slides API service
            presentation_id (str): ID of the presentation
            slide_id (str): Object ID of the slide to delete
        """

        request = {
            "requests": [
                {
                    "deleteObject": {
                        "objectId": slide_id
                    }
                }
            ]
        }

        self.presentations().batchUpdate(
            presentationId=presentation_id,
            body=request
        ).execute()