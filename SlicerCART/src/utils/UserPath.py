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
        print('filepath in read filepath', filepath)
        print('filename in read filepath', filename)

        with open(filepath, 'r') as file:
            content = yaml.safe_load(file)

        print('conent in read filepath', content)

        return content

    @enter_function
    def write_in_filepath(self, output_folder_path, volume_folder_path,
                          filename='slicercart.yml'):
        filepath = UserPath.check_or_create_filepath(self, filename)
        print('filepath in write in filepath', filepath)
        content = UserPath.read_filepath(self, filename)
        content[output_folder_path] = volume_folder_path
        print('content 222 in write in filepath', content)
        with open(filepath, 'w') as file:
            yaml.dump(content, file)



        # content[output_folder_path] = volume_folder_path
        #
        # with open(filepath, 'w') as file:
        #     yaml.dump(content, file)

    @enter_function
    def reset_last_selected(self, filepath):
        with open(filepath, 'w') as file:
            yaml.dump({}, file)

    @enter_function
    def save_selected_paths(self, output_folder_path, volume_folder_path):
        filepath = UserPath.check_or_create_filepath(self,
                                                     'last_selected_paths.yml')

        with open(filepath, 'r') as file:
            anika = yaml.safe_load(file)
        print('anika', anika)

        print('in save selected path outpuf folder', output_folder_path)
        print('volume folder path', volume_folder_path)


        UserPath.reset_last_selected(self, filepath)

        with open(filepath, 'r') as file:
            anika = yaml.safe_load(file)
        print('anika2', anika)

        print()

        UserPath.write_in_filepath(self, output_folder_path,
                                   volume_folder_path,
                                   'last_selected_paths.yml')

        with open(filepath, 'r') as file:
            anika = yaml.safe_load(file)
        print('anika3', anika)

    @enter_function
    def get_selected_paths(self):
        filepath = UserPath.check_or_create_filepath(self,
                                                     'last_selected_paths.yml')
        print('filepath in get selected path', filepath)
        content = UserPath.read_filepath(self, 'last_selected_paths.yml')
        print('content in get selected path', content)
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
