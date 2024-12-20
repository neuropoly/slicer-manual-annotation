# To install a package in slicer python environment, use the following command:
# pip install --user package_name
import os
import logging
import slicer
import qt
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

import tempfile
import darkdetect
from qt import QApplication, QPalette
