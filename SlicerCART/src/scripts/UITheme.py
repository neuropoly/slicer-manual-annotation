from utils import *

class Theme():
    def __init__(self):
        pass

    def get_mode(self):
        # Check if dark mode is enabled
        is_dark_mode = darkdetect.isDark()
        return is_dark_mode