"""
This python file contains all constants values used in SlicerCART.
"""
###############################################################################
# Import all required modules for correct use
from utils.requirements import *

###############################################################################

# Initial and default configuration filenames.
CONFIG_FILENAME = "configuration_config.yml"
CONFIG_COPY_FILENAME = CONFIG_FILENAME.split('.')[0] + '--do-not-modify.yml'
CONF_FOLDER_NAME = '_conf'

TIMER_MUTEX = RLock()

# From constants.py, CONFIG_FILE_PATH required the use of
# os.path.join, which limits its usability in the utils.constants.py
# PATHS can be adjusted automatically as follow:
SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))[:-5]
print('SCRIPT_PATH from file constants.py: ', SCRIPT_PATH)

CONFIG_FILE_PATH = os.path.join(SCRIPT_PATH, 'configuration_config.yml')
print('CONFIG_FILE_PATH from file constants.py: ', CONFIG_FILE_PATH)

# Read at startup the initial config file
with open(CONFIG_FILE_PATH, 'r') as file:
    content = yaml.safe_load(file)
INITIAL_CONFIG_FILE = content

CLASSIFICATION_BOXES_LIST = ["checkboxes", "comboboxes", "freetextboxes"]

