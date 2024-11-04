from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

import subFolder.CheckFunctions as cf

def jacques():
    print('helo jacques')

x = 'abcd'

def testing():
    return x

def use_maxime(y):
    print(y)

def other_file_same_level():
    ddd = cf.ppcheck()
    print(ddd)


bicycle = cf.MyBicycle()
