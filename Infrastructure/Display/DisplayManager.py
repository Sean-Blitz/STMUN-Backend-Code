import questionary
import sys

class DisplayClass:
    def __init__(self) -> None:
        pass

    def display(self, *message):
        print(*message)

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
