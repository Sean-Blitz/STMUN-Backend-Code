import questionary

class QuestionaryClass:
    def __init__(self) -> None:
        pass

    def display_list(self, menu_choices, promptText, exitOption):
        # Add a clear exit option at the bottom of the list
        menu_choices.append(exitOption)

        # 2. Render the primary navigation menu
        selected_choice = questionary.select(
            promptText,
            choices=menu_choices
        ).ask()

        # Handle the break condition
        if selected_choice == exitOption or selected_choice is None:
            print("Exiting modification menu...")
            selected_choice = "exit"
        
        return selected_choice

    def typing_with_pre_fill(self, promptText, preFillText):
        typedString = questionary.text(
            promptText,
            default=preFillText # Pre-fills the line so they can type over it
        ).ask()
        return typedString
    
    def press_any_key_to_continue(self):
        questionary.press_any_key_to_continue().ask()