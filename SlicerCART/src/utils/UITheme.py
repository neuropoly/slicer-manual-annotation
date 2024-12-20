from utils import *

class Theme():
    def __init__(self):
        pass

    # @enter_function
    # def get_mode(self):
    #     # Check if dark mode is enabled
    #     is_dark_mode = darkdetect.isDark()
    #     return is_dark_mode

    @enter_function
    def get_mode(self):
        # from qt import QApplication, QPalette
        # Get the current application's instance
        app = QApplication.instance()
        if not app:
            raise RuntimeError("No QApplication instance found")

        # Access the application's palette
        palette = app.palette()
        # Check the background color lightness
        background_color = palette.color(QPalette.Window)
        is_dark_mode = background_color.lightness() < 128
        return "dark" if is_dark_mode else "light"

    @enter_function
    def set_foreground(self, theme):
        if theme == "dark":
            return 'white'
        if theme == "light":
            return 'black'

