import sys
from Assignments import Display
import Assignments
import ServerRequests

def main():
    options = ["Assignments", "Hashes", "Database Management", "Awards", "Exit"]
    menu_action = Display.select_option_with_pointer(options, "Welcome to the SCVMUN Board Command Line Interface! Please select an option.", "SCVMUN CLI")

    if menu_action == "Assignments":
        options = ["Assign New Schools", "Add Delegates to a School", "Drop Delegates from a School"]
        action = Display.select_option_with_pointer(options, "Great! Select the specific option.", "SCVMUN CLI - Assignments Menu")
        if action == "Assign New Schools":
            Assignments.assign_new_schools()
        elif action == "Add Delegates to a School":
            Assignments.add_delegates()
        elif action == "Drop Delegates from a School":
            Assignments.drop_delegates()

    elif menu_action == "Hashes":
        options = ["Regenerate Hashes for Delegate", "Regenerate Hashes for School"]
        action = Display.select_option_with_pointer(options, "Great! Select the specific option.", "SCVMUN CLI - Hashes Menu")
        if action == "Regenerate Hashes for Delegate":
            committee = Display.take_text_input("What is the delegate's committee? Please check the sheet's capitalization.")
            country = Display.take_text_input("What is the delegate's country assignment? Please check the sheet's capitalization.")
            Display.display(f"New hash for the delegate: {ServerRequests.regenerate_hashes_for_delegate(committee, country)}")
        elif action == "Regenerate Hashes for School":
            schoolname = Display.take_text_input("What is the school name? Please check the sheet for specific spelling and name.")
            for key in (new_hashes := ServerRequests.regenerate_hashes_for_school(schoolname)):
                Display.display(f"{key}: {new_hashes[key]}")

    elif menu_action == "Database Management":
        options = ["Export current database to CSV", "View business log", "View tech log"]
        action = Display.select_option_with_pointer(options, "Great! Select the specific option.", "SCVMUN CLI - Database Menu")
        if action == "Export current database to CSV":
            ServerRequests.export_database_to_csv()
        elif action == "View business log":
            ServerRequests.view_business_log()
        elif action == "View tech log":
            ServerRequests.view_tech_log()
        else:
            Display.display("Invalid option selected. Exiting.")
            sys.exit()

    elif menu_action == "Awards":
        options = ["Generate all submitted awards", "View committee award submission status"]
        action = Display.select_option_with_pointer(options, "Great! Select the specific option.", "SCVMUN CLI - Awards Menu")

        if action == "Generate all submitted awards":
            awards = ServerRequests.request_all_awards_data()
            # Function to request awards, run script with the function's output to generate awards in Google Slides. Separate ST Delegates!
        elif action == "View committee award submission status":
            awards = ServerRequests.request_all_awards_data()
            # Function to request awards, and display which committees have submitted awards and which have not.

    elif menu_action == "Exit":
        Display.display("Exiting the SCVMUN CLI. Goodbye!")
        sys.exit()

    else:
        Display.display("Invalid option selected. Exiting.")
        sys.exit()


if __name__ == "__main__":
    main()