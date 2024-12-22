###############################################################################
# Import all required modules for correct use
from utils.requirements import *

###############################################################################

# INPUT_FILE_EXTENSION = '*.nii.gz'
# INTERPOLATE_VALUE = 0

# DEFAULT_VOLUMES_DIRECTORY = ''
# DEFAULT_SEGMENTATION_DIRECTORY = ''

# REQUIRE_VOLUME_DATA_HIERARCHY_BIDS_FORMAT = False

# IS_CLASSIFICATION_REQUESTED = True
# IS_SEGMENTATION_REQUESTED = True
# IS_MOUSE_SHORTCUTS_REQUESTED = False
# IS_KEYBOARD_SHORTCUTS_REQUESTED = True

# MODALITY = 'CT'

# REQUIRE_EMPTY = True

CONFIG_FILENAME = "configuration_config.yml"
CONFIG_COPY_FILENAME = CONFIG_FILENAME.split('.')[0] + '--do-not-modify.yml'
# Moved CONFIG_FILE_PATH to the main SlicerCART.py since it uses os.path.join

CONF_FOLDER_NAME = '_conf'

# WORKING_LIST_FILENAME = 'working_list.yaml'
# REMAINING_LIST_FILENAME = 'remaining_list.yaml'

# CT_WINDOW_WIDTH = 90
# CT_WINDOW_LEVEL = 45

TIMER_MUTEX = RLock()


# From the global variables, CONFIG_FILE_PATH required the use of
# os.path.join, which limits its usability in the utils.global.variables.py
# PATHS can be adjusted automatically as follow:
SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))[:-5]
print('SCRIPT_PATH used in global variables:,', SCRIPT_PATH)

CONFIG_FILE_PATH = os.path.join(SCRIPT_PATH, 'configuration_config.yml')
print('CONFIG_FILE_PATH used in global variables:,', CONFIG_FILE_PATH)

# This variable enables/disables easier debug mode (with print) in the python
# console (e.g. Debut.set_debug(self, True) or Debut.set_debug(self, False)
# ENABLE_DEBUG = True

