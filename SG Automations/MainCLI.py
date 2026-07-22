
import sys

from Assignments import Display
import Assignments


def main():
    options = ["Assignments", "Hashes", "Database Management", "Exit"]
    action = Display.select_option_with_pointer(options, "Welcome to the SCVMUN Board Command Line Interface! Please select an option.", "SCVMUN CLI")
    if action == "Assignments":
        options = ["Assign New Schools", "Add Delegates to a School", "Drop Delegates from a School"]
        action = Display.select_option_with_pointer(options, "Great! Select the specific option today.", "SCVMUN CLI - Assignments Menu")
        
        if action == "Assign New Schools":
            Assignments.assign_new_schools()
        elif action == "Add Delegates to a School":
            Assignments.add_delegates()
        elif action == "Drop Delegates from a School":
            Assignments.drop_delegates()
    elif action == "Hashes":
        pass
    elif action == "Database Management":
        pass
    elif action == "Exit":
        print("Exiting the SCVMUN CLI. Goodbye!")
        sys.exit()
    else:
        print("Invalid option selected. Exiting.")
        sys.exit()

def display(message):
    print(message)


if __name__ == "__main__":
    main()