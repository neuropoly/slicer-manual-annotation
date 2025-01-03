"""
This class manages hidden files when the user selects Continue from existing
folder in the initial configuration setup window.
"""
from utils import *

SELECTED_EXISTING_FOLDER = False

class UserPath():

    def __init__(self):
        pass

    @enter_function
    def get_user_path(self):
        user_path = Path.home()
        return user_path

    @enter_function
    def check_or_create_filepath(self, filename='slicercart.yml'):
        user_path = UserPath.get_user_path(self)
        folder_path = f'{user_path}{os.sep}.hslicercart{os.sep}'
        filepath = os.path.join(folder_path, filename)

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        if not os.path.exists(filepath):
            with open(filepath, 'w') as file:
                yaml.dump({}, file)  # Initialize a dictionary if file created.

        return filepath

    @enter_function
    def read_filepath(self, filename='slicercart.yml'):
        filepath = UserPath.check_or_create_filepath(self, filename)

        with open(filepath, 'r') as file:
            content = yaml.safe_load(file)

        return content

    @enter_function
    def write_in_filepath(self, output_folder_path, volume_folder_path,
                          filename='slicercart.yml'):
        filepath = UserPath.check_or_create_filepath(self, filename)
        content = UserPath.read_filepath(self, filename)
        content[output_folder_path] = volume_folder_path

        with open(filepath, 'w') as file:
            yaml.dump(content, file)

    @enter_function
    def reset_last_selected(self, filepath):
        with open(filepath, 'w') as file:
            yaml.dump({}, file)

    @enter_function
    def save_selected_paths(self, output_folder_path, volume_folder_path):
        filepath = UserPath.check_or_create_filepath(self,
                                                     'last_selected_paths.yml')
        UserPath.reset_last_selected(self, filepath)
        UserPath.write_in_filepath(self, output_folder_path,
                                   volume_folder_path,
                                   'last_selected_paths.yml')

    @enter_function
    def get_selected_paths(self):
        filepath = UserPath.check_or_create_filepath(self,
                                                     'last_selected_paths.yml')
        content = UserPath.read_filepath(self, 'last_selected_paths.yml')
        UserPath.reset_last_selected(self, filepath)
        UserPath.set_selected_existing_folder(self)

        return content

    @enter_function
    def set_selected_existing_folder(self):
        global SELECTED_EXISTING_FOLDER
        SELECTED_EXISTING_FOLDER = not SELECTED_EXISTING_FOLDER

    @enter_function
    def get_selected_existing_folder(self):
        global SELECTED_EXISTING_FOLDER
        return SELECTED_EXISTING_FOLDER
