import os
import sys
from slicer.ScriptedLoadableModule import *

# import os
# import sys
#
# # Get the absolute path of the main folder (SlicerCART)
# script_folder = os.path.dirname(__file__)
# main_path = os.path.abspath(os.path.join(script_folder, ".."))  # Go up one level
# print("Main path %%%", main_path)
#
# # Add the main_path to sys.path to import slicerCART.py
# if main_path not in sys.path:
#     sys.path.append(main_path)
#
# # Import the main script (slicerCART)
# from ..src.SlicerCART import *


def ppcheck():
    print('in Checkfunction')
    return 'coucou'

class MyBicycle():
    def __init__(self):
        self.wheel = '4'

    def roll_wheel(self):
        print('self wheel 4444444')

# MyBicycle = MyBicycle()

# bebe.fly_wings()

# goodby()

# test = MyPlane()


