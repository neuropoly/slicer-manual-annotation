"""
 Module that optimizes workflow for manual segmentation in 3D Slicer.
 \file   SlicerManualAnnotation.py
 \authors   Maxime Bouthillier (MB)
            Delphine Pilon (DP)
            Laurent Letourneau-Guillon (LLG)
 \date   2024-06-12 (YYYY-MM-DD)
 Created on 2024-06-12
"""

# To install a package in slicer python environment, use the following command:
# pip install --user package_name
import os
from glob import glob
import re
import time
import yaml
from pathlib import Path
from threading import RLock

import qt, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
import slicerio  # cannot install in slicer
import SegmentStatistics

import pandas as pd
import numpy as np

import nrrd
import nibabel as nib

# MB - Additionnal libraries required for this module
import sys
import subprocess
import csv
import argparse
import copy
import vtk
from functools import partial
import random
import SimpleITK as sitk
import sitkUtils
from datetime import datetime
import math

# Adding all constants to the config file
CONFIG_FILE_PATH = os.path.join(Path(__file__).parent.resolve(), "config.yaml")

TIMER_MUTEX = RLock()


class SlicerManualAnnotation(ScriptedLoadableModule):
    """
    Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer
    /ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Slicer Manual Annotation" # Title of the module
        self.parent.categories = [
            "Examples"]  # Folder where the module is in the module selector
        self.parent.dependencies = []  # List of required module names
        self.parent.contributors = [
            "Delphine Pilon, "
            "An Ni Wu,"
            "Maxime Bouthillier, "
            "Emmanuel Montagnon, "
            "Laurent Letourneau-Guillon"]  # Based on
        # https://github.com/laurentletg/ICH_SEGMENTER_V2
        # TODO: update with short description of the module and a link to
        #  online module documentation
        self.parent.helpText = """
            This is an example of scripted loadable module bundled in an 
            extension.
            See more information in 
            <a href="https://github.com/organization/projectname
            "SlicerManualAnnotation">module documentation</a>.
            """
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = """
        Module supported by funding from : 
        1. RSNA Research & Education Foundation, through grant number RR2313. 
        The content is solely the responsibility of the authors and does not 
        necessarily represent the official views of the RSNA R&E Foundation.
        2. Neuro-Trauma Marie-Robert Foundation of Montréal Sacré-Coeur 
        Hospital.  
        3. Fonds de Recherche du Québec en Santé and Fondation de 
        l’Association des Radiologistes du Québec
        Radiology Research funding (299979) and Clinical Research 
        Scholarship–Junior 1 Salary Award (311203)
        4. Foundation of the Radiological Society of North America - Seed 
        Grant (RSD2122)
        5. Quebec Bio-Imaging Network, 2022 pilot project grant (Project no 
        21.24)
        6. Support professoral du Département de radiologie, radio-oncologie 
        et médecine nucléaire de l’Université de Montréal, Radiology 
        departement  Centre Hospitalier de l’Université de Montréal (CHUM) 
        and CHUM Research Center (CRCHUM) start-up funds
        Thanks to the Slicer community for the support and the development of 
        the software.
        """

class Timer():
    def __init__(self, number=None):
        with TIMER_MUTEX:
            self.number = number
            self.total_time = 0
            self.inter_time = 0
            # counting flag to allow to PAUSE the time
            self.flag = False  # False = not counting, True = counting (for
            # pause button)

    def start(self):
        with TIMER_MUTEX:
            if self.flag == False:
                # start counting flag (to allow to pause the time if False)
                self.flag = True
                self.start_time = time.time()

    def stop(self):
        with TIMER_MUTEX:
            if self.flag == True:
                self.inter_time = time.time() - self.start_time
                self.total_time += self.inter_time
                self.flag = False


class SlicerManualAnnotationWidget(ScriptedLoadableModuleWidget,
                              VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer
    /ScriptedLoadableModule.py
    """

    def __init__(self, parent=None):
        """
        Called when the user opens the module the first time and the widget is
        initialized.
        """

        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # Needed for parameter node obs
        self.logic = None
        self._parameterNode = None
        self._updatingGUIFromParameterNode = False

        # LLG CODE BELOW
        self.predictions_names = None

        # ----- ANW Addition  ----- : Initialize called var to False so the
        # timer only stops once
        self.called = False
        self.called_onLoadPrediction = False
        self.segmentation_node = None

        # MB CODE BELOW
        # Mouse customization initialization at startup
        # Some others customization features could be added
        # Get the slicer interactor and load the mouse customization class

        # Get the interactor from the 'Yellow' and 'Red' slice views
        self.interactor1 = slicer.app.layoutManager().sliceWidget(
            'Yellow').sliceView().interactor()
        self.interactor2 = slicer.app.layoutManager().sliceWidget(
            'Red').sliceView().interactor()

        # Apply the custom interactor style
        styleYellow = slicer.app.layoutManager().sliceWidget('Yellow')
        self.styleYellow = CustomInteractorStyle(sliceWidget=styleYellow)
        self.interactor1.SetInteractorStyle(self.styleYellow)

        styleRed = slicer.app.layoutManager().sliceWidget('Red')
        self.styleRed = CustomInteractorStyle(sliceWidget=styleRed)
        self.interactor2.SetInteractorStyle(self.styleRed)


    def get_config_values(self):
        with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as file:
            self.config_yaml = yaml.safe_load(file)
        print("DEBUG configuration values for LABELS.")
        for label in self.config_yaml["LABELS"]:
            print(20 * "-")
            print(label)
            print(20 * "-")

    def setup(self):
        """
        Called when the user opens the module the first time and the widget is
        initialized.
        """
        ### Segment editor widget
        self.layout.setContentsMargins(4, 0, 4, 0)

        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to
        # self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath('UI/SEGMENTER.ui'))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the
        # top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each
        # MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should
        # be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = SlicerManualAnnotationLogic()
        self.get_config_values()

        # MB CODE BELOW
        # Extract constant values from config file
        self.DEFAULT_VOLUME_DIR = self.config_yaml['default_volume_directory']
        self.DEFAULT_SEGMENTATION_DIR = self.config_yaml[
            'default_segmentation_directory']
        print(f'Default segmentation directory location:'
              f' {self.DEFAULT_SEGMENTATION_DIR}')

        self.OUTPUT_DIR = self.config_yaml['output_directory']
        self.GT_DIR = self.config_yaml['gt_references_directory']

        # EXTENSION_DIR corresponds to the directory of this extension
        # This is useful for executing a shell script
        self.EXTENSION_DIR = self.config_yaml['extension_directory']

        self.VOLUME_FILE_TYPE = self.config_yaml['volume_extension']
        self.SEGM_FILE_TYPE = self.config_yaml['segmentation_extension']
        self.VOL_REGEX_PATTERN = self.config_yaml['regex_format_volume_load']
        self.VOL_REGEX_PATTERN_PT_ID_INSTUID_SAVE = self.config_yaml[
            'regex_format_volume_save']

        # FOLDER_ORG corresponds to the organization of the dataset
        self.FOLDER_ORG = self.config_yaml['folder_organization']

        # MRI constants extraction
        # TODO: add a global variable view specification (e.g. axial, sagittal)
        self.CONTRAST = self.config_yaml['contrast']

        # CT-Scan constants extraction
        # Uncomment if loaded volumes are CT-Scans (HU threshold limitations)
        # self.OUTLIER_THRESHOLD_LB = self.config_yaml['OUTLIER_THRESHOLD'][
        # 'LOWER_BOUND']
        # self.OUTLIER_THRESHOLD_UB = self.config_yaml['OUTLIER_THRESHOLD'][
        # 'UPPER_BOUND']
        # self.LB_HU = self.config_yaml["LABELS"][0]["lower_bound_HU"]
        # self.UB_HU = self.config_yaml["LABELS"][0]["upper_bound_HU"]


        # Define usage variables
        # GUI case list variables
        self.files_seg_name_list = []
        self.files_seg_path_list = []

        # GUI case list navigation global variables initialization
        self.n_cases_dir = 0
        self.count_asess = 1
        self.index_files_seg = -1

        # Segmentation variables
        # Track if segmentation is modified
        self.segmentation_modified = False
        self.observer_tags = {}

        # Assess segmentation variables
        self.assessment_dict = {}
        self.new_cases_for_ref = self.config_yaml['new_cases_for_ref']

        # Display segmentation masks variables
        self.mask_loaded = False
        self.item_clicked = False
        self.segmentation_toggled = False
        self.interpolation_state = self.config_yaml["interpolation_state"]

        # Statistics variables
        self.csv_name = 'metadata.csv' # by default. Can be changed by user.

        # Define colors to be used in the application
        self.color_active = "green"
        self.color_inactive = "red"

        # Display the selected color view at module startup
        if self.config_yaml['slice_view_color'] == "Yellow":
            slicer.app.layoutManager().setLayout(
                slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpYellowSliceView)
        if self.config_yaml['slice_view_color'] == "Red":
            slicer.app.layoutManager().setLayout(
                slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpRedSliceView)
        self.file_extension = self.config_yaml['volume_extension']


        # Buttons initialization
        # PB for PushButton; TG for ToggleButton (used as); CB for ComboBox
        # At each startup, those buttons should be clicked to set current paths
        self.ui.PauseTimerButton.setText('Pause')
        self.ui.PBUInt8Casting.connect('clicked(bool)',
                                       self.converto_to_uint8casting)
        self.ui.PBGetDefaultDir.connect('clicked(bool)', self.get_default_dir)
        self.ui.PBBrowseVolDir.connect('clicked(bool)',
                                       self.browse_volume_dir)
        self.ui.PBSelectOutputDir.connect('clicked(bool)',
                                          self.select_output_dir)
        self.ui.PBSelectGTDir.connect('clicked(bool)',
                                      self.select_gt_dir)

        # Navigation buttons
        self.ui.PBPrevious.connect('clicked(bool)', self.go_previous_case)
        self.ui.PBNext.connect('clicked(bool)', self.go_next_case)

        # Safety/Update check buttons
        #TODO: configure and use those buttons (not done yet)
        self.ui.PBCheckSavedSeg.connect('clicked(bool)', self.save_statistics)
        self.ui.PBCheckErrorsLabels.connect('clicked(bool)',
                                            self.check_for_outlier_labels)

        # Workflow buttons
        self.ui.PBCreateSegmentation.connect('clicked(bool)',
                                             self.start_segmentation)
        self.ui.PBSegmentEditor.connect('clicked(bool)',
                                        self.open_segment_editor)
        self.ui.PBPaint.connect('clicked(bool)', self.activate_paint)
        self.ui.PBErase.connect('clicked(bool)', self.activate_erase)
        self.ui.PBAssessSegmentation.connect('clicked(bool)',
                                             self.assess_segmentation)
        self.ui.PBGetResultsSegmentation.connect('clicked(bool)',
                                                 self.get_results)

        self.ui.TGSegmentationVersions.connect('clicked(bool)',
                                               self.toggle_segmentation_versions)
        self.ui.TGInterpolation.connect('clicked(bool)',
                                        self.toggle_interpolation_state)

        self.ui.SlicerDirectoryListView.clicked.connect(
            self.get_current_table_item)

        self.ui.PBLoadMask.connect('clicked(bool)', self.load_masks)
        self.ui.PBLoadMask.setStyleSheet("background-color: red")
        self.ui.PBSaveSegmentation.connect('clicked(bool)',
                                           self.save_segmentation)

        # Other buttons
        self.ui.TGToggleVisibility.connect('clicked(bool)',
                                           self.toggle_visibility)
        self.ui.CBDropdownLabelSelect.currentIndexChanged.connect(
            self.on_dropdown_label_select_button)
        self.ui.TGToggleFill.connect('clicked(bool)',
                                     self.toggle_fill)
        self.ui.PBSegmentWindow.connect('clicked(bool)',
                                        self.push_segment_editor)
        self.ui.PBUndo.connect('clicked(bool)', self.push_undo_segmentation)
        self.ui.StartTimerButton.connect('clicked(bool)',
                                         self.toggle_start_timer)
        self.ui.PauseTimerButton.connect('clicked(bool)',
                                         self.toggle_pause_timer)

        # Uncomment if scans and needs to consider HU min and max values
        # self.ui.UB_HU.valueChanged.connect(self.onUB_HU)
        # self.ui.LB_HU.valueChanged.connect(self.onLB_HU)
        # self.ui.pushDefaultMin.connect('clicked(bool)', self.onPushDefaultMin)
        # self.ui.pushDefaultMax.connect('clicked(bool)', self.onPushDefaultMax)


        # Keyboard shortcuts settings
        keyboard_shortcuts = []
        for i in self.config_yaml["KEYBOARD_SHORTCUTS"]:
            shortcutKey = i.get("shortcut")
            callback_name = i.get("method")
            callback = getattr(self, callback_name)
            keyboard_shortcuts.append((shortcutKey, callback))

        print(f'keyboard_shortcuts: {keyboard_shortcuts}')

        for (shortcutKey, callback) in keyboard_shortcuts:
            shortcut = qt.QShortcut(slicer.util.mainWindow())
            shortcut.setKey(qt.QKeySequence(shortcutKey))
            shortcut.connect("activated()", callback)

        # Labels verification settings
        for label in self.config_yaml["LABELS"]:
            print("self config yaml LABELS", self.config_yaml["LABELS"])
            print("LABELS", label)
            self.ui.CBDropdownLabelSelect.addItem(label["name"])
            print("in set up label[name]", label["name"])

        # MB Not modified from initial module
        self.ui.pushButton_SemiAutomaticPHE_ShowResult.setEnabled(False)
        self.disablePauseTimerButton()
        self.disableSegmentAndPaintButtons()
        self.enableStartTimerButton()
        self.ui.ThresholdLabel.setStyleSheet("font-weight: bold")
        self.ui.SemiAutomaticPHELabel.setStyleSheet("font-weight: bold")
        self.ui.UB_HU.setMinimum(-32000)
        self.ui.LB_HU.setMinimum(-32000)
        self.ui.UB_HU.setMaximum(29000)
        self.ui.LB_HU.setMaximum(29000)
        self.ui.TGToggleFill.setStyleSheet(
            "background-color : indianred")
        self.ui.PBSegmentWindow.setStyleSheet(
            "background-color : lightgray")
        self.ui.TGToggleVisibility.setStyleSheet(
            "background-color : lightgreen")
        self.ui.lcdNumber.setStyleSheet("background-color : black")

        # # # Change the value of the upper and lower bound of the HU
        # # self.ui.UB_HU.setValue(self.UB_HU)
        # # self.ui.LB_HU.setValue(self.LB_HU)

        # ### ANW ICH TYPE/LOCATION CONNECTIONS
        self.listichtype = [self.ui.ichtype1, self.ui.ichtype2,
                            self.ui.ichtype3, self.ui.ichtype4,
                            self.ui.ichtype5,
                            self.ui.ichtype6, self.ui.ichtype7,
                            self.ui.ichtype8, self.ui.ichtype9]
        self.listichloc = [self.ui.ichloc1, self.ui.ichloc2, self.ui.ichloc3,
                           self.ui.ichloc4, self.ui.ichloc5,
                           self.ui.ichloc6, self.ui.ichloc7, self.ui.ichloc8,
                           self.ui.ichloc9, self.ui.ichloc10]

        self.listEMs = [self.ui.EM_barras_density, self.ui.EM_barras_margins,
                        self.ui.EM_black_hole, self.ui.EM_blend,
                        self.ui.EM_fl_level, self.ui.EM_hypodensity,
                        self.ui.EM_island, self.ui.EM_satellite,
                        self.ui.EM_swirl]

        self.flag_ICH_in_labels = False
        self.flag_PHE_in_labels = False
        for label in self.config_yaml["LABELS"]:
            if "ICH" in label["name"].upper() or "HEMORRHAGE" in label[
                "name"].upper() or "HÉMORRAGIE" in label[
                "name"].upper() or "HEMORRAGIE" in label[
                "name"].upper() or "HAEMORRHAGE" in label["name"].upper():
                self.flag_ICH_in_labels = True
            if "PHE" in label["name"].upper() or "EDEMA" in label[
                "name"].upper() or "OEDEME" in label[
                "name"].upper() or "OEDÈME" in label["name"].upper():
                self.flag_PHE_in_labels = True

        # Initialize timers
        self.timers = []
        timer_index = 0
        for label in self.config_yaml["LABELS"]:
            self.timers.append(Timer(number=timer_index))
            timer_index = timer_index + 1

        self.MostRecentPausedCasePath = ""

        if not self.flag_ICH_in_labels:
            self.ui.MRMLCollapsibleButton.setVisible(False)
        if not self.flag_PHE_in_labels:
            self.ui.SemiAutomaticPHELabel.setVisible(False)
            self.ui.pushButton_SemiAutomaticPHE_Launch.setVisible(False)
            self.ui.pushButton_SemiAutomaticPHE_ShowResult.setVisible(False)

    # MB Commented from original module (uncomment if scans)
    # def setUpperAndLowerBoundHU(self, inputLB_HU, inputUB_HU):
    #     self.LB_HU = inputLB_HU
    #     self.UB_HU = inputUB_HU
    #     self.ui.UB_HU.setValue(self.UB_HU)
    #     self.ui.LB_HU.setValue(self.LB_HU)

    # MB CODE ADDED
    # Generic useful functions for developers
    def enter_function(self, function_name):
        # To remove entering function prints, just comment out the next line
        print(f"\n ENTERING {function_name}() \n")
        pass

    def print_dictionary(self, dictionary, name=None):
        if name is None:
            name = "dictionary"
        for element in dictionary:
            print(f"{name} {element}: ", dictionary[element])

    def show_message_box(self, message,
                         box_title=None,
                         buttons=False):
        self.enter_function("show_message_box")
        # Create a message box
        messageBox = qt.QMessageBox()

        # Set the message box title
        if box_title is None:
            messageBox.setWindowTitle("Message Box")
        else:
            messageBox.setWindowTitle(box_title)

        # Set the message box text
        messageBox.setText(message)

        if buttons:
            # Add Yes and No buttons
            messageBox.addButton(qt.QMessageBox.Yes)
            messageBox.addButton(qt.QMessageBox.No)

        # Display the message box as modal
        return messageBox.exec_()

    def set_button_color(self, button, color):
        button.setStyleSheet(f"background-color: {color}")

    def enableSegmentAndPaintButtons(self):
        self.enter_function("enableSegmentAndPaintButtons")
        self.ui.PBPaint.setEnabled(True)
        self.ui.PBErase.setEnabled(True)
        self.ui.pushButton_SemiAutomaticPHE_Launch.setEnabled(True)

    def disableSegmentAndPaintButtons(self):
        self.enter_function("disableSegmentAndPaintButtons")
        self.ui.PBPaint.setEnabled(False)
        self.ui.pushButton_SemiAutomaticPHE_Launch.setEnabled(False)
        self.ui.pushButton_SemiAutomaticPHE_ShowResult.setEnabled(False)
        self.ui.PBErase.setEnabled(False)

    # Getters section
    def get_default_dir(self):
        self.enter_function("get_default_dir")
        self.DEFAULT_VOLUME_DIR = qt.QFileDialog.getExistingDirectory(
            None, "Open default directory", self.DEFAULT_VOLUME_DIR,
            qt.QFileDialog.ShowDirsOnly)

    # MB Get nodes easily with functions
    def get_volume_node(self):
        # In this project, note that we can also get the first node with the
        # following: slicer.util.getNodesByClass('vtkMRMLScalarVolumeNode')[0]
        return slicer.mrmlScene.GetFirstNodeByClass(
                "vtkMRMLScalarVolumeNode")
    def get_segmentation_node(self):
        # In this project, note that we can also get the first node with the
        # following: slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
        return slicer.mrmlScene.GetFirstNodeByClass(
            'vtkMRMLSegmentationNode')

    def get_label_map_display_node(self):
        return slicer.mrmlScene.GetFirstNodeByClass(
            'vtkMRMLLabelMapVolumeDisplayNode')

    def get_storage_node(self):
        return slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLStorageNode')

    def get_transform_node(self):
        return slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLTransformNode')

    def get_active_segments(self, segmentation_node):
        return segmentation_node.GetSegmentation()

    def get_number_of_segments(self, segments):
        return segments.GetNumberOfSegments()

    def get_existing_segment(self):
        self.enter_function("get_existing_segment")
        filename = self.remove_file_extension(self.segment_name)
        print("get_existing_segment(), filename: ", filename)
        version = self.get_latest_version(filename)
        print("get_existing_segment(), version: ", version)
        if version == 0:
            print("version==0")
            return False
        return True

    def get_path_from_name(self, current_case):
        self.enter_function("get_path_from_name")
        print("current_case: ", self.current_case)
        for element in self.all_cases_path:
            if current_case in element:
                print("case path: ", element)
                return element

    # Return an integer
    def get_latest_version(self, filename, folder_path=None):
        self.enter_function("get_latest_version")
        print("get_latest_version(), filename: ", filename)
        print("get_latest_version(), folder_path: ", folder_path)

        version = 0
        list_version = self.get_list_of_versions(filename, folder_path)

        if list_version == []:
            return version
        else:
            max_version = max(list_version)
            # To prevent exceeding 99 versions.
            max_version = min(max_version, 98)
            print("get_latest_version(), max version: ", max_version)
            return max_version

    def get_segment_names_list(self, segments):
        segment_names = []
        for i in range(self.get_number_of_segments(segments)):
            segment = segments.GetNthSegment(i)
            segment_name = segment.GetName()
            segment_names.append(segment.GetName())
        return segment_names

    def get_all_labels_list(self):
        self.enter_function("get_all_labels_list")
        list_of_labels = []
        for i in range(len(self.config_yaml["LABELS"])):
            print(self.config_yaml["LABELS"][i]["name"])
            list_of_labels.append(self.config_yaml["LABELS"][i]["name"])
        return list_of_labels

    # Get list_of_versions ('list' put here at the beginning for convenience)
    def get_list_of_versions(self, filename, folder_path=None):
        self.enter_function("get_list_of_versions")
        list_version = []
        # If folder_path argument is not passed, it selects by default the
        # files in the version directory
        if folder_path is None:
            folder_path = f'{self.output_folder}{os.sep}versions'
        print("folder_path: ", folder_path)
        if self.check_if_folder_exists(folder_path):
            elements = os.listdir(folder_path)
            for element in elements:
                element = element[
                          :-len(self.config_yaml["volume_extension"])]
                if filename in element:
                    list_version.append(int(element[-2:]))
        return list_version

    def get_all_files_versions(self, max_version=None):
        self.enter_function("get_all_files_versions")
        versions_folder = os.path.join(self.output_folder, 'versions')
        # Adjust pattern to match files
        pattern = os.path.join(versions_folder, '*')
        all_files = glob(pattern)
        print("get_all_files_versions(), all_files length: ", len(all_files))
        print("get_all_files_versions(), max_version: ", max_version)
        list_of_labels = self.get_all_labels_list()

        # Sort the all files list so that the list returned has the element in
        # the same order as compared to the label list (order) from the config
        # file
        all_files_label_sorted = []
        for label in list_of_labels:
            for version in range(max_version):
                for element in all_files:
                    if ((label in element)
                            and (f"_v{(version + 1):02d}" in element)):
                        all_files_label_sorted.append(element)

        # Create a sorted dictionary with formatted versions as key and each
        # file that has the corresponding version in value (a list)
        versions_dict = {}
        for i in range(max_version):
            list_of_files = []
            for element in all_files_label_sorted:
                if f"_v{(i + 1):02d}" in element:
                    print("all file[i] found", all_files_label_sorted[i])
                    list_of_files.append(element)
                    versions_dict[f"_v{(i + 1):02d}"] = list_of_files

        return versions_dict

    def get_version_string(self, version):
        """
        Argument version is an integer to be converted in a string _vXX
        """
        return f"_v{version:02d}"

    def get_index_difference(self):
        self.enter_function("get_index_difference")
        len_cases_dir = self.n_cases_dir
        print("len_cases_dir: ", len_cases_dir)
        len_files_seg_list = len(self.files_seg_name_list)
        print("len_files_seg_list: ", len_files_seg_list)
        difference = int(len_cases_dir - len_files_seg_list)
        print("difference: ", difference)
        return difference

    def get_current_table_item(self):
        self.enter_function("get_current_table_item")
        # ----- ANW Addition ----- : Reset timer when change case and uncheck
        # all checkboxes
        self.resetTimer()
        # self.uncheckAllBoxes()
        self.clearTexts()

        # All below is dependent on self.current_case_index updates
        if self.check_different_list():
            self.current_case_index = self.ui.SlicerDirectoryListView.currentRow
            # If gap between UI case list and slice viewer, consider next lines
            # self.index_files_seg = self.ui.SlicerDirectoryListView.currentRow
            # print("self ui slicerdirectory lsit view self index yaml,",
            #       self.index_files_seg)
            self.index_files_seg = -1
            self.update_UI_from_other_case_list()
        else:
            self.update_case_index(
                self.ui.SlicerDirectoryListView.currentRow)  # Index starts at 0
            # Update the case index
            self.current_case_index = self.ui.SlicerDirectoryListView.currentRow
            self.current_case = self.cases[self.current_case_index]
            self.current_case_path = self.cases_path[self.current_case_index]

        self.update_current_patient()
        self.load_patient()

        # ----- ANW Addition ----- : Reset timer when change case, also reset
        # button status
        self.resetTimer()

    # Setters section
    def set_files_seg_values(self):
        self.enter_function("set_files_seg_values")
        print("Index yaml succeed: ", self.index_files_seg)
        self.current_case = self.files_seg_name_list[self.index_files_seg]
        print("current_case succeed: ", self.current_case)
        self.current_case_path = self.files_seg_path_list[self.index_files_seg]
        print("current_case_path  succeed: ", self.current_case_path)
        self.current_case_index = self.all_cases.index(self.files_seg_name)
        print("current_case_index: ", self.current_case_index)

    def set_all_cases_values(self):
        self.enter_function("set_all_cases_values")
        self.current_case = self.all_cases[self.current_case_index]
        self.current_case_path = self.all_cases_path[self.current_case_index]

    def set_cases_values(self):
        self.enter_function("set_cases_values")
        self.current_case = self.cases[self.current_case_index]
        self.current_case_path = self.cases_path[self.current_case_index]

    def set_appropriate_index(self):
        self.enter_function("set_appropriate_index")
        if self.check_different_list():
            print(" self check different list in set approiate index")
            pass

    def set_segment_name(self, label_name):
        self.enter_function("set_segment_name")
        current_case_name = self.remove_file_extension(self.current_case)
        volume_extension = self.config_yaml["volume_extension"]
        segment_name =  (f"{current_case_name}_"
                         f"{label_name}"
                         f"{volume_extension}")
        print(" set_segment_name(), segment_name: ", segment_name)
        return segment_name

    def set_one_label_color(self, segment,
                            label_color_r,
                            label_color_g,
                            label_color_b):
        self.enter_function("set_one_label_color")

        segment.SetColor(label_color_r / 255,
                         label_color_g / 255,
                         label_color_b / 255)

    def set_all_labels_colors(self, segmentation_node,
                              assess_segmentation_flag=False):
        self.enter_function("set_all_labels_colors")
        segmentation_node.UndoEnabledOn()
        segmentation = segmentation_node.GetSegmentation()
        for label in self.config_yaml["LABELS"]:
            label_name = label["name"]
            print("label_name: ", label_name)
            print("label color_r: ", label["color_r"])
            print("label color_g: ", label["color_g"])
            print("label color_b: ", label["color_b"])

            if assess_segmentation_flag:
                # -12 to remove the extension Segmentation (keeping the _)
                segment_name = (
                    f"{segmentation_node.GetName()[:-12]}{label_name}"
                    f"{self.file_extension}")
            else:
                segment_name = self.new_segment(label_name)

            segment_id = segmentation.GetSegmentIdBySegmentName(segment_name)
            # segment = segmentation.GetSegment(segment_name) maybe to try if
            # not working
            segment = segmentation.GetSegment(segment_id)

            self.set_one_label_color(segment,
                                     label["color_r"],
                                     label["color_g"],
                                     label["color_b"])

    # TODO: Set a color to the segments of a specific corresponding version,
    def set_color_to_specific_version(self):
        pass

    # Check functions
    def check_if_folder_exists(self, folder_path):
        self.enter_function("check_if_folder_exists")
        # Check if a folder path exists and return True/False
        if os.path.exists(folder_path):
            print("Folder exists: ", folder_path)
            return True
        else:
            print("Folder does not exist: ", folder_path)
            return False

    def check_if_file_version_exists(self, filename, folder_path):
        self.enter_function("check_if_file_version_exists")
        print("filename: ", filename)
        # Check the version for a specific filename and returns a string.
        folder_version = self.check_if_folder_exists(folder_path)
        version = "_v01"
        if folder_version:
            version = self.get_latest_version(filename)
        return version

    # Useful general functions for handling file, versions and LABELS
    def remove_file_extension(self, file_path):
        self.enter_function("remove_file_extension")
        filename = file_path.split('.')[0]
        print("filename: ", filename)
        return filename

    def remove_version_extension(self, filename):
        self.enter_function("remove_version_extension")
        # Version format is always _vXX
        filename = filename[:-4]
        return filename

    def remove_label_extension(self, filename, list_of_labels):
        self.enter_function("remove_label_extension")
        for i in range(len(list_of_labels)):
            if list_of_labels[i] in filename:
                return filename.replace(list_of_labels[i], "")

    def format_latest_version(self, filename):
        self.enter_function("format_latest_version")
        latest_version = self.get_latest_version(filename)
        return f"_v{latest_version:02d}"

    def increment_latest_version(self, filename):
        self.enter_function("increment_latest_version")
        latest_version = self.get_latest_version(filename)
        return f"_v{(latest_version + 1):02d}"

    # MB CODE BELOW
    # Define a callback function for the observers
    def observe_segmentation_node(self):
        self.enter_function("observe_segmentation_node")
        segmentation_node = self.get_segmentation_node()

        def segment_modified_callback(segment, event, segmentation_node):
            # MB If event and segmentation_node are removed, an error appears
            self.enter_function("segment_modified_callback")
            print("Segment modified:", segment.GetName())
            self.segmentation_modified = True
            print("self.segmentation_modified", self.segmentation_modified)
            # Timer begin when one or more segment has been modified
            self.time_begin = datetime.now()

        if segmentation_node:
            # Get the active segment
            segments = self.get_active_segments(segmentation_node)
            # Get number of segments
            num_segments = self.get_number_of_segments(segments)
            # Iterate through segments and collect names
            segment_names = self.get_segment_names_list(segments)

            # Add observer to the segment
            for i in range(num_segments):
                segment = segments.GetNthSegment(i)
                observer_tag = segment.AddObserver(
                    vtk.vtkCommand.ModifiedEvent,
                    partial(segment_modified_callback, segment))
                self.observer_tags[segment_names[i]] = observer_tag

        print("Observers setted: ", self.segmentation_modified)

    def cleanup_observers(self):
        self.enter_function("cleanup_observers")
        # Remove observers
        for observer_tag in self.observer_tags.values():
            slicer.mrmlScene.RemoveObserver(observer_tag)
        self.observer_tags = {}

    def converto_to_uint8casting(self):
        """
        Check for dtype in nrrd or nifti files and cast to uint8 if not already
        this causes issues in Slicer 5.6 (vector error). Segmentation file
        should anyway be uint8, not float.
        """
        self.enter_function("converto_to_uint8casting")
        # Message box to confirm overwriting
        reply = self.show_message_box(
            'Message',
            'Casiting to uint8. Do you want to overwrite the original '
            'segmentation files?', True)
        if reply == qt.QMessageBox.No:
            raise ValueError('The segmentation files were not overwritten.')
        else:
            self.cast_segmentation_to_uint8()

    def cast_segmentation_to_uint8(self):
        self.enter_function("cast_segmentation_to_uint8")
        for case in self.cases_path:
            # Load the segmentation
            input_path = os.path.basename(case)
            if input_path.endswith('.nii') or input_path.endswith('.nii.gz'):
                segm = nib.load(case)
                segm_data = segm.get_fdata()
                print(f'infile: {input_path}, dtype: {segm_data.dtype}')
                if segm_data.dtype != np.uint8:
                    segm_data = segm_data.astype(np.uint8)
                    segm_nii = nib.Nifti1Image(segm_data, segm.affine)
                    nib.save(segm_nii, case)
                    print(f'converted file {input_path} to uint8')
            elif input_path.endswith('.nrrd'):
                segm_data, header = nrrd.read(case)
                print(f'infile: {input_path}, dtype: {segm_data.dtype}')
                if segm_data.dtype != np.uint8:
                    segm_data = segm_data.astype(np.uint8)
                    header['type'] = 'unsigned char'
                    nrrd.write(case, segm_data, header=header)
                    print(f'converted file {input_path} to uint8')
            else:
                raise ValueError(
                    'The input segmentation file must be in nii, nii.gz or '
                    'nrrd format.')

    def browse_volume_dir(self):
        self.enter_function("browse_volume_dir")
        # LLG get dialog window to ask for directory
        self.current_dir = qt.QFileDialog.getExistingDirectory(
            None,"Open a folder", self.DEFAULT_VOLUME_DIR,
            qt.QFileDialog.ShowDirsOnly)
        self.update_current_dir()

        # The lines below work well for the BRATS dataset
        # self.cases_path = sorted(glob(f'{self.current_dir}{os.sep}{
        # self.FOLDER_ORG}*{os.sep}*{self.CONTRAST}{self.VOLUME_FILE_TYPE}'))

        # The lines below work well for BIDS dataset
        self.cases_path = sorted(glob(
            f'{self.current_dir}{os.sep}{self.FOLDER_ORG}*{os.sep}anat'
            f'{os.sep}*{self.CONTRAST}{self.VOLUME_FILE_TYPE}'))
        self.n_cases_dir = len(self.cases_path)

        # MB Added to facilitate loading of any case list (helps navigation)
        self.all_cases_path = sorted(glob(
            f'{self.current_dir}{os.sep}{self.FOLDER_ORG}*{os.sep}anat'
            f'{os.sep}*{self.CONTRAST}{self.VOLUME_FILE_TYPE}'))
        self.all_cases = []
        for i in range(len(self.all_cases_path)):
            self.all_cases.append(os.path.split(self.all_cases_path[i])[1])

        # print("self.all_cases_path", self.all_cases_path)
        # print("self.all_cases", self.all_cases)
        print("current_dir: ", self.current_dir)
        print("VOLUME_FILE_TYPE: ", self.VOLUME_FILE_TYPE)
        print("REGEX_PATTERN: ", self.VOL_REGEX_PATTERN)
        print("FOLDER_ORG: ", self.FOLDER_ORG)
        print()

        self.cases = []
        for i in range(len(self.cases_path)):
            self.cases.append(os.path.split(self.cases_path[i])[1])

        # print("self.cases", self.cases)

        self.update_UI_case_list()

    # Checks if the volume directory list is different than the list in the
    # output folder (if output folder has been selected). Here for convenience
    def check_different_list(self):
        self.enter_function("check_different_list")
        if (self.files_seg_path_list != []) and (self.files_seg_name_list != []):
            self.cases_path = self.files_seg_path_list
            self.cases = self.files_seg_name_list
            return True
        return False

    def update_UI_case_list(self):
        self.enter_function("update_UI_case_list")
        self.ui.SlicerDirectoryListView.clear()
        # Populate the SlicerDirectoryListView
        if self.check_different_list():
            self.update_UI_from_other_case_list()
        else:
            self.ui.SlicerDirectoryListView.addItems(self.all_cases)
            self.current_case_index = 0  # THIS IS THE CENTRAL THING THAT
            # HELPS FOR CASE NAVIGATION
        self.update_cases()
        self.load_patient()

    def update_UI_from_other_case_list(self):
        self.enter_function("update_UI_from_other_case_list")
        self.ui.SlicerDirectoryListView.clear()
        self.ui.SlicerDirectoryListView.addItems(self.all_cases)

        # Get the case name according to the .yaml file for navigation
        if self.index_files_seg != -1 and (self.files_seg_name_list != []):
            self.set_files_seg_values()
        else:
            print("index from .yaml file for navigation not found (else)")
            self.set_all_cases_values()

    def update_cases(self):
        self.enter_function("update_cases")
        # All below is dependent on self.current_case_index updates,
        if self.check_different_list():
            self.update_UI_from_other_case_list()
        else:
            self.set_cases_values()

        self.update_current_patient()

        # Highlight the current case in the list view (when pressing on next o)
        self.ui.SlicerDirectoryListView.setCurrentItem(
            self.ui.SlicerDirectoryListView.item(self.current_case_index))

    def update_case_index(self, index):
        self.enter_function("update_case_index")
        # ----- ANW Modification ----- : Numerator on UI should start at 1
        # instead of 0 for coherence
        self.ui.FileIndex.setText('{} / {}'.format(index + 1, len(self.cases)))

    def update_current_dir(self):
        self.enter_function("update_current_dir")
        self.ui.CurrentDir.setText(
            'Current folder : \n...{}'.format(self.current_dir[-80:]))

    def update_current_patient(self):
        self.enter_function("update_current_patient")
        self.ui.CurrentPatient.setText(f'Current case: {self.current_case}')
        print("self.current_case_index", self.current_case_index)
        self.update_case_index(self.current_case_index)

    def update_current_segmentation_label(self):
        self.enter_function("update_current_segmentation_label")
        self.ui.CurrentSegmenationLabel.setText(
            'Current segment: {}'.format(self.segment_name))

    # Load a patient in the display viewer
    def load_patient(self):
        self.enter_function("load_patient")
        timer_index = 0
        self.timers = []
        for label in self.config_yaml["LABELS"]:
            self.timers.append(Timer(number=timer_index))
            timer_index = timer_index + 1
        # Reset dropbox to index 0
        # MB modified: initially was to 0
        # self.ui.dropDownButton_label_select.setCurrentIndex(0)
        self.ui.CBDropdownLabelSelect.setCurrentIndex(
            self.current_case_index)

        # Timer reset if we come back to same case
        self.called = False

        slicer.mrmlScene.Clear()
        slicer.util.loadVolume(self.current_case_path)
        self.volume_node = self.get_volume_node()
        self.update_cases()
        self.ui.CurrentSegmenationLabel.setText(
            'New patient loaded - No segmentation created!')

        # Adjust windowing (no need to use self. since this is used locally)
        volume_node_displayed = self.volume_node.GetDisplayNode()
        volume_node_displayed.AutoWindowLevelOff()

        # Deactivate the interpolation_state
        if not self.interpolation_state:
            print("interpolation_state setted to true")
            self.volume_node.GetDisplayNode().SetInterpolate(0)
            self.ui.TGInterpolation.setStyleSheet("background-color : red")

        # MB Uncomment if CT-Scans for Automated Window Width setting
        # volume_node_displayed.SetWindow(85)
        # volume_node_displayed.SetLevel(45)

        self.create_new_segmentation()
        self.subjectHierarchy()
        self.clean_hierarchy_folder()

    # Create a segmentation node (a segmentation node can include multiple
    # segments).
    def create_new_segmentation(self):
        self.enter_function("create_new_segmentation")
        # Create segment editor widget and node
        self.segmentEditorWidget = (
            slicer.modules.segmenteditor.widgetRepresentation().self().editor)
        self.segmentEditorNode = (
            self.segmentEditorWidget.mrmlSegmentEditorNode())

        # Create segmentation node (keep it local since we add a new
        # segmentation node)
        # Not for reference in other methods
        segmentation_node = slicer.mrmlScene.AddNewNodeByClass(
            "vtkMRMLSegmentationNode")

        # Set segmentation node name
        segmentation_node.SetName(self.segmentation_node_name)
        # Set segmentation node to segment editor
        self.segmentEditorWidget.setSegmentationNode(segmentation_node)
        # Set master volume node to segment editor
        self.segmentEditorWidget.setSourceVolumeNode(self.volume_node)

        # Set reference geometry to Volume node (important for the
        # segmentation to be in the same space as the volume)
        segmentation_node.SetReferenceImageGeometryParameterFromVolumeNode(
            self.volume_node)
        self.create_new_segments()

        # Restart the current timer
        self.timers[self.current_label_index] = Timer(
            number=self.current_label_index)
        # Reset tool
        self.segmentEditorWidget.setActiveEffectByName("No editing")


    # This function creates segments for each label in the config file,
    # set color to each label and select the first label in the label
    # select menu of the segment editor.
    def create_new_segments(self):
        self.enter_function("create_new_segments")
        segmentation_node = self.get_segmentation_node()
        print("segmentation_node: ", segmentation_node)

        # Set color LABELS for each segment in a segmentation node
        self.set_all_labels_colors(segmentation_node)

        first_label_name = self.config_yaml["LABELS"][0]["name"]
        self.first_label_segment_name = self.set_segment_name(first_label_name)

        """
        ATTENTION! NEVER COMMENT THIS LINE BELOW SINCE IT WILL CAUSE
        TROUBLESHOOTING AND WILL NEED FURTHER CORRECTIONS (PAINTING AND 
        SEGMENTATION)
        """
        # Select the first label in the segment editor
        self.select_label_push_button(self.first_label_segment_name)

    def new_segment(self, label_name):
        self.enter_function("new_segment")
        print("self.segmentation_modified: ", self.segmentation_modified)
        print("label_name: ", label_name)

        # MB Clean and reset segmentation modification flag
        self.cleanup_observers()
        self.segmentation_modified = False

        # Define a global variable associated with the segmentation node
        # TODO: make the segmentation_node variable local and adjust other
        # functions accordingly.
        # If troubleshooting, you might want to insert self.segmentation_node
        # in if self.mask_loaded and in else self.get_existing_segment and/or
        # else self.mask_loaded).
        self.segmentation_node = self.get_segmentation_node()

        # Define a global variable associated with the segment name
        # TODO: make the segment_name variable local and adjust other
        # functions accordingly.
        self.segment_name = self.set_segment_name(label_name)

        # MB Below will create a new segment if there are no segments in the
        # segmentation node, avoid overwriting existing segments
        print("new_segment(). Before checking if self.mask_loaded: ",
              self.mask_loaded)

        if self.mask_loaded:
            print("new_segment(). self.mask_loaded was true.")

            if self.get_existing_segment():
                print("New segment to be added.")
                # Add the segment to the segmentation node
                self.create_vtk_segment()

                # Update the segmentation node
                self.segmentation_node.Modified()
                print("A new non-empty or empty segment has been added.")

            else:
                print("Create an only empty segment.")
                self.segmentation_node.GetSegmentation().AddEmptySegment(
                    self.segment_name)

        else:
            print(" new_segment() else. self.mask_loaded was false.")
            self.segmentation_node.GetSegmentation().AddEmptySegment(
                self.segment_name)

        print("new_segment(). if self.mask_loaded. "
              "self.segmentation_modified: ", self.segmentation_modified)


        # Make the new segment active for editing
        # Set the segmentation node and volume to the Segment Editor widget
        self.segmentEditorWidget.setSegmentationNode(self.segmentation_node)
        self.segmentEditorWidget.setCurrentSegmentID(self.segmentation_node)

        return self.segment_name

    # TODO: refractor the name according to its actual use,
    #  since subjectHierarchy is a function and should start with an action verb
    def subjectHierarchy(self):
        self.enter_function("subjectHierarchy")

        # Get the subject hierarchy node
        subject_hierarchy_node = slicer.mrmlScene.GetSubjectHierarchyNode()
        # Get scene item ID first because it is the root item:
        scene_item_id = subject_hierarchy_node.GetSceneItemID()
        # Get the scene item ID (check if the scene item exists)
        subject_item_id = subject_hierarchy_node.GetItemChildWithName(
            subject_hierarchy_node.GetSceneItemID(), self.current_case)

        if not subject_item_id:
            subject_item_id = subject_hierarchy_node.CreateSubjectItem(
                subject_hierarchy_node.GetSceneItemID(), self.current_case)

        print("subjectHierarchy(). subject_item_id: ", subject_item_id)

        # TODO: this will need to be updated when moving to multiple studies
        #  per patient (or done in a separate script)
        # Creat a folder to include a study (if more than one study)
        # check if the folder exists and if not create it (avoid recreating a
        # new one when reloading a mask)
        study_name = 'Study to be updated'
        folder_id = subject_hierarchy_node.GetItemChildWithName(subject_item_id,
                                                                study_name)
        print("subjectHierarchy(). folder_id: ", folder_id)
        if not folder_id:
            folder_id = subject_hierarchy_node.CreateFolderItem(subject_item_id,
                                                                study_name)
        # Set under the subject
        subject_hierarchy_node.SetItemParent(folder_id, subject_item_id)

        # Get all volume nodes
        volumes_nodes = slicer.util.getNodesByClass('vtkMRMLVolumeNode')
        volumes_nodes_names = [i.GetName() for i in volumes_nodes]

        # Get all child (item_id = CT or MR series/sequences)
        for i in volumes_nodes_names:
            item_id = subject_hierarchy_node.GetItemChildWithName(
                scene_item_id, i)
            subject_hierarchy_node.SetItemParent(item_id, folder_id)


        # Get all child for segmentation nodes
        segmentation_nodes = slicer.util.getNodesByClass(
            'vtkMRMLSegmentationNode')
        self.segmentEditorWidget.setCurrentSegmentID(segmentation_nodes[0])
        # TODO: improve the function so the folder of studies to be updated
        #  can be useful
        # segmentation_nodes_names = [i.GetName() for i in segmentation_nodes]

    def clean_hierarchy_folder(self):
        self.enter_function("clean_hierarchy_folder")
        # Get the subject hierarchy node
        subject_hierarchy_node = slicer.mrmlScene.GetSubjectHierarchyNode()

        # Get the folder item by name (replace 'NameOfFolder' with the actual
        # folder name)
        folder_item_id = subject_hierarchy_node.GetItemByName(
            'Study to be updated')

        # Check if the folder item was found
        if folder_item_id:
            # Get all child items (nodes) in the folder
            child_items_ids = vtk.vtkIdList()
            subject_hierarchy_node.GetItemChildren(folder_item_id,
                                                   child_items_ids)

            # Iterate over each child item and remove the corresponding node
            for i in range(child_items_ids.GetNumberOfIds()):
                child_item_id = child_items_ids.GetId(i)
                node = subject_hierarchy_node.GetItemDataNode(child_item_id)
                # Check if the node is a labelmap volume node
                if node and node.IsA('vtkMRMLLabelMapVolumeNode'):
                    # Remove the labelmap volume node
                    slicer.mrmlScene.RemoveNode(node)
        else:
            print("clean_hierarchy_folder(). Folder not found.")

    # MB CODE BELOW
    def select_output_dir(self):
        self.enter_function("select_output_dir")
        self.output_folder = qt.QFileDialog.getExistingDirectory(
            None,"Open a folder", self.OUTPUT_DIR)

        # Define the remaining cases filepath
        remaining_cases_path = (f'{self.output_folder}'
                                f'{os.sep}remainingCases.yaml')
        # Create a copy of all cases
        all_cases_filepath = f'{self.output_folder}{os.sep}allCases.yaml'
        all_cases_data = {
            'FILES_SEG': self.all_cases
        }

        # If no file all_cases, create a yaml file that list all cases (will
        # not be modified after)
        if not os.path.exists(all_cases_filepath):
            print(f"***The path '{all_cases_filepath}' does not exists.")
            # Write data to a YAML file
            with open(all_cases_filepath, 'w') as file:
                yaml.dump(all_cases_data, file, default_flow_style=False)
                print("all_cases.yaml file created.")
        else:
            print(f"***The path '{all_cases_filepath}' exists.")
            with open(all_cases_filepath, 'r') as file:
                data = yaml.safe_load(file)
                self.all_cases = data["FILES_SEG"]
                all_cases_sublist = []
                for i in range(len(self.all_cases)):
                    for element in self.all_cases_path:
                        if self.all_cases[i] in element:
                            all_cases_sublist.append(element)
                self.all_cases_path = all_cases_sublist

        # If the file remaningCases exists, extract the first case of the list
        self.RemainingCases = remaining_cases_path
        if os.path.exists(remaining_cases_path):
            print(f"***The path '{remaining_cases_path}' exists.")

            def extract_first_list_element_from_yaml(remaining_cases_path):
                # Load the YAML file
                with open(remaining_cases_path, 'r') as file:
                    yaml_data = yaml.safe_load(file)

                # Check if 'FILES_SEG' key exists in the YAML data
                if 'FILES_SEG' in yaml_data:
                    # Return the first element of the 'FILES_SEG' list
                    return yaml_data['FILES_SEG'][0]
                else:
                    # Handle the case where 'FILES_SEG' key is not found
                    print("'FILES_SEG' key not found in the YAML file.")
                    return None

            def extract_elements_from_yaml(remaining_cases_path):
                # Load the YAML file
                with open(remaining_cases_path, 'r') as file:
                    yaml_data = yaml.safe_load(file)

                # Check if 'FILES_SEG' key exists in the YAML data
                if 'FILES_SEG' in yaml_data:
                    # Return the first element of the 'FILES_SEG' list
                    return yaml_data['FILES_SEG']
                else:
                    # Handle the case where 'FILES_SEG' key is not found
                    print("'FILES_SEG' key not2 found in the YAML file.")
                    return None

            first_element = extract_first_list_element_from_yaml(
                remaining_cases_path)
            print("First element in the 'FILES_SEG' list in remainingCases: ",
                  first_element)

            files_seg_remaining_list = extract_elements_from_yaml(
                remaining_cases_path)

            self.files_seg_name_list = files_seg_remaining_list
            self.current_case = first_element
            self.current_case_path = self.get_path_from_name(self.current_case)

            # Find the path of the case to be loaded.
            search_directory = self.current_dir
            def find_file_by_name(search_directory, first_element):
                for root, dirs, files in os.walk(search_directory):
                    if first_element in files:
                        return os.path.join(root, first_element)
                return None

            path_to_load = find_file_by_name(search_directory, first_element)

            # Find the path of the files to be in the case list
            def find_files(filenames, root_dir):
                file_paths = []
                for dirpath, _, files in os.walk(root_dir):
                    for file in files:
                        if file in filenames:
                            file_paths.append(os.path.join(dirpath, file))
                return file_paths

            # Sort the list of the remaining cases
            files_seg_remaining_path = sorted(
                find_files(files_seg_remaining_list,
                           self.current_dir))
            self.files_seg_path_list = files_seg_remaining_path

            # Go to the first element in the remainingCases list
            for i in range(len(self.cases)):  # tried with self.RemainingCases
                # and  works too = might create some bugs eventually

                if f'{path_to_load}' == self.all_cases_path[i]:
                    print(f"self.cases_path[i] {i}: ", self.cases_path[i])
                    print("self.current_case_index", self.current_case_index)
                    self.current_case_index = i
                    break

            self.update_UI_case_list()

        else:
            print(f"The path '{remaining_cases_path}' does not exist.")
            file_name = 'remainingCases.yaml'

            def save_files_seg_to_yaml(file_paths=self.RemainingCases,
                                       directory=self.output_folder,
                                       file_name=file_name):
                # Ensure the directory exists
                os.makedirs(directory, exist_ok=True)

                # Create a dictionary with the 'FILES_SEG' key
                data = {
                    'FILES_SEG': self.cases
                }

                # Write the dictionary to the YAML file
                with open((os.path.join(directory, file_name)), 'w') as file:
                    yaml.dump(data, file, default_flow_style=False)

            save_files_seg_to_yaml()

    # Select the ground-truth directory
    def select_gt_dir(self):
        self.enter_function("select_gt_dir")
        self.GTFolder = qt.QFileDialog.getExistingDirectory(
            None, "Open a folder", self.GT_DIR)

    # Getter method to get the segmentation node name - Not sure if this
    # is really useful here.
    @property
    def segmentation_node_name(self):
        self.enter_function("segmentation_node_name")
        return f'{self.current_case}_segmentation'

    def navigate_case(self, direction):
        self.enter_function("navigate_case")
        print("direction:", direction)

        # Check if segmentation is modified
        if self.segmentation_modified:
            print("Segmentation modified")

            result = self.show_message_box(
                'Do you want to save the current segmentation before '
                    'navigating?', 'Save Segmentation?', True)

            # Determine which button was clicked and act accordingly
            if result == qt.QMessageBox.Yes:
                print("User clicked Yes")
                self.save_segmentation(direction)
                self.segmentation_modified = False
            elif result == qt.QMessageBox.No:
                print("User clicked No")
                self.segmentation_modified = False
                if direction == "Next":
                    self.go_next_case()
                else:
                    self.go_previous_case()

            # Remove observers
            self.cleanup_observers()
            print("Continuing with the rest of the code...")

    def go_previous_case(self):
        self.enter_function("go_previous_case")
        if self.segmentation_modified:
            self.navigate_case("Previous")
            return None
        else:
            self.cleanup_observers()

        # ----- ANW Addition ----- : Reset timer when change case and uncheck
        # all checkboxes
        self.resetTimer()
        # self.uncheckAllBoxes()
        self.clearTexts()

        # Code below avoid getting in negative values.
        self.current_case_index = max(0, self.current_case_index - 1)
        self.update_cases()
        self.load_patient()

        # MB CODE BELOW - Comment and message box if first or last case
        if self.current_case_index == 0:
            print("*** This is the first case of the list. ***")
            self.show_message_box("This is the first case of the list.")

        print("*** previous button clicked. self.current_case_index: ",
              self.current_case_index)
        # Watch vs using self.all_cases
        print("*** previous button clicked. len(self.cases)-1: ",
              len(self.cases) - 1)
        print("*** previous button clicked. self.current_case_index + 1: ",
              self.current_case_index + 1)

    def go_next_case(self):
        self.enter_function("go_next_case")
        if self.segmentation_modified:
            self.navigate_case("Next")
            return None
        else:
            self.cleanup_observers()

        # ----- ANW Addition ----- : Reset timer when change case and uncheck
        # all checkboxes
        self.resetTimer()
        # self.uncheckAllBoxes()
        self.clearTexts()

        # ----- ANW Modification ----- : Since index starts at 0, we need to
        # do len(cases)-1 (instead of len(cases)+1).
        # Ex. if we have 10 cases, then len(case)=10 and index goes from 0-9,
        # so we have to take the minimum between len(self.cases)-1 and the
        # current_case_index (which is incremented by 1 everytime we click the
        # button)
        # self.current_case_index = min(len(self.cases)-1,
        # self.current_case_index+1)

        # MB CODE BELOW - Adjust index navigating in multiple lists
        print(" next button clicked. self.current_case_index BEFORE: ",
              self.current_case_index)

        self.current_case_index = min(len(self.all_cases) - 1,
                                      self.current_case_index + 1)
        print(" next button clicked. self.current_case_index AFTER:",
              self.current_case_index)

        self.update_cases()
        self.load_patient()

        if self.current_case_index == (len(self.all_cases) - 1):
            print("*** This is the last case of the list. ***")
            self.show_message_box("This is the last case of the list.")

        print("*** next button clicked. self.current_case_index: ",
              self.current_case_index)
        # Watch vs using self.all_cases
        print("*** next button clicked. len(self.cases)-1: ",
              len(self.cases) - 1)
        print("*** next button clicked. self.current_case_index + 1: ",
              self.current_case_index + 1)

    def select_label_push_button(self, segment_name):
        self.enter_function("select_label_push_button")
        print(f"segment_name: {segment_name}")

        segmentation = self.segmentation_node.GetSegmentation()
        segment_id = segmentation.GetSegmentIdBySegmentName(segment_name)

        # Select segment in the segment editor menu

        self.segmentEditorNode.SetSelectedSegmentID(segment_id)
        self.update_current_segmentation_label()

        # If CT-Scans, can be uncommented
        # self.LB_HU = label_LB_HU
        # self.UB_HU = label_UB_HU

        self.activate_paint()

        """
        NEVER COMMENT THOSE LINES SINCE IT AFFECTS SELECTING LABEL BUTTON
        FUNCTION (makes the icons in segment editor GUI becoming unclickable)
        """
        if (self.MostRecentPausedCasePath != self.current_case_path
                and self.MostRecentPausedCasePath != ""):

            self.timers[self.current_label_index] = Timer(
                number=self.current_label_index)  # new path, new timer

        self.timer_router()

    # Dr Letourneau work. Naming convention not refractored.
    def onPushButton_SemiAutomaticPHE_ShowResult(self):
        self.enter_function("onPushButton_SemiAutomaticPHE_ShowResult")
        self.segmentation_node.GetDisplayNode().SetVisibility(True)
        self.activate_erase()
        self.ui.pushButton_SemiAutomaticPHE_ShowResult.setEnabled(False)

    def ApplyThresholdPHE(self, inLB_HU, inUB_HU):
        self.enter_function("ApplyThresholdPHE")
        self.segmentEditorWidget.setActiveEffectByName("Threshold")
        effect = self.segmentEditorWidget.activeEffect()
        effect.setParameter("MinimumThreshold", f"{inLB_HU}")
        effect.setParameter("MaximumThreshold", f"{inUB_HU}")
        effect.self().onApply()

    def ApplySemiAutomaticThresholdAlgorithm(self):
        self.enter_function("ApplySemiAutomaticThresholdAlgorithm")
        self.ui.pushButton_SemiAutomaticPHE_ShowResult.setEnabled(True)

        self.segmentation_node.GetDisplayNode().SetVisibility(False)

        self.segmentEditorWidget.setActiveEffectByName("Threshold")
        effect = self.segmentEditorWidget.activeEffect()
        effect.setParameter("MinimumThreshold", f"{self.LB_HU}")
        effect.setParameter("MaximumThreshold", f"{self.UB_HU}")
        effect.self().onApply()

        self.segmentEditorWidget.setActiveEffectByName("Scissors")
        effect = self.segmentEditorWidget.activeEffect()
        effect.setParameter("Operation", "EraseOutside")
        effect.setParameter("Shape", "FreeForm")
    def startTimer(self):
        self.enter_function("startTimer")
        with TIMER_MUTEX:
            self.counter = 0
            # Add flag to avoid counting time when user clicks on save segm
            # button
            self.flag2 = True

            # ----- ANW Addition ----- : Code to keep track of time passed
            # with lcdNumber on UI
            # Create a timer
            self.timer = qt.QTimer()
            self.timer.timeout.connect(self.updatelcdNumber)

            # Start the timer and update every second
            self.timer.start(100)  # 1000 ms = 1 second

            # Call the updatelcdNumber function
            self.updatelcdNumber()

    def updatelcdNumber(self):
        # Get the time
        with TIMER_MUTEX:
            if self.flag2:  # add flag to avoid counting time when user
                # clicks on save segm button
                # the timer sends a signal every second (1000 ms).
                self.counter += 1  # the self.timer.timeout.connect(
            # self.updatelcdNumber) function is called every second and
                # updates the counter

            self.ui.lcdNumber.display(self.counter / 10)

    def stopTimer(self):
        with TIMER_MUTEX:
            # If already called once (i.e when user pressed save segm button
            # but forgot to annotator name), simply return the time
            if self.called:
                return self.total_time
            else:
                try:
                    self.total_time = self.counter / 10
                    self.timer.stop()
                    self.flag2 = False  # Flag is for the timer to stop counting
                    self.called = True
                    #   self.time_allocation()
                    return self.total_time
                except AttributeError as e:
                    print(f'!!! YOU DID NOT START THE COUNTER !!! :: {e}')
                    return None

    def resetTimer(self):
        with TIMER_MUTEX:
            # making flag to false : stops the timer
            self.flag2 = False  # For case after the first one the timer
            # stops until the user clicks on the
            self.counter = 0
            self.ui.lcdNumber.display(0)

            # reset button status
            self.enableStartTimerButton()
            self.disablePauseTimerButton()
            self.ui.PauseTimerButton.setText('Pause')
            if (self.ui.PauseTimerButton.isChecked()):
                self.ui.PauseTimerButton.toggle()

            self.disableSegmentAndPaintButtons()

    def enableStartTimerButton(self):
        self.ui.StartTimerButton.setEnabled(True)
        self.ui.StartTimerButton.setStyleSheet("background-color : yellowgreen")
        if (self.ui.StartTimerButton.isChecked()):
            self.ui.StartTimerButton.toggle()

    def disablePauseTimerButton(self):
        self.ui.PauseTimerButton.setStyleSheet("background-color : silver")
        self.ui.PauseTimerButton.setEnabled(False)

    def toggle_start_timer(self):
        if (self.ui.SlicerDirectoryListView.count > 0):
            if self.ui.StartTimerButton.isChecked():
                self.startTimer()
                self.timer_router()

                self.ui.StartTimerButton.setEnabled(False)
                self.ui.StartTimerButton.setStyleSheet(
                    "background-color : silver")

                self.ui.PauseTimerButton.setEnabled(True)
                self.ui.PauseTimerButton.setStyleSheet(
                    "background-color : indianred")

                self.enableSegmentAndPaintButtons()
        else:
            self.ui.StartTimerButton.toggle()

    def toggle_pause_timer(self):
        # if button is checked - Time paused
        if self.ui.PauseTimerButton.isChecked():
            # setting background color to light-blue
            self.ui.PauseTimerButton.setStyleSheet(
                "background-color : lightblue")
            self.ui.PauseTimerButton.setText('Restart')
            self.timer.stop()
            for indiv_timer in self.timers:
                indiv_timer.stop()
            self.flag = False

            self.MostRecentPausedCasePath = self.current_case_path

            self.disableSegmentAndPaintButtons()
            self.activate_erase()

        # if it is unchecked
        else:
            # set background color back to light-grey
            self.ui.PauseTimerButton.setStyleSheet(
                "background-color : indianred")
            self.ui.PauseTimerButton.setText('Pause')
            self.timer.start(100)
            self.timer_router()
            self.flag = True

            self.enableSegmentAndPaintButtons()

    # for the timer Class not the LCD one
    # MB DO NOT COMMENT THIS FUNCTION THIS DISABLE SELECTING NODE ...
    def timer_router(self):
        # MB
        # self.current_label_index = 0
        # print(" tes timer self curent label index : ",
        # self.current_label_index)
        # print(" self timers", self.timers)
        # self.timers[0].start()
        self.timers[self.current_label_index].start()
        self.flag = True

        timer_index = 0
        for timer in self.timers:
            if timer_index != self.current_label_index:
                timer.stop()
            timer_index = timer_index + 1

    def clearTexts(self):
        self.ui.ichtype_other.clear()
        self.ui.EM_comments.clear()

    #TODO: Adapt this function and call it when saving segmentation so name
    # degree and revision step must be written
    def save_node_with_isfile_check_qt_msg_box(self, file_path, node):
        """
        Create folder if it does not exist and save the node to the file_path.
        If the file already exists, a qt message box will ask the user if
        they want to replace the file.
        """
        self.enter_function("save_node_with_isfile_check_qt_msg_box")
        folder_path = os.path.dirname(file_path)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        if not os.path.isfile(file_path):
            slicer.util.saveNode(node, file_path)
        else:
            msg = qt.QMessageBox()
            msg.setWindowTitle('Save As')
            msg.setText(
                f'The file {file_path} already exists \n Do you want to '
                f'replace the existing file?')
            msg.setIcon(qt.QMessageBox.Warning)
            msg.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
            msg.exec()
            if msg.clickedButton() == msg.button(qt.QMessageBox.Ok):
                slicer.util.saveNode(node, file_path)
                return f'File saved as {file_path}'
            else:
                return "File not saved"

    def save_segmentation(self, direction=None):
        self.enter_function("save_segmentation")

        # Stop the timer once clicked on save_segmentation
        # Note that the times may be slightly different if annotations are
        # being recorded for future references than if not.
        self.time_end = datetime.now()

        # Get the segmentation node (the current one)
        self.segmentation_node = self.get_segmentation_node()
        segmentation_node = self.segmentation_node
        segmentation = segmentation_node.GetSegmentation()
        segments_ids = vtk.vtkStringArray()
        segmentation.GetSegmentIDs(segments_ids)

        # Get the volume node (the current one)
        self.volume_node = self.get_volume_node()

        # Get the labelmap volume node (added by chatgpt and saving works!)
        self.label_map_volume_node = slicer.mrmlScene.AddNewNodeByClass(
            'vtkMRMLLabelMapVolumeNode')
        slicer.modules.segmentations.logic(

        ).ExportVisibleSegmentsToLabelmapNode(
            self.segmentation_node,
            self.label_map_volume_node,
            self.volume_node)

        # Note that an attempt to make a separate function with the for loop
        # resulted in application 3D Slicer to crash (hypothesis of conflict
        # between local and global variables)
        for i in range(segments_ids.GetNumberOfValues()):
            segment_id = segments_ids.GetValue(i)
            segment = segmentation.GetSegment(segment_id)
            segment_name = segment.GetName()

            filename = self.remove_file_extension(segment_name)
            version = self.increment_latest_version(filename)
            self.version = version
            print(f"save_segmentation(), for loop {i} version: ", version)
            print(f"save_segmentation(), for loop {i} filename: ", filename)

            # Create a new labelmap volume node
            labelmap_volume_node = slicer.mrmlScene.AddNewNodeByClass(
                "vtkMRMLLabelMapVolumeNode", segment_name + "_labelmap")

            segment_id_array = vtk.vtkStringArray()
            segment_id_array.InsertNextValue(segment_id)

            slicer.modules.segmentations.logic().ExportSegmentsToLabelmapNode(
                segmentation_node, segment_id_array, labelmap_volume_node)

            # Construct the file path
            file_path = os.path.join(
                f"{self.output_folder}{os.sep}versions{os.sep}",
                f"{filename}{version}"
                f"{self.file_extension}")

            # Save the labelmap volume node
            slicer.util.saveNode(labelmap_volume_node, file_path)

            if self.new_cases_for_ref:
                print("self.new_cases_for_ref: ", self.new_cases_for_ref)
                # Construct the file path in the references folder for the label
                file_path_seg = os.path.join(
                    f"{self.GTFolder}{os.sep}{filename}{version}"
                    f"{self.file_extension}")

                # Check if a reference same version already exists, and avoid
                # overwriting.
                if os.path.exists(file_path_seg):
                    print("file_path_seg already exists: ", file_path_seg)
                    new_version_ref = version[2:]
                    new_version_ref = int(new_version_ref)
                    new_version_ref += 1
                    new_version_ref = f"{new_version_ref:02}"
                    version = new_version_ref

                    file_path_seg = os.path.join(
                        f"{self.GTFolder}{os.sep}{filename}_v{new_version_ref}"
                        f"{self.file_extension}")

                print("file_path for label: ", file_path_seg)

                # Save the labelmap volume node
                slicer.util.saveNode(labelmap_volume_node, file_path_seg)

                # Construct the file path in the references folder for volume
                volume_name = self.get_volume_node().GetName()
                file_path_volume = os.path.join(
                    f"{self.GTFolder}{os.sep}volumes{os.sep}{volume_name}"
                    f"{self.file_extension}")

                print("file_path of the volume: ", file_path_volume)

                # Check if a file_path_volume already exists (avoid duplicate)
                if not os.path.exists(file_path_volume):
                    print("file_path_volume does not exist: ", file_path_volume)
                    # Save the volume
                    slicer.util.saveNode(self.get_volume_node(),
                                         file_path_volume)

            # Remove the labelmap volume node from the scene
            slicer.mrmlScene.RemoveNode(labelmap_volume_node)

            print(f"Segment '{segment_name}' saved to: {file_path}")


        # TODO: Some adjustments will be needed to save a specific segment in
        #  the derivatives folder according to BIDS convention.

        # TODO: Create a function that will run a shell script and generate the
        #  Quality Control report from sct.

        # End timer for this case
        self.time_end = datetime.now()

        # TODO: Save a .json file with statistics
        # Save a csv file with statistics for the new cases
        self.save_csv_file(location=self.output_folder)
        if self.new_cases_for_ref:
            # Reset variable for a new case
            self.assessment_dict["name_anonymized"] = "NEW_CASE"
            index_to_set = max(0, self.current_label_index-1)
            self.assessment_dict["filename_final"] = self.all_cases[
                index_to_set]
            # Ensure variable version is convertible into an integer from _vXX
            if isinstance(version, str):
                version = version[-2:]
            self.assessment_dict["latest_ref_version"] = int(version)
            self.assessment_dict["dice_scores"] = "na"
            self.assessment_dict["dice_score_mean"] = "na"

            # Save statistics for new references if new cases will become new
            # references
            self.save_csv_file(location=self.GTFolder, assessment=True)

        # Update remaining-cases and current_index according to new work list
        self.update_remaining_cases()
        # Reset segmentation modification flag
        self.segmentation_modified = False

        # Go to the next case of the list
        print("Going to the next case.")
        self.select_next_navigation(direction)
        # Open a segment editor ready for the next case
        self.start_segmentation()

    # TODO: Create a function that will run a shell script and generate the
    #  Quality Control report from sct.
    def generate_qc_report(self):
        pass
    # # ON HOLD FOR NOW generate qc report
    ###mathieu suggestion in sctmeeting : Env pour 3d slcier dans le
    # terminal pour executer sheell scirpt
    ###go see folder agenda sct meeting for qc
    # print("qc report to be generated")
    # print("self extension directory", self.EXTENSION_DIR)
    # shell_script = (f"{self.EXTENSION_DIR}{os.sep}bin/from_sct_qc.sh")
    # # shell_script = (f"{self.EXTENSION_DIR}{os.sep}bin/from_sct_qc.sh
    # 'jacques' ")
    # #make sure you have the permission to execute the shell script
    # # Execute the shell script
    # # result = subprocess.run([shell_script], capture_output=True,
    # text=True)
    #
    # # background_image
    # # volumeNode = slicer.util.getNode('MRHead')
    # print("******volume node: ", self.volume_node)
    # # background_image_path = self.volume_node.GetStorageNode(
    # ).GetFileName()
    # print("storage node:", self.volume_node.GetStorageNode().GetFileName())
    # bg_image = self.volume_node.GetStorageNode().GetFileName()
    #
    # #name of the current segment
    # segmentEditorWidget =
    # slicer.modules.segmenteditor.widgetRepresentation().self().editor
    # selectedSegmentID = segmentEditorWidget.mrmlSegmentEditorNode(
    # ).GetSelectedSegmentID()
    # print("name of the current segment:", selectedSegmentID)
    # # current segment node path (mask)
    # current_segment_path = f'{self.output_folder}{os.sep}{
    # selectedSegmentID}.nii.gz'
    # print("current segment path", current_segment_path)
    #
    # #path of the current roi segmentation
    # #please note that this works only for bids (always 10 characters for
    # # subject naming)
    # labels_path = f'{self.current_dir}{os.sep}derivatives{os.sep}LABELS'
    #
    #
    # ##ATTENTION! INSTEAD OF USING :10 WE COULD USE PARSE FUNCTION TO
    # # DELIMITATE WITH THE SUBJECT NAME
    # subject_name = f'{self.current_case}'[:10]
    # print("subject name", subject_name)
    # print("type subject name", type(subject_name))
    # current_roi = (f'{labels_path}{os.sep}{subject_name}{os.sep}anat'
    #                f'{os.sep}{self.volume_node.GetName()}_seg.nii.gz')
    # print("path current roi segmentation:", current_roi)
    #
    #
    # #path of output file (from the shell script to run)
    # output_folder = self.output_folder
    # print("path output file", output_folder)
    #
    # result = subprocess.run([shell_script, bg_image,
    #                          current_segment_path, current_roi,
    #                          output_folder],
    #                         capture_output=True,
    #                         text=True)

    # Save a csv file with statistics
    # TODO: Add a comment box so the comments can be saved in the csv file
    def save_csv_file(self, location, assessment=False):
        self.enter_function("save_csv_file")

        self.annotator_name = self.ui.AnnotatorName.text
        self.annotator_degree = self.ui.AnnotatorDegree.currentText
        self.revision_step = self.ui.RevisionStep.currentText
        self.comments_line = self.ui.CommentsLine.text

        print(" save_csv_file(), segmentation_node.name: ",
              self.segmentation_node.GetName())
        print(" save_csv_file(), annotator_name: ", self.annotator_name)
        print(" save_csv_file(), annotator_degree: ", self.annotator_degree)
        print(" save_csv_file(), revision_step: ", self.revision_step)
        print(" save_csv_file(), comments_line: ", self.comments_line)

        def format_time(time):
            return time.strftime("%Y-%m-%d %H:%M:%S")

        def format_dif_time(timedelta):
            timedelta_str = str(timedelta)
            datetime_object = datetime.strptime(timedelta_str , "%H:%M:%S.%f")
            datetime_object = datetime_object.strftime("%H:%M:%S.%f")[:-3]
            print("datetime_object: ", datetime_object)
            return datetime_object


        # Actual variables [formated in list for convenient purposes].
        # Case number defined according to the setting (segmentation vs assess)
        annotator_name = [self.annotator_name]
        annotator_degree = [self.annotator_degree]
        revision_step = [self.revision_step]

        # Help to catch if segment has not been modified and an attempt is
        # made to save statistics
        if self.segmentation_modified:
            begin = [format_time(self.time_begin)]
            end = [format_time(self.time_end)]
            time_difference = [format_dif_time(self.time_end -
                                                    self.time_begin)]
        else:
            self.enter_function("except")
            self.show_message_box(
                "Segmentation has not been modified. Cannot save statistics.")

        comments = [self.comments_line]
        csv_name = self.csv_name

        #TODO: refractor to make it shorter and more efficient. Here,
        # the method can only be used for saving file.csv only while saving
        # or assessing, but this could be extended/optimized.
        if assessment:
            name_anonymized = [self.assessment_dict["name_anonymized"]]
            case_number = [self.assessment_dict["filename_final"]]
            version = [self.get_version_string(self.assessment_dict[
                                                   "latest_ref_version"])]

            dice_scores_dict = [self.assessment_dict["dice_scores"]]
            dice_score_mean = [self.assessment_dict["dice_score_mean"]]
            data = list(zip(name_anonymized,
                            case_number,
                            annotator_name,
                            annotator_degree,
                            revision_step,
                            version,
                            begin,
                            end,
                            time_difference,
                            comments,
                            dice_score_mean,
                            dice_scores_dict))

            # Create the folder if it does not exist
            os.makedirs(location, exist_ok=True)
            # Define the complete file path
            csv_path = os.path.join(location, csv_name)

        else:
            case_number = [self.segmentation_node.GetName()]
            version = [self.version]
            # Combine data into rows using zip
            data = list(zip(case_number,
                            annotator_name,
                            annotator_degree,
                            revision_step,
                            version,
                            begin,
                            end,
                            time_difference,
                            comments))

            # Create the folder if it does not exist
            os.makedirs(location, exist_ok=True)
            # Define the complete file path
            csv_path = os.path.join(location, csv_name)
        # Check if the file already exists
        csv_exists = os.path.isfile(csv_path)

        # Write in csv file or add new data
        with open(csv_path, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Write header only if the file does not already exist
            if not csv_exists:
                # writer.writerow(
                #     ['Case number',
                #      'Annotator Name',
                #      'Annotator Degree',
                #      'Revision Step'])
                if assessment:
                    writer.writerow(
                        ['Anonymized Name',
                         'Case Number',
                         'Annotator Name',
                         'Annotator Degree',
                         'Revision Step',
                         'Version',
                         'Begin',
                         'End',
                         'Time Difference',
                         'Comments',
                         'Dice Score Mean',
                         'Dice Score per Label',
                         ])
                else :
                    writer.writerow(
                        ['Case Number',
                         'Annotator Name',
                         'Annotator Degree',
                         'Revision Step',
                         'Version',
                         'Begin',
                         'End',
                         'Time Difference',
                         'Comments '
                         ])

            # Write data rows
            for row in data:
                writer.writerow(row)

    def push_volumes_to_folder(self):
        self.enter_function("push_volumes_to_folder")
        print("self.new_cases_for_ref: ", self.new_cases_for_ref)

    def update_remaining_cases(self):
        self.enter_function("update_remaining_cases")
        with open(self.RemainingCases, 'r') as file:
            data = yaml.safe_load(file)
            self.files_seg_name_list = data['FILES_SEG']

            self.files_seg_path_list = []
            for i in range(len(self.files_seg_name_list)):
                for element in self.all_cases_path:
                    if self.files_seg_name_list[i] in element:
                        self.files_seg_path_list.append(element)

        index_case_to_modify = self.all_cases.index(self.current_case)
        print("index_case_to_modify: ", index_case_to_modify)
        corresponding_index = self.get_corresponding_index()

        print("Checking if first or last case.")
        if ((corresponding_index[0] == 0)
                or (corresponding_index[0] == len(self.all_cases) - 1)):
            print("First or last case: ", corresponding_index[0])
            self.current_case_modified = self.all_cases[corresponding_index[0]]
            self.current_case_path_modified = self.all_cases_path[
                corresponding_index[0]]

        else:
            self.current_case_modified = self.all_cases[corresponding_index[0]]
            self.current_case_path_modified = self.all_cases_path[
                corresponding_index[0]]

        if self.current_case_modified in data['FILES_SEG']:
            print("self.current_case_modified: ", self.current_case_modified)
            self.index_files_seg = corresponding_index[1]

            self.files_seg_path_list.remove(self.current_case_path_modified)
            self.files_seg_name_list.remove(self.current_case_modified)

            data['FILES_SEG'] = self.files_seg_name_list

            if data['FILES_SEG'] == []:
                print("data['FILES_SEG'] is now empty.")
                self.show_message_box("There is no remaining cases.")
                self.index_files_seg = -1
                self.current_case_index = -1
                self.files_seg_path_list = []

            elif self.index_files_seg >= len(self.files_seg_name_list) - 1:
                print("That means you were on the last case.")
                self.index_files_seg = len(self.files_seg_name_list) - 1
                self.show_message_box("Last case in remaininCases has been "
                                      "segmented. \nGoing to the last "
                                      "case in the remaining list.")

            else:
                print("The list is not empty.")
                self.files_seg_name = self.files_seg_name_list[
                    self.index_files_seg]
                self.current_case_index = self.all_cases.index(
                    self.files_seg_name)

        else:
            print("File not found in the 'FILES_SEG' list.",
                  corresponding_index[1])

        # Update remainingCases with new values
        with open(self.RemainingCases, 'w') as file:
            print("New length of remainingCases.yaml: ", len(data['FILES_SEG']))
            yaml.dump(data, file, default_flow_style=False)

    def select_next_navigation(self, direction=None):
        self.enter_function("select_next_navigation")
        if direction == "Previous":
            if self.current_case_index == 0:
                print("*** This is the first case of the list. ***")
                self.show_message_box("This is the first case of the list.")
            else:
                self.go_previous_case()
        else:
            if self.current_case_index == (len(self.all_cases) - 1):
                print("*** This is the last case of the list. ***")
                self.show_message_box("This is the last case of the list.")
            else:
                self.go_next_case()

    # Function setted here since it is closely related to the immediate above
    # functions
    def get_corresponding_index(self):
        self.enter_function("get_corresponding_index")
        if self.current_case:
            all_cases_index = self.all_cases.index(self.current_case)
            if self.current_case in self.files_seg_name_list:
                files_seg_list_index = self.files_seg_name_list.index(
                    self.current_case)
            else:
                files_seg_list_index = -1
            print("get_corresponding_index(), self.current_cases: ",
                  self.current_case)
            print("get_corresponding_index(), all_cases_index: ",
                  all_cases_index)
            print("get_corresponding_index(), files_seg_list_index: ",
                  files_seg_list_index)
            return (all_cases_index, files_seg_list_index)

    def create_vtk_segment(self):
        self.enter_function("create_vtk_segment")
        # Creates a vtk object from an existing already saved segment.
        # Load Binary Label Map
        filename = self.remove_file_extension(self.segment_name)
        version = self.format_latest_version(filename)
        print("create_vtk_segment(), version: ", version)
        segment_path = (f"{self.output_folder}{os.sep}versions"
                        f"{os.sep}{filename}"
                        f"{version}{self.file_extension}")
        print("create_vtk_segment(), segment_path: ", segment_path)

        labelmap_node = slicer.util.loadLabelVolume(segment_path)

        # If the loaded segment is empty (has only 0 values), will add new
        # segment, but need to check first if empty or not

        # Convert the image data to a numpy array
        scalars = slicer.util.arrayFromVolume(labelmap_node)
        # Check if there are any values other than 0
        label_map_not_empty = np.any(scalars != 0)

        if label_map_not_empty:
            print("labelmap_node is not empty", labelmap_node)
            print('The labelmap volume contains values other than 0')

            # Import it in the segmentation node
            slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(
                labelmap_node, self.segmentation_node)

            # Get the segmentation node
            segmentation = self.segmentation_node.GetSegmentation()

            # Get the segment IDs
            segments_ids = vtk.vtkStringArray()
            print("create_vtk_segment(), segments_ids: ", segments_ids)
            segmentation.GetSegmentIDs(segments_ids)

            # Set the name for the segment
            segment_id = segments_ids.GetValue(
                (segments_ids.GetNumberOfValues() - 1))
            print("create_vtk_segment(), segment_id: ", segment_id)
            segment = segmentation.GetSegment(segment_id)
            print("create_vtk_segment(), segment: ", segment)
            segment_name = f"{self.segment_name}"
            print("segment_name", segment_name)  # Customize the name as needed
            segment.SetName(segment_name)
            print("create_vtk_segment(), segment renamed: ", segment)

        else:
            print("labelmap_node is empty", labelmap_node)
            print('The labelmap volume only contains 0 values')
            self.segmentation_node.GetSegmentation().AddEmptySegment(
                self.segment_name)

    # Is called to load a specific version when selected in the toggle button
    # pop-up list
    def load_version(self, versions_dict, name_of_items):
        self.enter_function("load_version")
        list_version_to_load = versions_dict[f"_{name_of_items}"]
        # Print what appears on the toggle button interface ex v01
        print("load_version(), name_of_items: ", name_of_items)

        list_of_labels = self.get_all_labels_list()
        for segment_version_path in list_version_to_load:
            print("load_version(), segment_version_path: ",
                  segment_version_path)
            labelmap_node = slicer.util.loadLabelVolume(segment_version_path)
            slicer.modules.segmentations.logic(

            ).ImportLabelmapToSegmentationNode(
                labelmap_node, self.segmentation_node)

            # Get the segmentation
            segmentation = self.segmentation_node.GetSegmentation()
            segments_ids = vtk.vtkStringArray()
            segmentation.GetSegmentIDs(segments_ids)
            segment_id = segments_ids.GetValue(
                (segments_ids.GetNumberOfValues() - 1))
            segment = segmentation.GetSegment(segment_id)

            # Find the appropriate label
            for i in range(len(list_of_labels)):
                if list_of_labels[i] in segment_version_path:
                    label = list_of_labels[i]
                    break
                else:
                    label = None
            segment_name = f"{name_of_items}_{label}"
            print("segment_name", segment_name)  # Customize the name as needed
            segment.SetName(segment_name)

        self.segmentation_node.Modified()
        self.subjectHierarchy()
        self.clean_hierarchy_folder()

    def unload_version(self, versions_dict, name_of_items):
        self.enter_function("unload_version")
        list_version_to_unload = versions_dict[f"_{name_of_items}"]
        print("unload_version(), name_of_items: ", name_of_items)

        list_of_labels = self.get_all_labels_list()

        # Get the segmentation
        segmentation = self.segmentation_node.GetSegmentation()
        segments_ids = vtk.vtkStringArray()
        segmentation.GetSegmentIDs(segments_ids)

        number_of_values = segments_ids.GetNumberOfValues()

        # Iterate through all segments and print their names
        for i in range(number_of_values):
            segment_id = segments_ids.GetValue(i)
            segment = segmentation.GetSegment(segment_id)
            segment_name = segment.GetName()
            print(f"Segment ID: {segment_id}, Segment Name: {segment_name}")
            for label in list_of_labels:
                if f"{name_of_items}_{label}" == segment_name:
                    segmentation.RemoveSegment(segment_id)

        self.segmentation_node.Modified()
        self.subjectHierarchy()
        self.clean_hierarchy_folder()

    #Not modified from LLG work
    def msg2_clicked(self, msg2_button):
        if msg2_button.text == 'OK':
            slicer.util.saveNode(self.segmentation_node, self.outputSegmFile)
        else:
            return

    def msg3_clicked(self, msg3_button):
        if msg3_button.text == 'OK':
            slicer.util.saveNode(self.label_map_volume_node,
                                 self.outputSegmFileNifti)
        else:
            return

    def msg4_clicked(self, msg4_button):
        if msg4_button.text == 'OK':
            slicer.util.saveNode(self.volume_node, self.outputVolfile)
        else:
            return

    # Toggle segmentation section
    def toggle_segmentation_versions(self):
        self.enter_function("toggle_segmentation_versions")
        self.open_selection_box()

    def open_selection_box(self):
        self.enter_function("open_selection_box")

        # TODO: Need to uncomment when knowing how to remove the color when
        #  closing the qt dialog box
        # Set the toggle button color when clicked
        # self.set_button_color(self.ui.TGSegmentationVersions,
        # self.color_active)

        # Initialize clickedItems
        self.clickedItems = set()

        # Create the custom widget
        widget = qt.QWidget()
        widget.setWindowTitle(f"{self.current_case}")
        widget.setLayout(qt.QVBoxLayout())

        # Set the minimum size for the widget
        widget.setMinimumSize(300, 200)  # Width: 300, Height: 200

        # Set the widget to stay on top
        widget.setWindowFlags(widget.windowFlags() | qt.Qt.WindowStaysOnTopHint)

        item_layout = qt.QGridLayout()
        widget.layout().addLayout(item_layout)

        # Add items to the selection box
        name = self.all_cases[self.current_case_index]
        filename = self.remove_file_extension(name)
        items = set(sorted(self.get_list_of_versions(filename)))
        print("open_selection_box(), items: ", items)
        name_of_items = []
        for i in range(len(items)):
            name_of_items.append(f"v{i + 1:02d}")
        print("open_selection_box(), name_of_items:", name_of_items)
        max_version = max(items, default=0)  # avoid error if the case has no
        # Previous segmentation
        num_columns = 1
        versions_dict = self.get_all_files_versions(max_version)
        print("open_selection_box(), version_dict", versions_dict)

        # Store button widgets in a dictionary
        self.buttons = {}

        def item_clicked(name_of_items):
            print(f"Item '{name_of_items}' clicked")
            button = self.buttons[name_of_items]
            if name_of_items not in self.clickedItems:
                print(
                    f"New item '{name_of_items}' has not been clicked before.")
                self.item_clicked = True  # Mark this item as clicked
                self.load_version(versions_dict, name_of_items)
                # Set button color to active color (e.g. green)
                self.set_button_color(button, self.color_active)
                self.clickedItems.add(name_of_items)  # Add to clicked items set
            else:
                print(
                    f"Item '{name_of_items}' has already been clicked before.")
                self.item_clicked = False  # Unmark this item as clicked
                self.unload_version(versions_dict, name_of_items)
                # Revert button color to default
                self.set_button_color(button, color="")
                self.clickedItems.remove(
                    name_of_items)  # Remove from clicked items set

        for i, item in enumerate(name_of_items):
            row = i // num_columns
            col = i % num_columns
            button = qt.QPushButton(item)
            button.clicked.connect(lambda _, name=item: item_clicked(
                name))  # Use lambda with default argument
            item_layout.addWidget(button, row, col)
            self.buttons[item] = button

        # Add OK and Cancel buttons
        button_box = qt.QDialogButtonBox(
            qt.QDialogButtonBox.Ok | qt.QDialogButtonBox.Cancel)
        button_box.accepted.connect(widget.close)
        button_box.rejected.connect(widget.close)
        widget.layout().addWidget(button_box)

        # Show the widget as non-modal (allows clicking in other windows)
        widget.show()

    ########## BEGIN OF ASSESS SEGMENTATION SECTION ##########
    def assess_segmentation(self):
        self.enter_function("assess_segmentation")

        # Clear the current scene (this makes sur previous segmentation on
        # the same test case will be removed)
        slicer.mrmlScene.Clear(0)

        # Get the list of the ground truth references segmentations
        ground_truth_list = [f for f in os.listdir(self.GTFolder) if
                             os.path.isfile(os.path.join(self.GTFolder, f)) and
                             not f.startswith('.') and not f.endswith(
                                 '.cache')]

        print("ground_truth_list", ground_truth_list)

        # Element to exclude of the random choice (e.g. file.csv)
        exclude_element = self.csv_name

        # Create a new list excluding the specified element
        ground_truth_list = [elem for elem in ground_truth_list if  elem !=
                             exclude_element]

        # Select a random case to assess and display it in the SliceViewer
        random_item_filepath = random.choice(ground_truth_list)
        filename = self.remove_file_extension(random_item_filepath)

        list_of_labels = self.get_all_labels_list()
        filename_final = self.remove_version_extension(filename)
        filename_final = self.remove_label_extension(filename_final,
                                                     list_of_labels)
        print("filename_final", filename_final)
        filename_final = filename_final[:-1]

        # Get and load the volume associated to the random_item_filepath
        # TODO: if references folder is organized differently, must adapt below
        volumePath = (
            f"{self.GTFolder}{os.sep}volumes{os.sep}{filename_final}"
            f"{self.file_extension}")
        slicer.util.loadVolume(volumePath)

        # Get and set appropriate names for volume node and segmentation masks
        nodeID1 = 'vtkMRMLScalarVolumeNode1'
        volumeNodeMain = slicer.mrmlScene.GetNodeByID(nodeID1)

        count = self.count_asess + 1

        nodeID2 = f'vtkMRMLScalarVolumeNode{count}'
        volumeNodeTest = slicer.mrmlScene.GetNodeByID(nodeID2)
        # Prevent the 'Assessment' buttons to fail working if no volume is
        # already loaded in the scene
        if volumeNodeTest is None:
            volumeNodeTest = slicer.mrmlScene.GetNodeByID(nodeID1)

        def set_assess_name():
            if self.count_asess == 1:
                volumeNodeTest.SetName('NewVolumeName')
                return 'NewVolumeName'
            else:
                volumeNodeTest.SetName(f'NewVolumeName_{self.count_asess}')
                return f'NewVolumeName_{self.count_asess}'

        name_anonymized = set_assess_name()
        slicer.app.processEvents()
        print("name_anonymized: ", name_anonymized)

        # Increment the number of iteration to find easily the appropriate node
        self.count_asess += 1

        # Get latest version of the segmentation to compare
        latest_ref_version = self.get_latest_version(filename_final,
                                                     self.GTFolder)

        # Open the SegmentEditor and create new Segments
        # Step 1: Create a New Segmentation Node
        volume_node_name_an = name_anonymized  # Replace with your volume node name
        volume_node_an = slicer.util.getNode(volume_node_name_an)

        segmentation_node = slicer.mrmlScene.AddNewNodeByClass(
            'vtkMRMLSegmentationNode')
        cur_seg_name = segmentation_node.SetName(
            volume_node_an.GetName() + '_Segmentation')
        segmentation = segmentation_node.GetSegmentation()
        print("assess_segmentation(), cur_seg_name: ", cur_seg_name)

        # Create new segments and attribute them in the segmentation node
        for i in range(len(list_of_labels)):
            segmentation.AddEmptySegment()
            segment_id = segmentation.GetNthSegmentID(i)
            segment = segmentation.GetSegment(segment_id)
            segment.SetName(
                f"{name_anonymized}_{list_of_labels[i]}{self.file_extension}")

        print(f"Created new segmentation node: {segmentation_node.GetName()}")

        if volumeNodeTest == slicer.mrmlScene.GetNodeByID(nodeID1):
            print("volumeNodeTest is nodeID1. No previous volume loaded.")

            # Set the first label_name to self.segment_name (prevent issues)
            self.segment_name = list_of_labels[0]

            # Associate the volumePath (path of the file randomly selected in
            # the ground-truth list) to self.current_case_path (prevent issues)
            self.current_case_path = volumePath

            # Create segment editor widget and node (prevent issues)
            self.segmentEditorWidget = (
                slicer.modules.segmenteditor.widgetRepresentation().self(

                ).editor)
            self.segmentEditorNode = (
                self.segmentEditorWidget.mrmlSegmentEditorNode())

        # Set the segmentation node in the Segmentation Editor
        segmentationEditorWidget = slicer.modules.SegmentEditorWidget.editor
        segmentationEditorWidget.setSegmentationNode(segmentation_node)
        # Set the source volume in the segmentation editor widget
        # Note that setMasterVolumeNode is deprecated. Changed for
        # setSourceVolumeNode instead.
        # segmentationEditorWidget.setMasterVolumeNode(volume_node_an)
        segmentationEditorWidget.setSourceVolumeNode(volume_node_an)


        self.set_all_labels_colors(segmentation_node, True)
        self.first_label_segment_name = (
            f"{name_anonymized}_{list_of_labels[0]}"
            f"{self.file_extension}")
        self.segmentation_node = segmentation_node

        self.select_label_push_button(self.first_label_segment_name)
        self.open_segment_editor()
        # A timer will begin when a segmentation will be modified
        self.observe_segmentation_node()

        # Get the essential values for use in results
        # Global dictionary initialized in setup.
        # Here, we found more convenient to set each element in a dictionary.
        self.assessment_dict["filename"] = filename
        self.assessment_dict["filename_final"] = filename_final
        self.assessment_dict["volumePath"] = volumePath
        self.assessment_dict["name_anonymized"] = name_anonymized
        self.assessment_dict["latest_ref_version"] = latest_ref_version
        self.assessment_dict["volume_node_name_an"] = volume_node_name_an
        self.assessment_dict["segmentation_node"] = segmentation_node
        self.assessment_dict["list_of_labels"] = list_of_labels
        self.assessment_dict["ground_truth_list"] = ground_truth_list

        # Uncomment for debugging
        # self.print_dictionary(self.assessment_dict, "assessment_dict")

    # TODO: Can be done? At each slice that is modified, a dice score is
    #  printed when leaving the slice --- MB not essential
    def get_results(self):
        self.enter_function("get_results")

        # Stop Timer
        self.time_end = datetime.now()

        # Calculate the overall Dice score between the reference segmentation
        # and the new one (saved in assessment folder)

        # Create a list with the latest version of each segment of comparison
        list_of_label_map_to_compare = []
        latest_ref_version = self.assessment_dict["latest_ref_version"]
        latest_ref_version_str = self.get_version_string(latest_ref_version)
        for element in self.assessment_dict["ground_truth_list"]:
            if self.assessment_dict["filename_final"] in element:
                if latest_ref_version_str in element:  # if there are multiple
                    # versions, takes the latest one for comparison!
                    list_of_label_map_to_compare.append(element)

        # Get comparison segmentation node and corresponding volume node
        segmentation_node = self.assessment_dict["segmentation_node"]
        segmentation = segmentation_node.GetSegmentation()
        segment_ids = vtk.vtkStringArray()
        segmentation.GetSegmentIDs(segment_ids)

        volume_node_name_an = self.assessment_dict["volume_node_name_an"]
        volume_node_an = slicer.util.getNode(volume_node_name_an)

        # Add in the display zone the segments of comparison
        list_of_labels = self.assessment_dict["list_of_labels"]
        for i in range(len(list_of_labels)):
            # Specify the segment ID (replace 'Segment_1' with the actual
            # segment ID)
            segment_id = f'Segment_{i + 1}'

            # Create a new labelmap volume node
            label_map_volume_node = slicer.mrmlScene.AddNewNodeByClass(
                'vtkMRMLLabelMapVolumeNode', f'Segment_{i + 1}')

            # Export the segment to the labelmap volume node
            slicer.modules.segmentations.logic().ExportSegmentsToLabelmapNode(
                segmentation_node, [segment_id], label_map_volume_node)

        # Find and load segmentations from reference
        list_of_label_map_names = []
        for element in list_of_label_map_to_compare:
            list_of_label_map_names.append(self.remove_file_extension(element))

        list_of_label_map_path_to_compare = []
        for element in list_of_label_map_to_compare:
            list_of_label_map_path_to_compare.append(
                f"{self.GTFolder}{os.sep}{element}")

        for segment in list_of_label_map_path_to_compare:
            # Path to the labelmap volume file
            label_map_volume_path = segment  # Replace with your actual file path

            # Load the labelmap volume
            [success, label_map_volume_node] = slicer.util.loadLabelVolume(
                label_map_volume_path, returnNode=True)

        # Now here we have all the segments for assessment as labelmap and
        # references label map that can be compared

        # Compute Dice Score for each assessed segment and new segment
        # Before, we pair them in a list of tuple.
        dice_score_tuple_list = []

        filename_final = self.assessment_dict["filename_final"]
        print("get_results(), filename_final: ", filename_final)
        print("get_results(), latest_ref_version_str: ", latest_ref_version_str)

        for i in range(len(list_of_label_map_to_compare)):
            dice_score_tuple_list.append((f"Segment_{i + 1}",
                                  f"{filename_final}_{list_of_labels[i]}"
                                  f"{latest_ref_version_str}"))

        print("get_results(), dice_score_tuple_list: ", dice_score_tuple_list)

        # Create a dictionary containing dice score for each label
        dice_scores = self.compute_dice_score(dice_score_tuple_list,
                                            volume_node_an)

        # Upload the global dictionary of assessment with dice scores
        self.assessment_dict["dice_scores"] = dice_scores

        # Compute the dice_score_mean for all LABELS (if != than inf since
        # inf means both reference and assessment LABELS are empty)
        dice_score_mean = self.compute_mean_dice_score()
        self.assessment_dict["dice_score_mean"] = dice_score_mean

        # TODO: see below (dice score threshold)
        # If Dice Score > threshold, then print/ dialog box! You passed
        # If Dice Score < threshold, then print dialog box! Your Dice Score
        # Please retry and load a new volume to be assessed

        # Save statistics of the assessment and its results
        self.save_csv_file(location=self.GTFolder, assessment=True)

    def compute_dice_score(self, dice_score_tuple_list, reference_volume_node):
        self.enter_function("compute_dice_score")
        dice_score_results_list = []
        dice_score_results_dict = {}
        list_of_labels = self.assessment_dict["list_of_labels"]
        for element in dice_score_tuple_list:
            # Get the label map nodes to compare
            # 0 is the labelmap for the assessed segment
            # 1 is the labelmap for the reference segment
            labelmap1 = slicer.util.getNode(element[0])
            labelmap2 = slicer.util.getNode(element[1])

            # Convert the label maps to SimpleITK images
            sitkImage1 = sitkUtils.PullVolumeFromSlicer(labelmap1)
            sitkImage2 = sitkUtils.PullVolumeFromSlicer(labelmap2)

            # Define a reference volume (choose one of the volumes as reference)
            # reference_volume_node = volume_node_an

            # Convert the reference volume to SimpleITK image
            reference_itk_image = sitkUtils.PullVolumeFromSlicer(
                reference_volume_node)

            # Resample sitkImage1 to match the reference volume
            resampler = sitk.ResampleImageFilter()
            resampler.SetReferenceImage(reference_itk_image)
            resampler.SetInterpolator(sitk.sitkNearestNeighbor)
            resampler.SetDefaultPixelValue(0)

            resampledImage1 = resampler.Execute(sitkImage1)
            resampledImage2 = resampler.Execute(sitkImage2)

            # Ensure the label maps are binary (only 0 and 1)
            resampledImage1 = sitk.BinaryThreshold(resampledImage1,
                                                   lowerThreshold=1,
                                                   upperThreshold=1,
                                                   insideValue=1,
                                                   outsideValue=0)
            resampledImage2 = sitk.BinaryThreshold(resampledImage2,
                                                   lowerThreshold=1,
                                                   upperThreshold=1,
                                                   insideValue=1,
                                                   outsideValue=0)

            # Compute the Dice coefficient
            dice_filter = sitk.LabelOverlapMeasuresImageFilter()
            dice_filter.Execute(resampledImage1, resampledImage2)
            dice_score = dice_filter.GetDiceCoefficient()

            print(f"Dice score {element}:", dice_score)
            # Best option: create a dictionary with the label name in key and
            # dice score in value
            for label in list_of_labels:
                if label in element[1]:
                    dice_score_results_dict[label] = round(dice_score, 3)

            # Optional: create a list with segment names compared and dice score
            dice_score_results_list.append((element[0], element[1], dice_score))

        # Print in the python console the reference volume name and the dice
        # score result for each segment label
        print("reference_volume_node name: ",
              self.assessment_dict["filename_final"])
        self.print_dictionary(dice_score_results_dict,
                              "dice_score_results_dict")
        return dice_score_results_dict

    def compute_mean_dice_score(self):
        self.enter_function("compute_mean_dice_score")
        dice_scores_dict = self.assessment_dict["dice_scores"]
        values = []
        for element in dice_scores_dict:
            if dice_scores_dict[element] != math.inf:
                values.append(dice_scores_dict[element])
        print("values compute mean dice score", values)
        print("type values", type(values))
        print("len values", len(values))

        total_sum = 0
        for i in range(len(values)):
            total_sum += values[i]

        if len(values) == 0:
            self.show_message_box("There is no dice score to average.")
        else:
            mean_dice_score = total_sum / len(values)
            print("mean dice score: ", round(mean_dice_score, 3))
            return round(mean_dice_score, 3)

    ########## END OF ASSESS SEGMENTATION SECTION ##########

    def clicked_pb_create_segmentation(self):
        self.enter_function("clicked_pb_create_segmentation")
        self.select_label_push_button(self.segment_name)

    def start_segmentation(self):
        self.enter_function("start_segmentation")
        self.clicked_pb_create_segmentation()
        self.open_segment_editor()
        self.observe_segmentation_node()
        print("Segment editor opened.")

    def toggle_interpolation_state(self):
        self.enter_function("toggle_interpolation_state")
        volume_node = self.get_volume_node()
        display_node = volume_node.GetDisplayNode()
        current_state = display_node.GetInterpolate()
        display_node.SetInterpolate(not current_state)
        print("current state: ", current_state)
        # toggleButton = self.ui.TGInterpolation
        if current_state == 0:
            self.set_button_color(self.ui.TGInterpolation, self.color_active)
        else:
            self.set_button_color(self.ui.TGInterpolation, self.color_inactive)

    #LLG work

    def msg_warnig_delete_segm_node_clicked(self):
        if slicer.util.getNodesByClass('vtkMRMLSegmentationNode'):
            slicer.mrmlScene.RemoveNode(
                slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0])

    # MB adapted to display the latest version available when clicked
    # TODO: adapt so that if the UI case list is updated, the actual
    #  displayed case will be reloaded with the stte of the load_masks button
    def load_masks(self):
        self.enter_function("load_masks")
        self.mask_loaded = not self.mask_loaded
        print("self.mask_loaded: ", self.mask_loaded)
        if self.mask_loaded:
            self.set_button_color(self.ui.PBLoadMask, self.color_active)
        else:
            self.set_button_color(self.ui.PBLoadMask, self.color_inactive)

    # LLG work
    def convert_nifti_header_Segment(self):
        self.enter_function("convert_nifti_header_Segment")
        # Check if the first segment starts with Segment_1 (e.g. loaded from
        # nnunet).
        # If so change the name and colors of the segments to match the ones
        # in the config file
        first_segment_name = self.segmentation_node.GetSegmentation(

        ).GetNthSegment(
            0).GetName()
        print(f'first_segment_name :: {first_segment_name}')
        if first_segment_name.startswith("Segment_"):
            # iterate through all segments and rename them
            for i in range(
                    self.segmentation_node.GetSegmentation(

                    ).GetNumberOfSegments()):
                segment_name = self.segmentation_node.GetSegmentation(

                ).GetNthSegment(
                    i).GetName()
                print(f' src segment_name :: {segment_name}')
                for label in self.config_yaml["LABELS"]:
                    if label["value"] == int(segment_name.split("_")[-1]):
                        new_segment_name = f"{self.current_case}_{label['name']}"
                        print(f'new segment_name :: {new_segment_name}')
                        self.segmentation_node.GetSegmentation().GetNthSegment(
                            i).SetName(new_segment_name)
                        # set color
                        self.segmentation_node.GetSegmentation().GetNthSegment(
                            i).SetColor(label["color_r"] / 255,
                                        label["color_g"] / 255,
                                        label["color_b"] / 255)

    def update_current_case_paths_by_segmented_volumes(self):
        self.enter_function("update_current_case_paths_by_segmented_volumes")
        print('\n ENTERINE update_current_case_paths_by_segmented_volumes \n')
        print(self.output_seg_dir)
        segmentations = glob(os.path.join(self.output_seg_dir, '*.seg.nrrd'))
        print(len(segmentations))
        print(self.SEGM_REGEX_PATTERN)
        print(os.path.basename(segmentations[0]))
        segmented_IDs = [
            re.findall(self.SEGM_REGEX_PATTERN, os.path.basename(segmentation))[
                0] for segmentation in
            segmentations]

        self.ui.SlicerDirectoryListView.clear()
        for case in self.cases_path:
            case_id = re.findall(self.VOL_REGEX_PATTERN, case)[0]
            item = qt.QListWidgetItem(case_id)
            if not case_id in segmented_IDs:
                item.setForeground(qt.QColor('red'))

            elif case_id in segmented_IDs:
                item.setForeground(qt.QColor('green'))
            self.ui.SlicerDirectoryListView.addItem(item)

    def onpushbuttonttest2(self):
        self.enter_function("onpushbuttonttest2")
        pass

    def push_segment_editor(self):
        self.enter_function("push_segment_editor")

        if self.ui.PBSegmentWindow.isChecked():
            self.ui.PBSegmentWindow.setStyleSheet(
                "background-color : gray")
            self.ui.PBSegmentWindow.setText('Undock Segment Editor')
            slicer.modules.segmenteditor.widgetRepresentation().setParent(None)
            slicer.modules.segmenteditor.widgetRepresentation().show()

        # if it is unchecked (default)
        else:
            self.ui.PBSegmentWindow.setStyleSheet(
                "background-color : lightgray")
            self.ui.PBSegmentWindow.setText('Dock Segment Editor')
            slicer.modules.segmenteditor.widgetRepresentation().setParent(
                slicer.util.mainWindow())

    def push_undo_segmentation(self):
        self.enter_function("push_undo_segmentation")
        self.segmentEditorWidget.undo()

    def on_dropdown_label_select_button(self, value):
        self.enter_function("on_dropdown_label_select_button")
        print("value: ", value)

        self.current_label_index = value
        label = self.config_yaml["LABELS"][value]
        label_name = label["name"]
        print("label: ", label)
        print("label_name: ", label_name)

        try:
            print("*** Try test ***")
            volumeNode = self.get_volume_node()
            segment_name = f"{self.current_case}_{label_name}"
            self.select_label_push_button(segment_name)
            print("*** Try passed ***")
        except:
            print(" *** Try failed. Raised except ***")

    def activate_paint(self):
        self.enter_function("activate_paint")
        self.segmentEditorWidget.setActiveEffectByName("Paint")
        # Note it seems that sometimes you need to activate the effect first
        # with : Assign effect to the segmentEditorWidget using the active
        # effect
        self.effect = self.segmentEditorWidget.activeEffect()
        self.effect.activate()
        self.effect.setParameter('BrushSphere', 1)
        # Seems that you need to activate the effect to see it in Slicer
        # Set up the mask parameters (note that PaintAllowed...was changed to
        # EditAllowed)
        self.segmentEditorNode.SetMaskMode(
            slicer.vtkMRMLSegmentationNode.EditAllowedEverywhere)
        # Set if using Editable intensity range (the range is defined below
        # using object.setParameter)
        # self.segmentEditorNode.SetMasterVolumeIntensityMask(True)
        # self.segmentEditorNode.SetSourceVolumeIntensityMaskRange(
        # self.LB_HU, self.UB_HU)
        # self.segmentEditorNode.SetOverwriteMode(
        # slicer.vtkMRMLSegmentEditorNode.OverwriteAllSegments)

    def keyboard_toggle_fill(self):
        self.enter_function("keyboard_toggle_fill")
        if self.ui.TGToggleFill.isChecked():
            self.ui.TGToggleFill.toggle()
            self.toggle_fill()
        else:
            self.ui.TGToggleFill.toggle()
            self.toggle_fill()

    def toggle_fill(self):
        self.enter_function("toggle_fill")
        if self.ui.TGToggleFill.isChecked():
            self.ui.TGToggleFill.setStyleSheet(
                "background-color : lightgreen")
            self.ui.TGToggleFill.setText('Fill: ON')
            self.segmentation_node.GetDisplayNode().SetOpacity2DFill(100)
        else:
            self.ui.TGToggleFill.setStyleSheet(
                "background-color : indianred")
            self.ui.TGToggleFill.setText('Fill: OFF')
            self.segmentation_node.GetDisplayNode().SetOpacity2DFill(0)

    def toggle_visibility(self):
        self.enter_function("toggle_visibility")
        segmentation_node = self.get_segmentation_node()
        segmentation_display_node = segmentation_node.GetDisplayNode()
        current_visibility = segmentation_display_node.GetVisibility()
        segmentation_display_node.SetVisibility(not current_visibility)

    def togglePaintMask(self):
        self.enter_function("togglePaintMask")
        if self.ui.pushButton_TogglePaintMask.isChecked():
            self.ui.pushButton_TogglePaintMask.setStyleSheet(
                "background-color : lightgreen")
            self.ui.pushButton_TogglePaintMask.setText('Paint Mask ON')
            self.segmentEditorNode.SetMaskMode(
                slicer.vtkMRMLSegmentationNode.EditAllowedEverywhere)

    def open_segment_editor(self):
        self.enter_function("open_segment_editor")
        slicer.util.selectModule("SegmentEditor")
        self.select_label_push_button(self.first_label_segment_name)

    def activate_erase(self):
        self.enter_function("activate_erase")
        self.segmentEditorWidget.setActiveEffectByName("Erase")
        # Note it seems that sometimes you need to activate the effect first
        # with : Assign effect to the segmentEditorWidget using the active
        # effect
        self.effect = self.segmentEditorWidget.activeEffect()
        # Seems that you need to activate the effect to see it in Slicer
        self.effect.activate()
        self.segmentEditorNode.SetMasterVolumeIntensityMask(False)

    def check_match_label_name_value(self):
        self.enter_function("check_match_label_name_value")
        """"
        Check match between label name and values
        seg.nrrd file = outputSegmFile
        seg nifti file = outputSegmFileNifti
        volume nifti file = outputVolfile
        """
        # get the current label name
        # read with slicerio
        print('-' * 20)
        print(f'self.current_case::{self.current_case}')
        print(f'self.outputSegmFile ::{self.outputSegmFile}')
        segmentation_info = slicerio.read_segmentation_info(self.outputSegmFile)
        print('-' * 20)
        print('Segmentation info :')
        print(segmentation_info)

        # get the segment names
        segment_names = slicerio.segment_names(segmentation_info)
        print('-' * 20)
        print('segment names:')
        print(segment_names)

        print('-' * 20)
        print(f'lenght of segment names {len(segment_names)}')
        if len(segment_names) != 3:
            raise ValueError('Number of segments not equal to 3')

        for i in segment_names:
            if self.current_case not in i:
                raise ValueError(
                    f'Case IC not found in segmentation segment name {i}')
            else:
                if 'ich' in i.lower():
                    ich_name = i
                elif 'ivh' in i.lower():
                    ivh_name = i
                elif 'phe' in i.lower():
                    phe_name = i
                else:
                    raise ValueError('Segment name not recognized')

        # #TODO: put in the config file
        segment_names_to_labels = [(ich_name, 1), (ivh_name, 2), (phe_name, 3)]
        voxels, header = nrrd.read(self.outputSegmFile)
        # I think this function corrects the segment names and LABELS
        extracted_voxels, extracted_header = slicerio.extract_segments(
            voxels, header, segmentation_info, segment_names_to_labels)
        # Below could be refactored to a function that take an arbitrary
        # number of segment names and LABELS (e.g. generic qc script)

        # Overwrite the nrrd file
        print(
            f'Writing a copy of the slicerio corrected segmentation file  '
            f'{self.outputSegmFile} with the corrected LABELS and names')
        output_file_pt_id_instanceUid = \
            re.findall(self.VOL_REGEX_PATTERN_PT_ID_INSTUID_SAVE,
                       os.path.basename(self.current_case_path))[0]
        output_dir_segmentation_file_corrected = os.path.join(self.DEFAULT_VOLUME_DIR,
                                                              'Segmentation_file_corrected_slicerio')
        if not os.path.isdir(output_dir_segmentation_file_corrected):
            os.makedirs(output_dir_segmentation_file_corrected)
        output_path = os.path.join(output_dir_segmentation_file_corrected,
                                   f'Slicerio_corrected_segmentation_'
                                   f'{output_file_pt_id_instanceUid}.seg.nrrd')

        try:
            print('-' * 20)
            print('*' * 20)
            print('Segment0')
            print(extracted_header['Segment0_LabelValue'])
            print(extracted_header['Segment0_Name'])
            print('*' * 20)
            print('Segment1')
            print(extracted_header['Segment1_LabelValue'])
            print(extracted_header['Segment1_Name'])
            print('*' * 20)
            print('Segment2')
            print(extracted_header['Segment2_LabelValue'])
            print(extracted_header['Segment2_Name'])

            assert extracted_header['Segment0_LabelValue'] == 1
            assert extracted_header['Segment0_Name'] == ich_name
            assert extracted_header['Segment1_LabelValue'] == 2
            assert extracted_header['Segment1_Name'] == ivh_name
            assert extracted_header['Segment2_LabelValue'] == 3
            assert extracted_header['Segment2_Name'] == phe_name
            print('-' * 20)
            nrrd.write(output_path, extracted_voxels, extracted_header)
            print(
                f'PASSED: Match segmentation LABELS and names for case '
                f'{self.current_case}')



        except AssertionError as e:  # TODO : check for segment index also
            # # Correct segmentation LABELS and names. Not that this requires
            # pynnrd directly.
            print('Correcting segmentation LABELS and names for case {}'.format(
                self.current_case))
            print(e)
            print('Segmentation name {} to label value {}'.format(
                extracted_header['Segment0_Name'],
                extracted_header['Segment0_LabelValue']))
            header['Segment0_LabelValue'] = 1
            header['Segment0_Name'] = ich_name
            print('Segmentation name {} to label value {}'.format(
                extracted_header['Segment1_Name'],
                extracted_header['Segment1_LabelValue']))
            header['Segment1_LabelValue'] = 2
            header['Segment1_Name'] = ivh_name
            print('Segmentation name {} to label value {}'.format(
                extracted_header['Segment2_Name'],
                extracted_header['Segment2_LabelValue']))
            header['Segment2_LabelValue'] = 3
            header['Segment2_Name'] = phe_name
            nrrd.write(output_path, extracted_voxels, extracted_header)
            print(
                f'Corrected: changed the  segmentation LABELS and names '
                f'matches for case {ID}')

    def check_for_outlier_labels(self):
        self.enter_function("check_for_outlier_labels")
        print("Checking for outlier LABELS")
        # Create a label map from the segmentation
        # Get the volume node and segmentation node
        volumeNode = slicer.util.getNodesByClass('vtkMRMLScalarVolumeNode')[0]
        segmentationNode = \
            slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
        segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(
            self.volume_node)

        volumeArray = slicer.util.arrayFromVolume(self.volume_node)

        # Loop through each segment
        segmentIDs = segmentationNode.GetSegmentation().GetSegmentIDs()
        for segmentID in segmentIDs:
            # Export the current segment to a new labelmap
            labelMapVolumeNode = slicer.mrmlScene.AddNewNodeByClass(
                'vtkMRMLLabelMapVolumeNode')
            slicer.modules.segmentations.logic().ExportSegmentsToLabelmapNode(
                segmentationNode, [segmentID],
                labelMapVolumeNode, self.volume_node)
            labelArray = slicer.util.arrayFromVolume(labelMapVolumeNode)
            print(segmentID)
            # Check and correct the values
            array_range = labelArray[
                (volumeArray < self.OUTLIER_THRESHOLD_LB) | (
                        volumeArray > self.OUTLIER_THRESHOLD_UB)]
            if array_range.any():
                print('Voxels to correct')
                labelArray[(volumeArray < self.OUTLIER_THRESHOLD_LB) | (
                        volumeArray > self.OUTLIER_THRESHOLD_UB)] = 0
                slicer.util.updateVolumeFromArray(labelMapVolumeNode,
                                                  labelArray)

                # Clear the original segment
                segmentationNode.GetSegmentation().RemoveSegment(segmentID)

                # Import the corrected labelmap back to this segment
                slicer.modules.segmentations.logic(

                ).ImportLabelmapToSegmentationNode(
                    labelMapVolumeNode,
                    segmentationNode)
            else:
                print('No correction needed')
            # Cleanup this temporary node
            slicer.mrmlScene.RemoveNode(
                labelMapVolumeNode.GetDisplayNode().GetColorNode())
            slicer.mrmlScene.RemoveNode(labelMapVolumeNode)
            # Make sure the segmentation node matches the reference volume
            # geometry
            (self.segmentation_node
            .SetReferenceImageGeometryParameterFromVolumeNode(
                self.volume_node))

    def save_statistics(self):
        self.enter_function("save_statistics")
        volumeNode = slicer.util.getNodesByClass('vtkMRMLScalarVolumeNode')[0]
        segmentationNode = \
            slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
        segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(
            volumeNode)
        segStatLogic = SegmentStatistics.SegmentStatisticsLogic()
        segStatLogic.getParameterNode().SetParameter("Segmentation",
                                                     segmentationNode.GetID())
        segStatLogic.getParameterNode().SetParameter("ScalarVolume",
                                                     volumeNode.GetID())
        segStatLogic.getParameterNode().SetParameter(
            "LabelSegmentStatisticsPlugin.obb_origin_ras.enabled", str(True))
        segStatLogic.getParameterNode().SetParameter(
            "LabelSegmentStatisticsPlugin.obb_diameter_mm.enables", str(True))
        segStatLogic.getParameterNode().SetParameter(
            "LabelSegmentStatisticsPlugin.obb_direction_ras_x_.enabled",
            str(True))
        segStatLogic.getParameterNode().SetParameter(
            "LabelSegmentStatisticsPlugin.obb_direction_ras_y_.enabled",
            str(True))
        segStatLogic.getParameterNode().SetParameter(
            "LabelSegmentStatisticsPlugin.obb_direction_ras_z_.enabled",
            str(True))
        segStatLogic.getParameterNode().SetParameter(
            "LabelSegmentStatisticsPLugin.obb_diameter_mm.enables", str(True))
        segStatLogic.computeStatistics()
        output_file_pt_id_instanceUid = \
            re.findall(self.VOL_REGEX_PATTERN_PT_ID_INSTUID_SAVE,
                       os.path.basename(self.current_case_path))[0]

        outputFilename = 'Volumes_{}_{}_{}.{}'.format(
            output_file_pt_id_instanceUid, self.annotator_name,
            self.revision_step[0], 'csv')
        print('segment statistics output file name: ', outputFilename)
        output_dir_volumes_csv = os.path.join(self.output_folder, 'csv_volumes')
        if not os.path.exists(output_dir_volumes_csv):
            os.makedirs(output_dir_volumes_csv)
        outputFilename = os.path.join(output_dir_volumes_csv, outputFilename)
        if not os.path.isfile(outputFilename):
            segStatLogic.exportToCSVFile(outputFilename)
            print(f'Wrote segmentation file here {outputFilename}')
        else:
            msg = qt.QMessageBox()
            msg.setWindowTitle('Save As')
            msg.setText(
                f'The file {outputFilename} already exists \n Do you want to '
                f'replace the existing file?')
            msg.setIcon(qt.QMessageBox.Warning)
            msg.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
            msg.exec()
            if msg.clickedButton() == msg.button(qt.QMessageBox.Ok):
                segStatLogic.exportToCSVFile(outputFilename)
                print(f'Wrote segmentation file here {outputFilename}')

        segStatLogic.exportToCSVFile(outputFilename)
        stats = segStatLogic.getStatistics()

        # Read the csv and clean it up
        df = pd.read_csv(outputFilename)
        df.set_index('Segment')
        df = df[['Segment', 'LabelmapSegmentStatisticsPlugin.volume_cm3']]
        df.rename(
            columns={'LabelmapSegmentStatisticsPlugin.volume_cm3': "Volumes"},
            inplace=True)
        df['ID'] = df['Segment'].str.extract("(ID_[a-zA-Z0-90]+)_")
        df['Category'] = df['Segment'].str.extract("_([A-Z]+)$")
        df.to_csv(outputFilename, index=False)


