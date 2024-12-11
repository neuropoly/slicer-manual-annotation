# To install a package in slicer python environment, use the following command:
# pip install --user package_name
import os
import logging
import slicer

# Qt installation may lead the module to fail.
try:
    print('try import qt.')
    import qt
except ImportError:
    print('import qt failed. PLEASE VERIFY QT INSTALLATION INTO 3D SLICER '
          'BEFORE ANY FURTHER USE..')
    #ToDo: add code to install Qt on all operating systems

from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from glob import glob
import re
import time
from pathlib import Path
from threading import RLock
from datetime import datetime
import filecmp
import shutil
import numpy as np
import vtk
import random
import colorsys
import sys
from functools import partial
import copy

# Check if python packages are missing due to issue with some module imports
from utils.install_python_packages import *
check_and_install_python_packages()

from bids_validator import BIDSValidator
import nibabel as nib
import nrrd
import pandas as pd
import slicerio
import yaml

