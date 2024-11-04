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

# If issues are encountered related to the importation of modules below,
# requirements.py could be splitted in two files (e.g. requirements.py with
# above modules and requirements2.py with below modules), and the function
# install_python_packages() could be executed before importing the second
# requirements2.py file (that would reproduce the initial importation
# pseudo-code execution install_python_packages was called before below
# importing).
from bids_validator import BIDSValidator
import nibabel as nib
import nrrd
import pandas as pd
import slicerio
import yaml
