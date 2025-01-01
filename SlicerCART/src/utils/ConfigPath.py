from utils.requirements import *
from utils.constants import *
from utils.debugging_helpers import *

OUTPUT_CONFIG_PATH = 'output_path.txt' # Name of the temp file where the path
# of the config file to use (from selected output folder). To use here only.

class ConfigPath():
    @enter_function
    def __init__(self):
        self.get_config_values(INITIAL_CONFIG_FILE)

    @enter_function
    def check_existing_configuration(self):
        """
        Check if a configuration file already exists in selected output folder.
        """

        path_to_saved_config_files = \
            f'{self.outputFolder}{os.sep}{CONF_FOLDER_NAME}'
        path_to_config_copy = \
            f'{path_to_saved_config_files}{os.sep}{CONFIG_COPY_FILENAME}'

        if os.path.exists(path_to_saved_config_files) == False:
            os.makedirs(path_to_saved_config_files)
            shutil.copy(CONFIG_FILE_PATH, path_to_config_copy)
        else:
            self.path_to_config_copy = path_to_config_copy
            self.config_yaml.clear()
            self.config_yaml = ConfigPath.open_project_config_file()
            ConfigPath.create_temp_file(name=OUTPUT_CONFIG_PATH,
                                        text=self.path_to_config_copy)

    @enter_function
    def open_project_config_file(self):
        """
        Load the appropriate configuration template from module or project if
        exists.
        """

        temp_file_exist = ConfigPath.get_temp_file()

        if temp_file_exist:
            with open(CONFIG_FILE_PATH, 'r') as file:
                self.config_yaml = yaml.safe_load(file)
        else:
            temp_dir = tempfile.gettempdir()
            temp_file_path = os.path.join(temp_dir, OUTPUT_CONFIG_PATH)
            # Read data of the temp file
            with open(temp_file_path, "r") as temp_file:
                output_path = temp_file.read()
            with open(output_path, 'r') as file:
                self.config_yaml = {}
                self.config_yaml = yaml.safe_load(file)

        return self.config_yaml

    @enter_function
    # Was in the initial code. Kept here for further usage if needed.
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
                    'Given that there is a new configuration of SlicerCART, '
                    'the output folder must be empty. ')
                msg.setWindowTitle("ERROR : The output folder must be empty ")
                msg.exec()
            else:
                self.check_existing_configuration()

    @enter_function
    def create_temp_file(self, name='output_folder_not_selected.txt',
                         text="Output folder not yet selected.\n"):
        """
        Create a temporary file for 1) using as a flag to check if output
        folder has een selected or not 2) saving the path of the config file
        in the selected output folder if selected (so it can be used).
        """

        # Create a temporary file
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, name)
        # Write some initial data to the file
        with open(temp_file_path, "w") as temp_file:
            temp_file.write(text)

    @enter_function
    def get_temp_file(self, name='output_folder_not_selected.txt'):
        """
        Verify if a specific temp file exists or not. By default, allows to
        detect if output folder has een selected or not.
        """

        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, name)

        try:
            # Write some initial data to the file
            with open(temp_file_path, "r") as temp_file:
                content = temp_file.read()
        except FileNotFoundError:
            return False

        return True

    @enter_function
    def delete_temp_file(self, name='output_folder_not_selected.txt'):
        """
        Delete a specific temp file if it exists.
        """

        # Get the path to the temporary file
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, name)

        # Check if the file exists
        if os.path.exists(temp_file_path):
            # Delete the file
            os.remove(temp_file_path)

    @enter_function
    def read_temp_file(self, name='output_folder_not_selected.txt'):
        """
        Read a specific temp file and return the contents.
        """

        # Get the path to the temporary file
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, name)

        # Open the file and read its contents
        with open(temp_file_path, "r") as file:
            content = file.read()
            return content

    @enter_function
    def write_config_file(self):
        """
        Write self.config_yaml in the appropriate location (initial or
        in the output folder configuration file).
        """

        temp_file_exist = ConfigPath.get_temp_file()

        if temp_file_exist:
            with open(CONFIG_FILE_PATH, 'w') as file:
                yaml.safe_dump(self.config_yaml, file)
        else:
            output_path = ConfigPath.read_temp_file(name=OUTPUT_CONFIG_PATH)
            with open(output_path, 'w') as file:
                yaml.safe_dump(self.config_yaml, file)

        # Ensure to get the latest config values
        ConfigPath.get_config_values(self.config_yaml)

    @enter_function
    def write_correct_path(self):
        """
        Ensure the temp file has the appropriate config file path,
        """

        path_to_saved_config_files = \
            f'{self.outputFolder}{os.sep}{CONF_FOLDER_NAME}'
        path_to_config_copy = \
            f'{path_to_saved_config_files}{os.sep}{CONFIG_COPY_FILENAME}'

        ConfigPath.create_temp_file(name=OUTPUT_CONFIG_PATH,
                                    text=path_to_config_copy)

    @enter_function
    def get_config_values(self, config=INITIAL_CONFIG_FILE):
        """
        Function moved from SlicerCART.py. Enables to select configuration
        values from a specified config file (for example, the latest). In
        fact, THIS IS A SETTER FUNCTION: it updates the config values from
        the config file passed in parameter.
        :param config: config yaml file content
        :return: config yaml file content
        """

        self.IS_DISPLAY_TIMER_REQUESTED = config[
            "is_display_timer_requested"]

        self.INPUT_FILE_EXTENSION = config["input_filetype"]
        self.DEFAULT_VOLUMES_DIRECTORY = config["default_volume_directory"]
        self.DefaultDir = self.DEFAULT_VOLUMES_DIRECTORY
        self.DEFAULT_SEGMENTATION_DIRECTORY = config[
            "default_segmentation_directory"]

        self.MODALITY = config["modality"]
        self.IS_CLASSIFICATION_REQUESTED = config[
            "is_classification_requested"]
        self.IS_SEGMENTATION_REQUESTED = config[
            "is_segmentation_requested"]
        self.IS_MOUSE_SHORTCUTS_REQUESTED = config[
            "is_mouse_shortcuts_requested"]
        self.IS_KEYBOARD_SHORTCUTS_REQUESTED = config[
            "is_keyboard_shortcuts_requested"]

        self.INTERPOLATE_VALUE = config["interpolate_value"]
        self.REQUIRE_EMPTY = config["require_empty"]
        self.ENABLE_DEBUG = config["enable_debug"]

        self.WORKING_LIST_FILENAME = config["working_list_filename"]
        self.REMAINING_LIST_FILENAME = config["remaining_list_filename"]

        self.CT_WINDOW_WIDTH = config["ct_window_width"]
        self.CT_WINDOW_LEVEL = config["ct_window_level"]

        self.REQUIRE_VOLUME_DATA_HIERARCHY_BIDS_FORMAT = config[
            "impose_bids_format"]

        self.KEEP_WORKING_LIST = config["keep_working_list"]

        if self.MODALITY == 'CT':
            # then BIDS not mandatory because it is not yet supported
            # therefore, either .nrrd or .nii.gz accepted
            REQUIRE_VOLUME_DATA_HIERARCHY_BIDS_FORMAT = False
            # CT_WINDOW_WIDTH = config["ct_window_width"]
            # CT_WINDOW_LEVEL = config["ct_window_level"]

        elif self.MODALITY == 'MRI':
            # therefore, .nii.gz required
            # INPUT_FILE_EXTENSION = '*.nii.gz'
            # user can decide whether to impose bids or not
            REQUIRE_VOLUME_DATA_HIERARCHY_BIDS_FORMAT = config[
                "impose_bids_format"]

        return config

    def set_output_folder(self, outputFolder):
        """
        Set output folder to ConfigPath class.
        """
        self.outputFolder = outputFolder


# Creating an instance of ConfigPath. This ensures that all the same
# config values will be used in the different files/modules.
ConfigPath = ConfigPath()