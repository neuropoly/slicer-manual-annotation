# import os

# from pathlib import Path
# import yaml

from utils import *

SELECTED_EXISTING_FOLDER = False
PATH_SELECTED_OUTPUT_FOLDER = ''
PATH_SELECTED_VOLUMES_FOLDER = ''

class UserPath():

    def __init__(self):
        pass

    # def selected_folder(self):
    #     global SELECTED_EXISTING_FOLDER
    #     SELECTED_EXISTING_FOLDER = False




    def get_user_path(self):
        user_path = Path.home()
        print('user_path', user_path)
        return user_path

    def check_or_create_filepath(self, filename='slicercart.yml'):
        print('check_or_create_filepath')
        user_path = UserPath.get_user_path(self)
        folder_path = f'{user_path}{os.sep}.hslicercart{os.sep}'
        # filename = 'slicercart.yml'
        filepath = os.path.join(folder_path, filename)

        if not os.path.exists(folder_path):
            print('hidden path ')
            os.makedirs(folder_path)

        if not os.path.exists(filepath):
            print('writing hidden file')
            with open(filepath, 'w') as file:
                yaml.dump({}, file) # Initialize a dictionary if file created.

        return filepath

    def read_filepath(self, filename='slicercart.yml'):
        filepath = UserPath.check_or_create_filepath(self, filename)
        with open(filepath, 'r') as file:
            content = yaml.safe_load(file)

            print('content', content)
        return content

    def write_in_filepath(self, output_folder_path, volume_folder_path,
                          filename = 'slicercart.yml' ):
        filepath = UserPath.check_or_create_filepath(self, filename)
        content = UserPath.read_filepath(self)
        print('content of Userpath filepath', content)

        content[output_folder_path] = volume_folder_path
        with open(filepath, 'w') as file:
            yaml.dump(content, file)



    def reset_last_selected(self, filepath):
        with open(filepath, 'w') as file:
            yaml.dump({}, file)


    def save_selected_paths(self, output_folder_path, volume_folder_path):
        filepath = UserPath.check_or_create_filepath(self,
                                                 'last_selected_paths.yml')
        UserPath.reset_last_selected(self, filepath)
        UserPath.write_in_filepath(self, output_folder_path,
                                   volume_folder_path,'last_selected_paths.yml')


    def get_selected_paths(self):
        filepath = UserPath.check_or_create_filepath(self,
                                                     'last_selected_paths.yml')
        content = UserPath.read_filepath(self, 'last_selected_paths.yml')
        print('content', content)
        UserPath.reset_last_selected(self, filepath)
        return content

    def set_selected_existing_folder(self):
        global SELECTED_EXISTING_FOLDER
        print('selected folder variable local', SELECTED_EXISTING_FOLDER)
        SELECTED_EXISTING_FOLDER = not SELECTED_EXISTING_FOLDER
        print('SELECTED_EXISTING_FOLDER', SELECTED_EXISTING_FOLDER)

    def get_selected_existing_folder(self):
        global SELECTED_EXISTING_FOLDER
        return SELECTED_EXISTING_FOLDER











