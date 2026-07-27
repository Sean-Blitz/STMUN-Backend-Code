import sys
from Assignments import Display
import Assignments
import ServerRequests

def main():
    options = ["Assignments", "Hashes", "Database Management", "Awards", "Exit"]
    action = Display.select_option_with_pointer(options, "Welcome to the SCVMUN Board Command Line Interface! Please select an option.", "SCVMUN CLI")
    if action == "Assignments":
        options = ["Assign New Schools", "Add Delegates to a School", "Drop Delegates from a School"]
        action = Display.select_option_with_pointer(options, "Great! Select the specific option.", "SCVMUN CLI - Assignments Menu")
        
        if action == "Assign New Schools":
            Assignments.assign_new_schools()
        elif action == "Add Delegates to a School":
            Assignments.add_delegates()
        elif action == "Drop Delegates from a School":
            Assignments.drop_delegates()
    elif action == "Hashes":
        options = ["Regenerate Hashes for Delegate", "Regenerate Hashes for School"]
        action = Display.select_option_with_pointer(options, "Great! Select the specific option.", "SCVMUN CLI - Hashes Menu")

        if action == "Regnerate Hashes for Delegate":
            committee = Display.take_text_input("What is the delegate's committee? Please check the sheet's capitalization.")
            country = Display.take_text_input("What is the delegate's country assignment? Please check the sheet's capitalization.")
    elif action == "Database Management":
        pass
    elif action == "Awards":
        pass
    elif action == "Exit":
        Display.display("Exiting the SCVMUN CLI. Goodbye!")
        sys.exit()
    else:
        Display.display("Invalid option selected. Exiting.")
        sys.exit()


if __name__ == "__main__":
    main()