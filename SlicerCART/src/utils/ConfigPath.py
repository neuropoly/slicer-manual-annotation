from utils import *

class ConfigPath():
    def __init__(self):
        pass

    @enter_function
    def check_existing_configuration(self):
        path_to_saved_config_files = f'{self.outputFolder}{os.sep}{CONF_FOLDER_NAME}'
        path_to_config_copy = f'{path_to_saved_config_files}{os.sep}{CONFIG_COPY_FILENAME}'

        if os.path.exists(path_to_saved_config_files) == False:
            print('config file does not exist')
            os.makedirs(path_to_saved_config_files)

            print('about to test ocnfig file path')

            shutil.copy(CONFIG_FILE_PATH, path_to_config_copy)
            print('CONFIG FILE PATH: ', CONFIG_FILE_PATH)
            # Write the updated YAML data back to the file
            with open(path_to_config_copy, 'w') as file:
                yaml.dump({'project_conf': 'True'}, file,
                          default_flow_style=False)

        else:
            print('config file fond')

            self.path_to_config_copy = path_to_config_copy
            print('self path to config copy$$$: ', self.path_to_config_copy)
            self.config_yaml.clear()
            ConfigPath.open_project_config_file(self)
            self.get_config_values()

            ConfigPath.create_temp_file(self, name='output_path.txt',
                                        text=self.path_to_config_copy)





    # def open_project_config_file(self):
    #     """
    #     Load the appropriate configuration template: from module or project if
    #     existing.
    #     """
    #
    #     try:
    #         self.path_to_config_copy
    #         with open(self.path_to_config_copy, 'r') as file:
    #             print('self config yaml ###')
    #             print('path to config copy, :', self.path_to_config_copy)
    #             print('fil!!!!!!!!!!!!: e', file)
    #             self.config_yaml = yaml.safe_load(file)
    #     except AttributeError:
    #         with open(CONFIG_FILE_PATH, 'r') as file:
    #             print('self path to config failed ************** \n  ')
    #             self.config_yaml = yaml.safe_load(file)
    #
    #     return self.config_yaml

    # def open_project_config_file(self):
    #     """
    #     Load the appropriate configuration template: from module or project if
    #     existing.
    #     """
    #
    #     try:
    #         self.path_to_config_copy
    #         with open(self.path_to_config_copy, 'r') as file:
    #             print('self config yaml ###')
    #             print('path to config copy, :', self.path_to_config_copy)
    #             print('fil!!!!!!!!!!!!: e', file)
    #             self.config_yaml = yaml.safe_load(file)
    #     except AttributeError:
    #         with open(CONFIG_FILE_PATH, 'r') as file:
    #             print('self path to config failed ************** \n  ')
    #             self.config_yaml = yaml.safe_load(file)
    #
    #     return self.config_yaml




    @enter_function
    def open_project_config_file(self):
        """
        Load the appropriate configuration template: from module or project if
        existing.
        """

        # temp_dir = tempfile.gettempdir()
        # print('temp_dir', temp_dir)
        # temp_file_path = os.path.join(temp_dir, 'output_folder_not_selected.txt')
        # print('temp_file_path', temp_file_path)
        # temp_file_exist = True
        #
        # try:
        #     # Write some initial data to the file
        #     with open(temp_file_path, "r") as temp_file:
        #         content = temp_file.read()
        #         print(f"Contents of the file:\n{content}")
        # except FileNotFoundError:
        #     print("File not found")
        #     temp_file_exist = False
        temp_file_exist = ConfigPath.get_temp_file(self)

        if temp_file_exist:
            with open(CONFIG_FILE_PATH, 'r') as file:
                print('self path to config failed ************** \n  ')
                self.config_yaml = yaml.safe_load(file)
        else:
            temp_dir = tempfile.gettempdir()
            temp_file_path = os.path.join(temp_dir, 'output_path.txt')
            # Write some initial data to the file
            with open(temp_file_path, "r") as temp_file:
                output_path = temp_file.read()
                print(f"Contents of the file:\n{output_path}")
            with open(output_path, 'r') as file:
                print('self config yaml ###')
                print('fil!!!!!!!!!!!!: e', file)
                # print('self config yaml before reset', self.config_yaml)
                self.config_yaml = {}
                self.config_yaml = yaml.safe_load(file)
                print('\n \n \n self config yaml after reset after',
                      self.config_yaml)

        ### REBNDCU ICI METTRE DES EDEBUGS PLUS PRECIS

        return self.config_yaml

    @enter_function
    def read_config_file(self):
        temp_file_exist = ConfigPath.get_temp_file(self)
        print('temp %%%%%%% file exists: ', temp_file_exist)
        if temp_file_exist:
            with open(CONFIG_FILE_PATH, 'r') as file:
                self.config_yaml = yaml.full_load(file)
        else:
            outputh_path = ConfigPath.read_temp_file(self,
                                                     name='output_path.txt')
            print('output_path,: ', outputh_path)
            self.path_to_config_copy = outputh_path
            # self.config_yaml = ConfigPath.open_project_config_file(self)
            with open(output_path, 'r') as file:
                print('self config yaml ###')
                print('fil!!!!!!!!!!!!: e', file)
                self.config_yaml = yaml.safe_load(file)
            print('DEBUG FINAL self config yaml', self.config_yaml)
        return self.config_yaml



    @enter_function
    def verify_empty(self):
        if self.outputFolder is not None and os.path.exists(self.outputFolder):

            content_of_output_folder = os.listdir(self.outputFolder)
            if '.DS_Store' in content_of_output_folder:
                content_of_output_folder.remove('.DS_Store')

            if len(content_of_output_folder) > 0:
                self.outputFolder = None

                msg = qt.QMessageBox()
                msg.setIcon(qt.QMessageBox.Critical)
                msg.setText("Error : The output folder must be empty ")
                msg.setInformativeText(
                    'Given that there is a new configuration of SlicerCART, the output folder must be empty. ')
                msg.setWindowTitle("ERROR : The output folder must be empty ")
                msg.exec()
            else:
                self.check_existing_configuration()

    @enter_function
    def create_temp_file(self, name='output_folder_not_selected.txt', text="Output folder not yet selected.\n"):
        # print('script path 3333333', SCRIPT_PATH)
        # Create a temporary file
        temp_dir = tempfile.gettempdir()
        print('temp_dir', temp_dir)
        temp_file_path = os.path.join(temp_dir, name)
        print('temp_file_path', temp_file_path)
        # Write some initial data to the file
        with open(temp_file_path, "w") as temp_file:
            temp_file.write(text)

    @enter_function
    def get_temp_file(self, name='output_folder_not_selected.txt'):
        temp_dir = tempfile.gettempdir()
        print('temp_dir', temp_dir)
        temp_file_path = os.path.join(temp_dir, name)
        print('temp_file_path', temp_file_path)
        try:
            # Write some initial data to the file
            with open(temp_file_path, "r") as temp_file:
                content = temp_file.read()
                print(f"Contents of the file:\n{content}")
        except FileNotFoundError:
            print("File not found")
            return False

        return True

    @enter_function
    def delete_temp_file(self, name='output_folder_not_selected.txt'):
        # Get the path to the temporary file
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, name)

        # Check if the file exists
        if os.path.exists(temp_file_path):
            # Delete the file
            os.remove(temp_file_path)
            print(f"File {temp_file_path} has been deleted.")
        else:
            print(f"File not found: {temp_file_path}")

    @enter_function
    def read_temp_file(self, name='output_folder_not_selected.txt'):
        # Get the path to the temporary file
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, name)

        # Open the file and read its contents
        with open(temp_file_path, "r") as file:
            content = file.read()
            print(f"Contents of the file:\n{content}")
            print('type content:', type(content))
            return content

    # @enter_function
    # def write_config_file(self):
    #     temp_dir = tempfile.gettempdir()
    #     print('temp_dir', temp_dir)
    #     temp_file_path = os.path.join(temp_dir,
    #                                   'output_folder_not_selected.txt')
    #     print('temp_file_path', temp_file_path)
    #     temp_file_exist = True
    #
    #     try:
    #         # Write some initial data to the file
    #         with open(temp_file_path, "r") as temp_file:
    #             content = temp_file.read()
    #             print(f"Contents of the file:\n{content}")
    #     except FileNotFoundError:
    #         print("File not found")
    #         temp_file_exist = False
    #
    #     if temp_file_exist:
    #         with open(CONFIG_FILE_PATH, 'w') as file:
    #             yaml.safe_dump(self.config_yaml, file)
    #     else:
    #         print(' %%%%%% IN ELSE SAVE PUSH SINGLE LABEL')
    #         output_path = ConfigPath.read_temp_file(self,
    #                                                 name='output_path.txt')
    #         print('output_path443', output_path)
    #         with open(output_path, 'w') as file:
    #             yaml.safe_dump(self.config_yaml, file)




    @enter_function
    def write_config_file(self):
        # temp_dir = tempfile.gettempdir()
        # print('temp_dir', temp_dir)
        # temp_file_path = os.path.join(temp_dir,
        #                               'output_folder_not_selected.txt')
        # print('temp_file_path', temp_file_path)
        # temp_file_exist = True
        #
        # try:
        #     # Write some initial data to the file
        #     with open(temp_file_path, "r") as temp_file:
        #         content = temp_file.read()
        #         print(f"Contents of the file:\n{content}")
        # except FileNotFoundError:
        #     print("File not found")
        #     temp_file_exist = False
        temp_file_exist = ConfigPath.get_temp_file(self)
        print('temp_file_exist in write config file', temp_file_exist)

        if temp_file_exist:
            with open(CONFIG_FILE_PATH, 'w') as file:
                yaml.safe_dump(self.config_yaml, file)
        else:
            print(' %%%%%% IN ELSE SAVE PUSH SINGLE LABEL')
            output_path = ConfigPath.read_temp_file(self,
                                                    name='output_path.txt')
            print('output_path443', output_path)
            with open(output_path, 'w') as file:
                yaml.safe_dump(self.config_yaml, file)