class MySlicerModule(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "My Slicer Module"
        self.parent.categories = ["Examples"]
        self.parent.dependencies = []
        self.parent.contributors = ["Your Name (Your Institution)"]
        self.parent.helpText = """This is an example module to demonstrate 
        integrating RenderManager."""
        self.parent.acknowledgementText = """This file was originally 
        developed by Your Name, Your Institution."""


    ########## MOUSE CUSTOMIZATION CLASS ##########

# MB CODE BELOW: MOUSE CUSTOMIZATION CLASS
# Note: the following import are required (e.g. if you want to export it)
# import vtk
# import slicer
# Note that the naming convention PEP8 is not applied to the following code
# Note that this class is instantiated in the set up/initilization of the module

class CustomInteractorStyle(vtk.vtkInteractorStyleImage):
    def __init__(self, sliceWidget=None):
        self.AddObserver("RightButtonPressEvent",
                         self.onRightButtonPressEvent)
        self.AddObserver("MouseMoveEvent", self.onMouseMoveEvent)
        self.AddObserver("RightButtonReleaseEvent",
                         self.onRightButtonReleaseEvent)
        self.AddObserver("MouseWheelForwardEvent",
                         self.onMouseWheelForwardEvent)
        self.AddObserver("MouseWheelBackwardEvent",
                         self.onMouseWheelBackwardEvent)
        self.AddObserver("LeftButtonPressEvent",
                         self.onLeftButtonPressEvent)
        self.AddObserver("LeftButtonReleaseEvent",
                         self.onLeftButtonReleaseEvent)
        self.AddObserver("KeyPressEvent", self.onKeyPressEvent)
        self.AddObserver("KeyReleaseEvent", self.onKeyReleaseEvent)
        self.startPosition = None
        self.sliceWidget = sliceWidget
        self.sliceNode = self.sliceWidget.mrmlSliceNode()
        self.sliceLogic = slicer.app.applicationLogic().GetSliceLogic(
            self.sliceNode)
        self.panning = False
        self.zooming = False
        self.adjustingWindowLevel = False
        self.z_pressed = False

    def onRightButtonPressEvent(self, obj, event):
        self.startPosition = self.GetInteractor().GetEventPosition()
        self.panning = True
        self.OnRightButtonDown()
        return

    def onMouseMoveEvent(self, obj, event):
        if self.panning and self.startPosition:
            currentPosition = self.GetInteractor().GetEventPosition()
            deltaX = self.startPosition[0] - currentPosition[0]
            deltaY = self.startPosition[1] - currentPosition[1]

            # Adjust the image position based on mouse movement
            pan = self.sliceNode.GetXYZOrigin()
            self.sliceNode.SetXYZOrigin(pan[0] + deltaX, pan[1] + deltaY,
                                        pan[2])
            self.sliceNode.Modified()

            self.startPosition = currentPosition
        elif self.adjustingWindowLevel and self.startPosition:
            currentPosition = self.GetInteractor().GetEventPosition()
            deltaX = currentPosition[0] - self.startPosition[0]
            deltaY = self.startPosition[1] - currentPosition[1]

            # Adjust the window level and width based on mouse movement
            volumeNode = self.sliceLogic.GetBackgroundLayer().GetVolumeNode()
            displayNode = volumeNode.GetDisplayNode()
            currentWindowLevel = displayNode.GetLevel()
            currentWindowWidth = displayNode.GetWindow()

            newWindowLevel = currentWindowLevel + deltaY
            newWindowWidth = currentWindowWidth + deltaX

            displayNode.SetLevel(newWindowLevel)
            displayNode.SetWindow(newWindowWidth)

            self.startPosition = currentPosition

        elif self.zooming and self.startPosition:
            self.zoom()
            self.startPosition = self.GetInteractor().GetEventPosition()

        self.OnMouseMove()
        return

    def onRightButtonReleaseEvent(self, obj, event):
        self.startPosition = None
        self.panning = False
        self.OnRightButtonUp()
        return

    def onLeftButtonPressEvent(self, obj, event):
        self.startPosition = self.GetInteractor().GetEventPosition()
        self.adjustingWindowLevel = True
        self.OnLeftButtonDown()
        return

    def onLeftButtonReleaseEvent(self, obj, event):
        self.startPosition = None
        self.adjustingWindowLevel = False
        self.OnLeftButtonUp()
        return

    def onKeyPressEvent(self, obj, event):
        key = self.GetInteractor().GetKeySym()
        if key == "x":
            self.z_pressed = True
        self.OnKeyPress()
        return

    def onKeyReleaseEvent(self, obj, event):
        key = self.GetInteractor().GetKeySym()
        if key == "x":
            self.z_pressed = False
        self.OnKeyRelease()
        return

    def onMouseWheelForwardEvent(self, obj, event):
        if self.z_pressed:
            # print("Mouse scroll")
            self.zoom_in()
            # print("self zoom done")
        else:
            # Move to the next slice
            currentOffset = self.sliceLogic.GetSliceOffset()
            newOffset = currentOffset + self.getSliceSpacing()  # Move one
            # slice forward
            self.sliceLogic.SetSliceOffset(newOffset)
            self.OnMouseWheelForward()
        return

    def onMouseWheelBackwardEvent(self, obj, event):
        if self.z_pressed:
            # print("Mouse scroll")
            self.zoom_out()
        else:
            # Move to the previous slice
            currentOffset = self.sliceLogic.GetSliceOffset()
            newOffset = currentOffset - self.getSliceSpacing()  # Move one
            # slice backward
            self.sliceLogic.SetSliceOffset(newOffset)
            self.OnMouseWheelBackward()
        return

    def zoom_in(self):
        fov = self.sliceNode.GetFieldOfView()
        self.sliceNode.SetFieldOfView(fov[0] * 0.9, fov[1] * 0.9, fov[2])
        self.sliceNode.Modified()

    def zoom_out(self):
        fov = self.sliceNode.GetFieldOfView()
        self.sliceNode.SetFieldOfView(fov[0] / 0.9, fov[1] / 0.9, fov[2])
        self.sliceNode.Modified()

    def zoom(self):
        if self.startPosition:
            fov = self.sliceNode.GetFieldOfView()
            currentPos = self.GetInteractor().GetEventPosition()
            deltaY = self.startPosition[1] - currentPos[1]
            factor = 1.01 if deltaY > 0 else 0.99
            zoomSpeed = 10
            factor = factor ** (abs(deltaY) / zoomSpeed)
            self.sliceNode.SetFieldOfView(fov[0] * factor, fov[1] * factor,
                                          fov[2])
            self.sliceNode.Modified()

    def getSliceSpacing(self):
        volumeNode = self.sliceLogic.GetBackgroundLayer().GetVolumeNode()
        if volumeNode:
            spacing = volumeNode.GetSpacing()
            return spacing[2]  # Return the spacing along the Z-axis
        return 1.0  # Default spacing if volumeNode is not available

class SlicerManualAnnotationLogic(ScriptedLoadableModuleLogic):
    pass

class SlicerManualAnnotationTest(ScriptedLoadableModuleTest):
    """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer
  /ScriptedLoadableModule.py
  """

    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene
        clear will be enough.
    """
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here.
    """
        self.setUp()
        self.test_SlicerManualAnnotation1()

    def test_SlicerManualAnnotation1(self):
        """ Ideally you should have several levels of tests.  At the lowest
        level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert
    other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

        self.delayDisplay("Starting the test")

        # Get/create input data

        pass
