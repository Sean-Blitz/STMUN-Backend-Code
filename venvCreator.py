import os
import venv

def create_virtual_env(target_folder, venv_name=".venv"):
    """
    Creates a virtual environment inside a specific target folder.
    """
    # Combine the folder path and the environment name
    venv_dir = os.path.join(target_folder, venv_name)
    
    print(f"Creating virtual environment at: {venv_dir}")
    
    venv.create(venv_dir, with_pip=True)
    
    print("Virtual environment successfully created!")
    print(f"To activate it, run the appropriate command from your terminal:")
    print(f"  Mac/Linux: source {os.path.join(venv_dir, 'bin', 'activate')}")
    print(f"  Windows:   {os.path.join(venv_dir, 'Scripts', 'activate')}")

if __name__ == "__main__":
    # Replace this with the path to your target folder
    # Use "." to build it directly inside your current working directory
    target_directory = input("Enter the path to the target folder to create venv inside: ")
    
    create_virtual_env(target_directory)