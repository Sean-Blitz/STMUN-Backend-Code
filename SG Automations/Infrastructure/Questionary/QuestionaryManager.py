import questionary

class QuestionaryClass:
    def __init__(self) -> None:
        pass

    def display_list(self, menu_choices):
        # Add a clear exit option at the bottom of the list
        menu_choices.append("Save and Exit")

        # 2. Render the primary navigation menu
        selected_choice = questionary.select(
            "Select a delegate to modify their assignment:",
            choices=menu_choices
        ).ask()

        # Handle the break condition
        if selected_choice == "Save and Exit" or selected_choice is None:
            print("Exiting modification menu...")
            selected_choice = "exit"
        
        return selected_choice

    def typing_with_pre_fill(self, promptText, preFillText):
        new_committee = questionary.text(
            promptText,
            default=preFillText # Pre-fills the line so they can type over it
        ).ask()
        return new_committee