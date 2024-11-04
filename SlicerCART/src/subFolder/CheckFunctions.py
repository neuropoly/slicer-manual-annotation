from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

def ppcheck():
    print('in Checkfunction')
    return 'coucou'

class MyBicycle():
    def __init__(self):
        self.wheel = '4'

    def roll_wheel(self):
        print('self wheel 4444444')

# MyBicycle = MyBicycle()

