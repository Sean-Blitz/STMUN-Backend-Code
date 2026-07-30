import questionary
import sys

class DisplayClass:
    def __init__(self) -> None:
        pass

    def display(self, *message):
        print(*message)

    def take_text_input(self, *promptText):
        return input(*promptText)

    def go_one_line_up(self):
        # ANSI escape code to move the cursor up one line
        sys.stdout.write("\033[F")
        sys.stdout.flush()
    
    def clear_current_line(self):
        # ANSI escape code to clear the current line
        sys.stdout.write("\033[K")
        sys.stdout.flush()

    def display_list_of_selections(self, menu_choices, promptText, exitOption):
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

    def display_list_of_selections_multi_select(self, menu_choices, prompt_text, exit_option):
        """
        Renders a multi-select checkbox menu.
        Allows toggling multiple choices and includes a done/exit option at the bottom.
        """
        # 1. Format choices for questionary.checkbox
        # We convert string options into questionary.Choice objects.
        checkbox_choices = [
            questionary.Choice(title=choice, value=choice) 
            for choice in menu_choices
        ]

        # Add a visual separator and the exit/done option at the bottom
        checkbox_choices.append(questionary.Separator())
        checkbox_choices.append(questionary.Choice(title=f"-> {exit_option}", value="EXIT_KEY"))

        # 2. Render the checkbox prompt
        # Users press Spacebar to select/deselect, and Enter when finished.
        selected_choices = questionary.checkbox(
            f"{prompt_text} (Use Space to select, Enter to finish):",
            choices=checkbox_choices
        ).ask()

        # 3. Handle exit condition or cancelled prompt (e.g., Ctrl+C)
        if selected_choices is None or "EXIT_KEY" in selected_choices:
            # Filter out the exit key if any other items were checked alongside it
            selected_choices = [c for c in selected_choices if c != "EXIT_KEY"] if selected_choices else []
            print("Exiting selection menu...")
            
            # If no other choices were picked, return "exit" string or empty list as needed
            if not selected_choices:
                return "exit"

        return selected_choices

    def typing_with_pre_fill(self, promptText, preFillText):
        typedString = questionary.text(
            promptText,
            default=preFillText # Pre-fills the line so they can type over it
        ).ask()
        return typedString
    
    def press_any_key_to_continue(self):
        questionary.press_any_key_to_continue().ask()

    def select_option_with_pointer(self, options, promptText, Title):
        """
        Takes a list of options and prompts the user to select one
        using an interactive arrow-key CLI menu.
        
        Arguments:
        options (list): List of options
        
        Returns:
        str: The name of the school chosen by the user.
        """
        if not options:
            print("\n All schools have been assigned! Nothing left to process.")
            sys.exit(0)
            
        print("\n" + "="*40)
        print(Title)
        print("="*40)
        
        selected = questionary.select(
            promptText,
            choices=options,
            pointer="-->",               
            use_indicator=True          
        ).ask()
        
        return selected
