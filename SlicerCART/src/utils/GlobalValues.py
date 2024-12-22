# from utils import *
# from utils.debugging_helpers import enter_function
# from utils import *
from utils.requirements import *
from utils.ConfigPath import *
from utils.debugging_helpers import *

class GlobalValues:
    @enter_function
    def __init__(self):
        self.get_config_values()
        # self.config_yaml = ConfigPath.open_project_config_file
        print('self config yal in global values', self.config_yaml)
        self.INPUT_FILE_EXTENSION = INPUT_FILE_EXTENSION
        self.DEFAULT_VOLUMES_DIRECTORY = DEFAULT_VOLUMES_DIRECTORY
        self.DEFAULT_SEGMENTATION_DIRECTORY = DEFAULT_SEGMENTATION_DIRECTORY
        self.REQUIRE_VOLUME_DATA_HIERARCHY_BIDS_FORMAT = REQUIRE_VOLUME_DATA_HIERARCHY_BIDS_FORMAT
        self.MODALITY = MODALITY
        self.IS_CLASSIFICATION_REQUESTED = IS_CLASSIFICATION_REQUESTED
        self.IS_SEGMENTATION_REQUESTED = IS_SEGMENTATION_REQUESTED
        self.IS_MOUSE_SHORTCUTS_REQUESTED = IS_MOUSE_SHORTCUTS_REQUESTED
        self.IS_KEYBOARD_SHORTCUTS_REQUESTED = IS_KEYBOARD_SHORTCUTS_REQUESTED
        self.INTERPOLATE_VALUE = INTERPOLATE_VALUE
        self.CT_WINDOW_WIDTH = CT_WINDOW_WIDTH
        self.CT_WINDOW_LEVEL = CT_WINDOW_LEVEL
        self.IS_DISPLAY_TIMER_REQUESTED = IS_DISPLAY_TIMER_REQUESTED
        self.REQUIRE_EMPTY = REQUIRE_EMPTY
        self.WORKING_LIST_FILENAME = WORKING_LIST_FILENAME
        self.REMAINING_LIST_FILENAME = REMAINING_LIST_FILENAME
        # self.ENABLE_DEBUG = ENABLE_DEBUG


    @enter_function
    def get_config_values(self):
        # Select the appropriate configuration file.
        self.config_yaml = ConfigPath.open_project_config_file(self)

        global INPUT_FILE_EXTENSION
        global DEFAULT_VOLUMES_DIRECTORY
        global DEFAULT_SEGMENTATION_DIRECTORY
        global REQUIRE_VOLUME_DATA_HIERARCHY_BIDS_FORMAT
        global MODALITY
        global IS_CLASSIFICATION_REQUESTED
        global IS_SEGMENTATION_REQUESTED
        global IS_MOUSE_SHORTCUTS_REQUESTED
        global IS_KEYBOARD_SHORTCUTS_REQUESTED
        global INTERPOLATE_VALUE
        global CT_WINDOW_WIDTH
        global CT_WINDOW_LEVEL
        global IS_DISPLAY_TIMER_REQUESTED
        global REQUIRE_EMPTY
        global WORKING_LIST_FILENAME
        global REMAINING_LIST_FILENAME
        global ENABLE_DEBUG

        IS_DISPLAY_TIMER_REQUESTED = self.config_yaml[
            "is_display_timer_requested"]

        INPUT_FILE_EXTENSION = self.config_yaml["input_filetype"]
        print('input file Extension in slicercart', INPUT_FILE_EXTENSION)

        DEFAULT_VOLUMES_DIRECTORY = self.config_yaml["default_volume_directory"]
        self.DefaultDir = DEFAULT_VOLUMES_DIRECTORY
        DEFAULT_SEGMENTATION_DIRECTORY = self.config_yaml[
            "default_segmentation_directory"]
        MODALITY = self.config_yaml["modality"]
        IS_CLASSIFICATION_REQUESTED = self.config_yaml[
            "is_classification_requested"]
        IS_SEGMENTATION_REQUESTED = self.config_yaml[
            "is_segmentation_requested"]
        IS_MOUSE_SHORTCUTS_REQUESTED = self.config_yaml[
            "is_mouse_shortcuts_requested"]
        IS_KEYBOARD_SHORTCUTS_REQUESTED = self.config_yaml[
            "is_keyboard_shortcuts_requested"]
        INTERPOLATE_VALUE = self.config_yaml["interpolate_value"]

        REQUIRE_EMPTY = self.config_yaml["require_empty"]
        ENABLE_DEBUG = self.config_yaml["enable_debug"]


        WORKING_LIST_FILENAME = self.config_yaml["working_list_filename"]
        REMAINING_LIST_FILENAME = self.config_yaml["remaining_list_filename"]

        CT_WINDOW_WIDTH = self.config_yaml["ct_window_width"]
        CT_WINDOW_LEVEL = self.config_yaml["ct_window_level"]
        REQUIRE_VOLUME_DATA_HIERARCHY_BIDS_FORMAT = self.config_yaml[
            "impose_bids_format"]

        if MODALITY == 'CT':
            # then BIDS not mandatory because it is not yet supported
            # therefore, either .nrrd or .nii.gz accepted
            REQUIRE_VOLUME_DATA_HIERARCHY_BIDS_FORMAT = False
            # CT_WINDOW_WIDTH = self.config_yaml["ct_window_width"]
            # CT_WINDOW_LEVEL = self.config_yaml["ct_window_level"]

        elif MODALITY == 'MRI':
            # therefore, .nii.gz required
            # INPUT_FILE_EXTENSION = '*.nii.gz'
            # user can decide whether to impose bids or not
            REQUIRE_VOLUME_DATA_HIERARCHY_BIDS_FORMAT = self.config_yaml[
                "impose_bids_format"]

GlobalValues = GlobalValues()