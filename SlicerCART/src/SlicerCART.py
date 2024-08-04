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


# TODO: There is probably a more elegant way to install pacakages through the extension manager when the user installs the extension.
# TODO: check if the package installed with error

# Dictionary of required python packages and their import names
REQUIRED_PYTHON_PACKAGES = {
    "nibabel": "nibabel",
    "pandas": "pandas",
    "PyYAML": "yaml",
    "pynrrd": "nrrd",
    "slicerio": "slicerio",
    "bids_validator": "bids_validator"
}

def check_and_install_python_packages():
    missing_packages = []
    
    for pip_name, import_name in REQUIRED_PYTHON_PACKAGES.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(pip_name)

    if missing_packages:
        msg = "SlicerCART module: The following required python packages are missing:"
        msg += "\n" + "\n".join(missing_packages)
        msg += "\nWould you like to install them now?"
        response = qt.QMessageBox.question(slicer.util.mainWindow(), 'Install Extensions', msg,
                                           qt.QMessageBox.Yes | qt.QMessageBox.No)
        if response == qt.QMessageBox.Yes:
            for pip_name in missing_packages:
                slicer.util.pip_install(pip_name)
                # Wait for the installation to complete
                slicer.app.processEvents()
            qt.QMessageBox.information(slicer.util.mainWindow(), 'Restart Slicer',
                                       'Slicer will now restart to complete the installation.')
            slicer.app.restart()
        else:
            qt.QMessageBox.warning(slicer.util.mainWindow(), 'Missing Extensions',
                                   'The SlicerCART module cannot be loaded without the required extensions.')


check_and_install_python_packages()

from bids_validator import BIDSValidator
import nibabel as nib
import nrrd
import pandas as pd
import slicerio
import yaml

INPUT_FILE_EXTENSION = '*.nii.gz'
INTERPOLATE_VALUE = 0

DEFAULT_VOLUMES_DIRECTORY = ''
DEFAULT_SEGMENTATION_DIRECTORY = ''

REQUIRE_VOLUME_DATA_HIERARCHY_BIDS_FORMAT = False

IS_CLASSIFICATION_REQUESTED = True
IS_SEGMENTATION_REQUESTED = True
IS_SEMI_AUTOMATIC_PHE_TOOL_REQUESTED = True

MODALITY = 'CT'

REQUIRE_EMPTY = True

LABEL_CONFIG_FILENAME = "label_config.yml"
KEYBOARD_SHORTCUTS_CONFIG_FILENAME = "keyboard_shortcuts_config.yml"
CLASSIFICATION_CONFIG_FILENAME = "classification_config.yml"
GENERAL_CONFIG_FILENAME = "general_config.yml"

LABEL_CONFIG_COPY_FILENAME = LABEL_CONFIG_FILENAME.split('.')[0] + '--do-not-modify.yml'
KEYBOARD_SHORTCUTS_CONFIG_COPY_FILENAME = KEYBOARD_SHORTCUTS_CONFIG_FILENAME.split('.')[0] + '--do-not-modify.yml'
CLASSIFICATION_CONFIG_COPY_FILENAME = CLASSIFICATION_CONFIG_FILENAME.split('.')[0] + '--do-not-modify.yml'
GENERAL_CONFIG_COPY_FILENAME = GENERAL_CONFIG_FILENAME.split('.')[0] + '--do-not-modify.yml'

LABEL_CONFIG_FILE_PATH = os.path.join(Path(__file__).parent.resolve(), LABEL_CONFIG_FILENAME)
KEYBOARD_SHORTCUTS_CONFIG_FILE_PATH = os.path.join(Path(__file__).parent.resolve(), KEYBOARD_SHORTCUTS_CONFIG_FILENAME)
CLASSIFICATION_CONFIG_FILE_PATH = os.path.join(Path(__file__).parent.resolve(), CLASSIFICATION_CONFIG_FILENAME)
GENERAL_CONFIG_FILE_PATH = os.path.join(Path(__file__).parent.resolve(), GENERAL_CONFIG_FILENAME)

CONF_FOLDER_NAME = '_conf'

CT_WINDOW_WIDTH = 90
CT_WINDOW_LEVEL = 45



TIMER_MUTEX = RLock()

class SlicerCARTConfigurationInitialWindow(qt.QWidget):
   def __init__(self, segmenter, parent = None):
      super(SlicerCARTConfigurationInitialWindow, self).__init__(parent)

      self.segmenter = segmenter

      layout = qt.QVBoxLayout()

      self.reuse_configuration_hbox = qt.QHBoxLayout()

      self.new_config_radio_button = qt.QRadioButton('New configuration', self)
      self.reuse_config_radio_button = qt.QRadioButton('Continue from existing output folder', self)
      self.use_template_config_radio_button = qt.QRadioButton('Use template configuration', self)

      self.reuse_configuration_hbox.addWidget(self.new_config_radio_button)
      self.reuse_configuration_hbox.addWidget(self.reuse_config_radio_button)
      self.reuse_configuration_hbox.addWidget(self.use_template_config_radio_button)

      self.new_config_radio_button.toggled.connect(lambda: self.update_selected_reuse_config_option(self.new_config_radio_button.text))
      self.reuse_config_radio_button.toggled.connect(lambda: self.update_selected_reuse_config_option(self.reuse_config_radio_button.text))
      self.use_template_config_radio_button.toggled.connect(lambda: self.update_selected_reuse_config_option(self.use_template_config_radio_button.text))

      self.new_config_radio_button.setChecked(True) # par défaut
      self.reuse_configuration_selected_option = self.new_config_radio_button.text

      layout.addLayout(self.reuse_configuration_hbox) 

      self.next_button = qt.QPushButton('Next')
      self.next_button.clicked.connect(self.push_next)
      layout.addWidget(self.next_button)

      self.cancel_button = qt.QPushButton('Cancel')
      self.cancel_button.clicked.connect(self.push_cancel)
      layout.addWidget(self.cancel_button)

      self.setLayout(layout)
      self.setWindowTitle("Configure SlicerCART")
      self.resize(800, 100)
   
   def update_selected_reuse_config_option(self, option):
       self.reuse_configuration_selected_option = option
   
   def push_next(self):
       if self.reuse_configuration_selected_option == self.reuse_config_radio_button.text:
           msg = qt.QMessageBox()
           msg.setWindowTitle('Informative Message')
           msg.setText('Please select the working output directory. ')
           msg.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
           msg.buttonClicked.connect(self.select_output_folder_clicked)
           msg.exec()
       elif self.reuse_configuration_selected_option == self.use_template_config_radio_button.text:
           msg = qt.QMessageBox()
           msg.setWindowTitle('Informative Message')
           msg.setText('Please select the _conf folder containing the template configuration files. ')
           msg.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
           msg.buttonClicked.connect(self.select_template_folder_clicked)
           msg.exec()
       elif self.reuse_configuration_selected_option == self.new_config_radio_button.text:
           slicerCARTConfigurationSetupWindow = SlicerCARTConfigurationSetupWindow(self.segmenter)
           slicerCARTConfigurationSetupWindow.show()
           self.segmenter.ui.SelectOutputFolder.setVisible(True)
           self.close()

   def select_output_folder_clicked(self, button):
       if button.text == 'OK':
          global REQUIRE_EMPTY
          REQUIRE_EMPTY = False
          self.segmenter.onSelectOutputFolder()
          REQUIRE_EMPTY = True
          self.segmenter.ui.SelectOutputFolder.setVisible(False)
          if (os.path.exists(f'{self.segmenter.outputFolder}{os.sep}{CONF_FOLDER_NAME}') and
             os.path.exists(f'{self.segmenter.outputFolder}{os.sep}{CONF_FOLDER_NAME}{os.sep}{LABEL_CONFIG_COPY_FILENAME}') and 
             os.path.exists(f'{self.segmenter.outputFolder}{os.sep}{CONF_FOLDER_NAME}{os.sep}{CLASSIFICATION_CONFIG_COPY_FILENAME}') and 
             os.path.exists(f'{self.segmenter.outputFolder}{os.sep}{CONF_FOLDER_NAME}{os.sep}{GENERAL_CONFIG_COPY_FILENAME}') and
             os.path.exists(f'{self.segmenter.outputFolder}{os.sep}{CONF_FOLDER_NAME}{os.sep}{KEYBOARD_SHORTCUTS_CONFIG_COPY_FILENAME}')):
                # use this configuration directly
                shutil.copy(f'{self.segmenter.outputFolder}{os.sep}{CONF_FOLDER_NAME}{os.sep}{LABEL_CONFIG_COPY_FILENAME}', LABEL_CONFIG_FILE_PATH)
                shutil.copy(f'{self.segmenter.outputFolder}{os.sep}{CONF_FOLDER_NAME}{os.sep}{CLASSIFICATION_CONFIG_COPY_FILENAME}', CLASSIFICATION_CONFIG_FILE_PATH)
                shutil.copy(f'{self.segmenter.outputFolder}{os.sep}{CONF_FOLDER_NAME}{os.sep}{GENERAL_CONFIG_COPY_FILENAME}', GENERAL_CONFIG_FILE_PATH)
                shutil.copy(f'{self.segmenter.outputFolder}{os.sep}{CONF_FOLDER_NAME}{os.sep}{KEYBOARD_SHORTCUTS_CONFIG_COPY_FILENAME}', KEYBOARD_SHORTCUTS_CONFIG_FILE_PATH)
                
                self.segmenter.setup_configuration()
                self.close()
          else:
                msg = qt.QMessageBox()
                msg.setWindowTitle('Informative Message')
                msg.setText('The selected output folder does not contain the required configuration files for SlicerCART. Please try again. ')
                msg.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
                msg.buttonClicked.connect(self.error_msg_for_output_folder_selection_clicked)
                msg.exec()
          
       else:
          slicerCART_configuration_initial_window = SlicerCARTConfigurationInitialWindow(self.segmenter)
          slicerCART_configuration_initial_window.show()
          self.close()
          return
       
   def error_msg_for_output_folder_selection_clicked(self, button):
        slicerCART_configuration_initial_window = SlicerCARTConfigurationInitialWindow(self.segmenter)
        slicerCART_configuration_initial_window.show()
        self.close()
   
   # TODO Delph : validate that the onSelectOutputFile verifyCompatibility is required??? evaluate use cases
   def select_template_folder_clicked(self, button):
       if button.text == 'OK':
          conf_folder_path = qt.QFileDialog.getExistingDirectory(None,"Open a folder", '', qt.QFileDialog.ShowDirsOnly)
          if (os.path.split(conf_folder_path)[1] == CONF_FOLDER_NAME and
              os.path.exists(f'{conf_folder_path}{os.sep}{LABEL_CONFIG_COPY_FILENAME}') and 
              os.path.exists(f'{conf_folder_path}{os.sep}{CLASSIFICATION_CONFIG_COPY_FILENAME}') and 
              os.path.exists(f'{conf_folder_path}{os.sep}{GENERAL_CONFIG_COPY_FILENAME}') and
              os.path.exists(f'{conf_folder_path}{os.sep}{KEYBOARD_SHORTCUTS_CONFIG_COPY_FILENAME}')):
                 
              slicerCARTConfigurationSetupWindow = SlicerCARTConfigurationSetupWindow(self.segmenter, conf_folder_path)
              slicerCARTConfigurationSetupWindow.show()
              self.segmenter.ui.SelectOutputFolder.setVisible(True)
              self.close()

          else:
              msg = qt.QMessageBox()
              msg.setWindowTitle('Informative Message')
              msg.setText('The selected output folder does not contain the required configuration files for SlicerCART. Please try again. ')
              msg.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
              msg.buttonClicked.connect(self.error_msg_for_output_folder_selection_clicked)
              msg.exec()
              
       else:
          slicerCART_configuration_initial_window = SlicerCARTConfigurationInitialWindow(self.segmenter)
          slicerCART_configuration_initial_window.show()
          self.close()
          return
       
   def push_cancel(self):
       msg = qt.QMessageBox()
       msg.setWindowTitle('Informative Message')
       msg.setText('Using default configurations. To select a different configuration, restart the application. ')
       msg.exec()

       self.segmenter.setup_configuration()
       self.close()

class SlicerCARTConfigurationSetupWindow(qt.QWidget):
   def __init__(self, segmenter, conf_folder_path = None, parent = None):
      super(SlicerCARTConfigurationSetupWindow, self).__init__(parent)

      if conf_folder_path is not None:
          shutil.copy(f'{conf_folder_path}{os.sep}{LABEL_CONFIG_COPY_FILENAME}', LABEL_CONFIG_FILE_PATH)
          shutil.copy(f'{conf_folder_path}{os.sep}{CLASSIFICATION_CONFIG_COPY_FILENAME}', CLASSIFICATION_CONFIG_FILE_PATH)
          shutil.copy(f'{conf_folder_path}{os.sep}{GENERAL_CONFIG_COPY_FILENAME}', GENERAL_CONFIG_FILE_PATH)
          shutil.copy(f'{conf_folder_path}{os.sep}{KEYBOARD_SHORTCUTS_CONFIG_COPY_FILENAME}', KEYBOARD_SHORTCUTS_CONFIG_FILE_PATH) 

      with open(GENERAL_CONFIG_FILE_PATH, 'r') as file:
            self.general_config_yaml = yaml.full_load(file)
      with open(KEYBOARD_SHORTCUTS_CONFIG_FILE_PATH, 'r') as file:
            self.keyboard_shortcuts_config_yaml = yaml.full_load(file)
    
      self.set_default_values()

      self.segmenter = segmenter

      layout = qt.QVBoxLayout()

      task_button_hbox = qt.QHBoxLayout()

      task_button_hbox_label = qt.QLabel()
      task_button_hbox_label.setText('Task : ')
      task_button_hbox_label.setStyleSheet("font-weight: bold")

      self.segmentation_task_checkbox = qt.QCheckBox()
      self.segmentation_task_checkbox.setText('Segmentation')

      self.classification_task_checkbox = qt.QCheckBox()
      self.classification_task_checkbox.setText('Classification')

      task_button_hbox.addWidget(task_button_hbox_label)
      task_button_hbox.addWidget(self.segmentation_task_checkbox)
      task_button_hbox.addWidget(self.classification_task_checkbox)

      layout.addLayout(task_button_hbox)

      modality_hbox = qt.QHBoxLayout()

      modality_hbox_label = qt.QLabel()
      modality_hbox_label.setText('Modality : ')
      modality_hbox_label.setStyleSheet("font-weight: bold")

      self.ct_modality_radio_button = qt.QRadioButton('CT', self)
      self.mri_modality_radio_button = qt.QRadioButton('MRI', self)

      modality_hbox.addWidget(modality_hbox_label)
      modality_hbox.addWidget(self.ct_modality_radio_button)
      modality_hbox.addWidget(self.mri_modality_radio_button)

      layout.addLayout(modality_hbox)

      self.include_semi_automatic_PHE_tool_hbox = qt.QHBoxLayout()
      
      self.include_semi_automatic_PHE_tool_label = qt.QLabel()
      self.include_semi_automatic_PHE_tool_label.setText('Include Semi-Automatic PHE Segmentation Tool? ')
      self.include_semi_automatic_PHE_tool_label.setStyleSheet("font-weight: bold")

      self.include_semi_automatic_PHE_tool_combobox = qt.QComboBox()
      self.include_semi_automatic_PHE_tool_combobox.addItem('Yes') 
      self.include_semi_automatic_PHE_tool_combobox.addItem('No')

      self.include_semi_automatic_PHE_tool_hbox.addWidget(self.include_semi_automatic_PHE_tool_label)
      self.include_semi_automatic_PHE_tool_hbox.addWidget(self.include_semi_automatic_PHE_tool_combobox)

      layout.addLayout(self.include_semi_automatic_PHE_tool_hbox)

      bids_hbox = qt.QHBoxLayout()

      self.bids_hbox_label = qt.QLabel()
      self.bids_hbox_label.setText('Impose BIDS ? ')
      self.bids_hbox_label.setStyleSheet("font-weight: bold")
      bids_hbox.addWidget(self.bids_hbox_label)

      self.bids_combobox = qt.QComboBox()
      self.bids_combobox.addItem('Yes') 
      self.bids_combobox.addItem('No')

      bids_hbox.addWidget(self.bids_combobox)

      layout.addLayout(bids_hbox)

      file_extension_hbox = qt.QHBoxLayout()

      self.file_extension_label = qt.QLabel()
      self.file_extension_label.setText('Input File Extension : ')
      self.file_extension_label.setStyleSheet("font-weight: bold")
      file_extension_hbox.addWidget(self.file_extension_label)

      self.file_extension_combobox = qt.QComboBox()
      self.file_extension_combobox.addItem('*.nii.gz') 
      self.file_extension_combobox.addItem('*.nrrd')

      file_extension_hbox.addWidget(self.file_extension_combobox)

      layout.addLayout(file_extension_hbox)

      initial_view_hbox = qt.QHBoxLayout()

      self.initial_view_label = qt.QLabel()
      self.initial_view_label.setText('Initial View : ')
      self.initial_view_label.setStyleSheet("font-weight: bold")
      initial_view_hbox.addWidget(self.initial_view_label)

      self.initial_view_combobox = qt.QComboBox()
      self.initial_view_combobox.addItem('Red (axial)')
      self.initial_view_combobox.addItem('Yellow (sagittal)')
      self.initial_view_combobox.addItem('Green (coronal)')

      initial_view_hbox.addWidget(self.initial_view_combobox)

      layout.addLayout(initial_view_hbox)

      interpolate_hbox = qt.QHBoxLayout()

      self.interpolate_label = qt.QLabel()
      self.interpolate_label.setText('Interpolate Image? ')
      self.interpolate_label.setStyleSheet("font-weight: bold")
      interpolate_hbox.addWidget(self.interpolate_label)

      self.interpolate_combobox = qt.QComboBox()
      self.interpolate_combobox.addItem('No') 
      self.interpolate_combobox.addItem('Yes')

      interpolate_hbox.addWidget(self.interpolate_combobox)

      layout.addLayout(interpolate_hbox)

      ct_window_level_hbox = qt.QHBoxLayout()

      self.ct_window_level_label = qt.QLabel()
      self.ct_window_level_label.setText('Window Level : ')
      self.ct_window_level_label.setStyleSheet("font-weight: bold")
      ct_window_level_hbox.addWidget(self.ct_window_level_label)

      self.ct_window_level_line_edit = qt.QLineEdit(self.ct_window_level_selected)
      onlyInt = qt.QIntValidator()
      self.ct_window_level_line_edit.setValidator(onlyInt)
      ct_window_level_hbox.addWidget(self.ct_window_level_line_edit)

      layout.addLayout(ct_window_level_hbox)

      ct_window_width_hbox = qt.QHBoxLayout()

      self.ct_window_width_label = qt.QLabel()
      self.ct_window_width_label.setText('Window Width : ')
      self.ct_window_width_label.setStyleSheet("font-weight: bold")
      ct_window_width_hbox.addWidget(self.ct_window_width_label)
      
      self.ct_window_width_line_edit = qt.QLineEdit(self.ct_window_width_selected)
      onlyInt = qt.QIntValidator()
      self.ct_window_width_line_edit.setValidator(onlyInt)
      ct_window_width_hbox.addWidget(self.ct_window_width_line_edit)

      layout.addLayout(ct_window_width_hbox)

      ##########################################
      # TODO Delph : create buttons

      # if classification : configure checkboxes, comboboxes, text fields

      # TODO Delph : if new configuration, force empty output folder upon selection 
      # TODO Delph : if template configuration, BE MORE FLEXIBLE (issue #30) allow selection of existing outputFolder with config 
      # only if the configuration changed superficially (impose_bids : true to false only; not input file ext;
      #  is_classif || is_segment : true to false only; is_semi_auto : any; not modality; slice_view : any; window: any)
      # ks : any
      # labels : any HU range; any color; append at end ; no modif name || value 
      # classif : append only (AND WORK MUST BE DONE TO REORG PREV DATA TO HAVE EMPTY FIELDS i.e. no mismatch of columns and data in .csv)

      ##########################################

      toggle_fill_ks_hbox = qt.QHBoxLayout()

      toggle_fill_ks_label = qt.QLabel()
      toggle_fill_ks_label.setText('Toggle Fill Keyboard Shortcut : ')
      toggle_fill_ks_label.setStyleSheet("font-weight: bold")
      toggle_fill_ks_hbox.addWidget(toggle_fill_ks_label)

      self.toggle_fill_ks_line_edit = qt.QLineEdit(self.toggle_fill_ks_selected)
      self.toggle_fill_ks_line_edit.setMaxLength(1)
      toggle_fill_ks_hbox.addWidget(self.toggle_fill_ks_line_edit)

      layout.addLayout(toggle_fill_ks_hbox)

      toggle_visibility_ks_hbox = qt.QHBoxLayout()

      toggle_visibility_ks_label = qt.QLabel()
      toggle_visibility_ks_label.setText('Toggle Visibility Keyboard Shortcut : ')
      toggle_visibility_ks_label.setStyleSheet("font-weight: bold")
      toggle_visibility_ks_hbox.addWidget(toggle_visibility_ks_label)

      self.toggle_visibility_ks_line_edit = qt.QLineEdit(self.toggle_visibility_ks_selected)
      self.toggle_visibility_ks_line_edit.setMaxLength(1)
      toggle_visibility_ks_hbox.addWidget(self.toggle_visibility_ks_line_edit)

      layout.addLayout(toggle_visibility_ks_hbox)

      undo_ks_hbox = qt.QHBoxLayout()

      undo_ks_label = qt.QLabel()
      undo_ks_label.setText('Undo Keyboard Shortcut : ')
      undo_ks_label.setStyleSheet("font-weight: bold")
      undo_ks_hbox.addWidget(undo_ks_label)

      self.undo_ks_line_edit = qt.QLineEdit(self.undo_ks_selected)
      self.undo_ks_line_edit.setMaxLength(1)
      undo_ks_hbox.addWidget(self.undo_ks_line_edit)

      layout.addLayout(undo_ks_hbox)

      save_seg_ks_hbox = qt.QHBoxLayout()

      save_seg_ks_label = qt.QLabel()
      save_seg_ks_label.setText('Save Segmentation Keyboard Shortcut : ')
      save_seg_ks_label.setStyleSheet("font-weight: bold")
      save_seg_ks_hbox.addWidget(save_seg_ks_label)

      self.save_seg_ks_line_edit = qt.QLineEdit(self.save_seg_ks_selected)
      self.save_seg_ks_line_edit.setMaxLength(1)
      save_seg_ks_hbox.addWidget(self.save_seg_ks_line_edit)

      layout.addLayout(save_seg_ks_hbox)

      smooth_ks_hbox = qt.QHBoxLayout()

      smooth_ks_label = qt.QLabel()
      smooth_ks_label.setText('Smooth Margins Keyboard Shortcut : ')
      smooth_ks_label.setStyleSheet("font-weight: bold")
      smooth_ks_hbox.addWidget(smooth_ks_label)

      self.smooth_ks_line_edit = qt.QLineEdit(self.smooth_ks_selected)
      self.smooth_ks_line_edit.setMaxLength(1)
      smooth_ks_hbox.addWidget(self.smooth_ks_line_edit)

      layout.addLayout(smooth_ks_hbox)

      remove_small_holes_ks_hbox = qt.QHBoxLayout()

      remove_small_holes_ks_label = qt.QLabel()
      remove_small_holes_ks_label.setText('Remove Small Holes Keyboard Shortcut : ')
      remove_small_holes_ks_label.setStyleSheet("font-weight: bold")
      remove_small_holes_ks_hbox.addWidget(remove_small_holes_ks_label)

      self.remove_small_holes_ks_line_edit = qt.QLineEdit(self.remove_small_holes_ks_selected)
      self.remove_small_holes_ks_line_edit.setMaxLength(1)
      remove_small_holes_ks_hbox.addWidget(self.remove_small_holes_ks_line_edit)

      layout.addLayout(remove_small_holes_ks_hbox)

      interpolate_ks_hbox = qt.QHBoxLayout()

      interpolate_ks_label = qt.QLabel()
      interpolate_ks_label.setText('Interpolate Image Keyboard Shortcut : ')
      interpolate_ks_label.setStyleSheet("font-weight: bold")
      interpolate_ks_hbox.addWidget(interpolate_ks_label)

      self.interpolate_ks_line_edit = qt.QLineEdit(self.interpolate_ks_selected)
      self.interpolate_ks_line_edit.setMaxLength(1)
      interpolate_ks_hbox.addWidget(self.interpolate_ks_line_edit)

      layout.addLayout(interpolate_ks_hbox)

      self.configure_labels_button = qt.QPushButton('Configure Labels...')
      self.configure_labels_button.setStyleSheet("background-color : yellowgreen")
      layout.addWidget(self.configure_labels_button)

      self.previous_button = qt.QPushButton('Previous')
      layout.addWidget(self.previous_button)
      
      self.apply_button = qt.QPushButton('Apply')
      layout.addWidget(self.apply_button)

      self.cancel_button = qt.QPushButton('Cancel')
      layout.addWidget(self.cancel_button)

      self.populate_default_values()
      self.connect_buttons_to_callbacks()

      self.setLayout(layout)
      self.setWindowTitle("Configure SlicerCART")
      self.resize(800, 200)
   
   def connect_buttons_to_callbacks(self):
       self.segmentation_task_checkbox.stateChanged.connect(self.segmentation_checkbox_state_changed)
       self.ct_modality_radio_button.toggled.connect(lambda: self.update_selected_modality(self.ct_modality_radio_button.text))
       self.mri_modality_radio_button.toggled.connect(lambda: self.update_selected_modality(self.mri_modality_radio_button.text))
       self.include_semi_automatic_PHE_tool_combobox.currentIndexChanged.connect(self.update_include_semi_automatic_PHE_tool)
       self.bids_combobox.currentIndexChanged.connect(self.update_bids)
       self.file_extension_combobox.currentIndexChanged.connect(self.update_file_extension)
       self.initial_view_combobox.currentIndexChanged.connect(self.update_initial_view)
       self.interpolate_combobox.currentIndexChanged.connect(self.update_interpolate)
       self.ct_window_level_line_edit.textChanged.connect(self.update_ct_window_level)
       self.ct_window_width_line_edit.textChanged.connect(self.update_ct_window_width)
       self.toggle_fill_ks_line_edit.textChanged.connect(self.update_toggle_fill_ks)
       self.toggle_visibility_ks_line_edit.textChanged.connect(self.update_toggle_visibility_ks)
       self.undo_ks_line_edit.textChanged.connect(self.update_undo_ks)
       self.save_seg_ks_line_edit.textChanged.connect(self.update_save_seg_ks)
       self.smooth_ks_line_edit.textChanged.connect(self.update_smooth_ks)
       self.remove_small_holes_ks_line_edit.textChanged.connect(self.update_remove_small_holes_ks)
       self.interpolate_ks_line_edit.textChanged.connect(self.update_interpolate_ks)
       self.configure_labels_button.clicked.connect(self.push_configure_labels)
       self.previous_button.clicked.connect(self.push_previous)
       self.apply_button.clicked.connect(self.push_apply)
       self.cancel_button.clicked.connect(self.push_cancel)
   
   def populate_default_values(self):
       if self.include_semi_auto_PHE_tool_selected_option == 'Yes':
           self.include_semi_automatic_PHE_tool_combobox.setCurrentIndex(0)
       else:
           self.include_semi_automatic_PHE_tool_combobox.setCurrentIndex(1)
    
       
       if self.modality_selected == 'CT':
           self.ct_modality_radio_button.setChecked(True)
       elif self.modality_selected == 'MRI':
           self.mri_modality_radio_button.setChecked(True)

       if self.bids_selected:
           self.bids_combobox.setCurrentIndex(0)
       else:
           self.bids_combobox.setCurrentIndex(1)
    
       if 'Red' in self.initial_view_selected:
           self.initial_view_combobox.setCurrentIndex(0)
       elif 'Yellow' in self.initial_view_selected:
           self.initial_view_combobox.setCurrentIndex(1)
       elif 'Green' in self.initial_view_selected:
           self.initial_view_combobox.setCurrentIndex(2)
    
       if self.file_extension_selected == '*.nii.gz':
           self.file_extension_combobox.setCurrentIndex(0)
       elif self.file_extension_selected == '*.nrrd':
           self.file_extension_combobox.setCurrentIndex(1)

       self.interpolate_combobox.setCurrentIndex(self.interpolate_selected)

       self.segmentation_task_checkbox.setChecked(self.segmentation_selected)
       self.classification_task_checkbox.setChecked(self.classification_selected)

       self.segmentation_checkbox_state_changed()

   def set_default_values(self):
       self.segmentation_selected = self.general_config_yaml['is_segmentation_requested'] 
       self.classification_selected = self.general_config_yaml['is_classification_requested']

       if self.general_config_yaml['is_semi_automatic_phe_tool_requested']:  
            self.include_semi_auto_PHE_tool_selected_option = 'Yes'
       else:
            self.include_semi_auto_PHE_tool_selected_option = 'No'

       self.modality_selected = self.general_config_yaml['modality']

       self.bids_selected = self.general_config_yaml['impose_bids_format'] 

       self.ct_window_level_selected = self.general_config_yaml['ct_window_level'] 
       self.ct_window_width_selected = self.general_config_yaml['ct_window_width']  
       self.file_extension_selected = self.general_config_yaml['input_filetype'] 

       if self.general_config_yaml['slice_view_color'] == 'Red':
           self.initial_view_selected = 'Red (axial)'
       elif self.general_config_yaml['slice_view_color'] == 'Yellow':
           self.initial_view_selected = 'Yellow (sagittal)'
       elif self.general_config_yaml['slice_view_color'] == 'Green':
           self.initial_view_selected = 'Green (coronal)'

       self.interpolate_selected = self.general_config_yaml['interpolate_value'] 

       self.toggle_fill_ks_selected = self.keyboard_shortcuts_config_yaml['KEYBOARD_SHORTCUTS'][0]['shortcut'] 
       self.toggle_visibility_ks_selected = self.keyboard_shortcuts_config_yaml['KEYBOARD_SHORTCUTS'][1]['shortcut'] 
       self.undo_ks_selected = self.keyboard_shortcuts_config_yaml['KEYBOARD_SHORTCUTS'][2]['shortcut'] 
       self.save_seg_ks_selected = self.keyboard_shortcuts_config_yaml['KEYBOARD_SHORTCUTS'][3]['shortcut'] 
       self.smooth_ks_selected = self.keyboard_shortcuts_config_yaml['KEYBOARD_SHORTCUTS'][4]['shortcut'] 
       self.remove_small_holes_ks_selected = self.keyboard_shortcuts_config_yaml['KEYBOARD_SHORTCUTS'][5]['shortcut'] 
       self.interpolate_ks_selected = self.keyboard_shortcuts_config_yaml['KEYBOARD_SHORTCUTS'][6]['shortcut'] 

   def segmentation_checkbox_state_changed(self):
       self.segmentation_selected = self.segmentation_task_checkbox.isChecked()

       if self.segmentation_task_checkbox.isChecked():
            self.configure_labels_button.setEnabled(True)

            if self.modality_selected == 'CT':
                self.include_semi_automatic_PHE_tool_combobox.setEnabled(True)
            else:
                self.include_semi_automatic_PHE_tool_combobox.setEnabled(False)
       else: 
            self.configure_labels_button.setEnabled(False)

            self.include_semi_automatic_PHE_tool_combobox.setEnabled(False)
   
   def update_interpolate_ks(self):
       self.interpolate_ks_selected = self.interpolate_ks_line_edit.text
   
   def update_remove_small_holes_ks(self):
       self.remove_small_holes_ks_selected = self.remove_small_holes_ks_line_edit.text
   
   def update_smooth_ks(self):
       self.smooth_ks_selected = self.smooth_ks_line_edit.text

   def update_save_seg_ks(self):
       self.save_seg_ks_selected = self.save_seg_ks_line_edit.text
   
   def update_undo_ks(self):
       self.undo_ks_selected = self.undo_ks_line_edit.text
   
   def update_toggle_visibility_ks(self):
       self.toggle_visibility_ks_selected = self.toggle_visibility_ks_line_edit.text
   
   def update_toggle_fill_ks(self):
       self.toggle_fill_ks_selected = self.toggle_fill_ks_line_edit.text
   
   def update_ct_window_width(self):
       self.ct_window_width_selected = self.ct_window_width_line_edit.text
   
   def update_ct_window_level(self):
       self.ct_window_level_selected = self.ct_window_level_line_edit.text
   
   def update_interpolate(self):
       if self.interpolate_combobox.currentText == 'Yes':
           self.interpolate_selected = 1
       else:
           self.interpolate_selected = 0
   
   def update_initial_view(self):
       self.initial_view_selected = self.initial_view_combobox.currentText
   
   def update_file_extension(self):
       self.file_extension_selected = self.file_extension_combobox.currentText
   
   def update_bids(self):
       self.bids_selected = self.bids_combobox.currentText
   
   def update_include_semi_automatic_PHE_tool(self):
       self.include_semi_auto_PHE_tool_selected_option = self.include_semi_automatic_PHE_tool_combobox.currentText
   
   def update_selected_modality(self, option):
       self.modality_selected = option

       if self.modality_selected == 'CT':
            self.bids_combobox.setEnabled(False)

            self.ct_window_level_line_edit.setEnabled(True)
            self.ct_window_width_line_edit.setEnabled(True)

            self.include_semi_automatic_PHE_tool_combobox.setEnabled(self.segmentation_selected)
       else:
            self.bids_combobox.setEnabled(True)

            self.ct_window_level_line_edit.setEnabled(False)
            self.ct_window_width_line_edit.setEnabled(False)

            self.include_semi_automatic_PHE_tool_combobox.setEnabled(False)
   
   def push_configure_labels(self):
       configureLabelsWindow = ConfigureLabelsWindow(self.segmenter, self.modality_selected)
       configureLabelsWindow.show()
   
   def push_previous(self):
       slicerCART_configuration_initial_window = SlicerCARTConfigurationInitialWindow(self.segmenter)
       slicerCART_configuration_initial_window.show()
       self.close()
   
   def push_apply(self):
       self.general_config_yaml['is_segmentation_requested'] = self.segmentation_task_checkbox.isChecked()
       self.general_config_yaml['is_classification_requested'] = self.classification_task_checkbox.isChecked()
       self.general_config_yaml['modality'] = self.modality_selected

       if self.include_semi_auto_PHE_tool_selected_option == 'Yes':
           self.general_config_yaml['is_semi_automatic_phe_tool_requested'] = True 
       elif self.include_semi_auto_PHE_tool_selected_option == 'No':
           self.general_config_yaml['is_semi_automatic_phe_tool_requested'] = False 
    
       if self.bids_selected == 'Yes':
           self.general_config_yaml['impose_bids_format'] = True
       elif self.bids_selected == 'No':
           self.general_config_yaml['impose_bids_format'] = False
    
       self.general_config_yaml['input_filetype'] = self.file_extension_selected

       self.general_config_yaml['interpolate_value'] = self.interpolate_selected
       
       if 'Red' in self.initial_view_selected:
           self.general_config_yaml['slice_view_color'] = 'Red'
       elif 'Yellow' in self.initial_view_selected:
           self.general_config_yaml['slice_view_color'] = 'Yellow'
       elif 'Green' in self.initial_view_selected:
           self.general_config_yaml['slice_view_color'] = 'Green'
    
       self.general_config_yaml['ct_window_level'] = int(self.ct_window_level_selected)
       self.general_config_yaml['ct_window_width'] = int(self.ct_window_width_selected)

       self.keyboard_shortcuts_config_yaml['KEYBOARD_SHORTCUTS'][0]['shortcut'] = self.toggle_fill_ks_selected
       self.keyboard_shortcuts_config_yaml['KEYBOARD_SHORTCUTS'][1]['shortcut'] = self.toggle_visibility_ks_selected
       self.keyboard_shortcuts_config_yaml['KEYBOARD_SHORTCUTS'][2]['shortcut'] = self.undo_ks_selected
       self.keyboard_shortcuts_config_yaml['KEYBOARD_SHORTCUTS'][3]['shortcut'] = self.save_seg_ks_selected
       self.keyboard_shortcuts_config_yaml['KEYBOARD_SHORTCUTS'][4]['shortcut'] = self.smooth_ks_selected
       self.keyboard_shortcuts_config_yaml['KEYBOARD_SHORTCUTS'][5]['shortcut'] = self.remove_small_holes_ks_selected
       self.keyboard_shortcuts_config_yaml['KEYBOARD_SHORTCUTS'][6]['shortcut'] = self.interpolate_ks_selected

       with open(GENERAL_CONFIG_FILE_PATH, 'w') as file:   
            yaml.safe_dump(self.general_config_yaml, file)
       with open(KEYBOARD_SHORTCUTS_CONFIG_FILE_PATH, 'w') as file:   
            yaml.safe_dump(self.keyboard_shortcuts_config_yaml, file)

       self.segmenter.setup_configuration()
       self.close()

   def push_cancel(self):
       msg = qt.QMessageBox()
       msg.setWindowTitle('Informative Message')
       msg.setText('Using default configurations. To select a different configuration, restart the application. ')
       msg.exec()

       self.segmenter.setup_configuration()
       self.close()
class ConfigureLabelsWindow(qt.QWidget):
   def __init__(self, segmenter, modality, label_config_yaml = None, parent = None):
      super(ConfigureLabelsWindow, self).__init__(parent)

      self.segmenter = segmenter
      self.modality = modality

      if label_config_yaml is None:
            with open(LABEL_CONFIG_FILE_PATH, 'r') as file:
                    self.label_config_yaml = yaml.full_load(file)
      else:
          self.label_config_yaml = label_config_yaml

      layout = qt.QVBoxLayout()

      self.label_table_view = qt.QTableWidget()
      layout.addWidget(self.label_table_view)

      self.versionCheckboxWidgets = {}

      if len(self.label_config_yaml['labels']) > 0:
          number_of_available_labels = len(self.label_config_yaml['labels'])

          self.label_table_view.setRowCount(number_of_available_labels)
          if self.modality == 'MRI':
                self.label_table_view.setColumnCount(5) # edit button, remove button, name, value, color
          elif self.modality == 'CT':
                self.label_table_view.setColumnCount(7) # edit button, remove button, name, value, color, range HU min, range HU max
          self.label_table_view.horizontalHeader().setStretchLastSection(True)
          self.label_table_view.horizontalHeader().setSectionResizeMode(qt.QHeaderView.Stretch)

          for index, label in enumerate(self.label_config_yaml['labels']): 
                # TODO Delph LIVE : QIntValidator not working???
                edit_button = qt.QPushButton('Edit')
                edit_button.clicked.connect(lambda state, label = label: self.push_edit_button(label))
                edit_button_hbox = qt.QHBoxLayout()
                edit_button_hbox.addWidget(edit_button)
                edit_button_hbox.setAlignment(qt.Qt.AlignCenter)
                edit_button_hbox.setContentsMargins(0, 0, 0, 0)
                edit_button_widget = qt.QWidget()
                edit_button_widget.setLayout(edit_button_hbox)
                self.label_table_view.setCellWidget(index, 0, edit_button_widget)
                self.label_table_view.setHorizontalHeaderItem(0, qt.QTableWidgetItem(''))

                remove_button = qt.QPushButton('Remove')
                remove_button.clicked.connect(lambda state, label = label: self.push_remove_button(label))
                remove_button_hbox = qt.QHBoxLayout()
                remove_button_hbox.addWidget(remove_button)
                remove_button_hbox.setAlignment(qt.Qt.AlignCenter)
                remove_button_hbox.setContentsMargins(0, 0, 0, 0)
                remove_button_widget = qt.QWidget()
                remove_button_widget.setLayout(remove_button_hbox)
                self.label_table_view.setCellWidget(index, 1, remove_button_widget)
                self.label_table_view.setHorizontalHeaderItem(1, qt.QTableWidgetItem(''))

                cell = qt.QTableWidgetItem(label['name'])
                cell.setFlags(qt.Qt.NoItemFlags)
                cell.setForeground(qt.QBrush(qt.QColor(0, 0, 0)))
                self.label_table_view.setItem(index, 2, cell)
                self.label_table_view.setHorizontalHeaderItem(2, qt.QTableWidgetItem('Name'))

                cell = qt.QTableWidgetItem(str(label['value']))
                cell.setFlags(qt.Qt.NoItemFlags)
                cell.setForeground(qt.QBrush(qt.QColor(0, 0, 0)))
                self.label_table_view.setItem(index, 3, cell)
                self.label_table_view.setHorizontalHeaderItem(3, qt.QTableWidgetItem('Value'))

                cell = qt.QTableWidgetItem('')
                cell.setFlags(qt.Qt.NoItemFlags)
                cell.setBackground(qt.QBrush(qt.QColor(label['color_r'], label['color_g'], label['color_b'])))
                self.label_table_view.setItem(index, 4, cell)
                self.label_table_view.setHorizontalHeaderItem(4, qt.QTableWidgetItem('Colour'))

                if self.modality == 'CT':
                    cell = qt.QTableWidgetItem(str(label['lower_bound_HU']))
                    cell.setFlags(qt.Qt.NoItemFlags)
                    cell.setForeground(qt.QBrush(qt.QColor(0, 0, 0)))
                    self.label_table_view.setItem(index, 5, cell)
                    self.label_table_view.setHorizontalHeaderItem(5, qt.QTableWidgetItem('Min. HU'))

                    cell = qt.QTableWidgetItem(str(label['upper_bound_HU']))
                    cell.setFlags(qt.Qt.NoItemFlags)
                    cell.setForeground(qt.QBrush(qt.QColor(0, 0, 0)))
                    self.label_table_view.setItem(index, 6, cell)
                    self.label_table_view.setHorizontalHeaderItem(6, qt.QTableWidgetItem('Max. HU'))

      self.add_label_button = qt.QPushButton('Add Label')
      self.add_label_button.clicked.connect(self.push_add_label)
      layout.addWidget(self.add_label_button)

      self.save_button = qt.QPushButton('Save')
      self.save_button.clicked.connect(self.push_save)
      layout.addWidget(self.save_button)

      self.cancel_button = qt.QPushButton('Cancel')
      self.cancel_button.clicked.connect(self.push_cancel)
      layout.addWidget(self.cancel_button)

      self.setLayout(layout)
      self.setWindowTitle("Configure Labels")
      self.resize(800, 200)

   def push_edit_button(self, label):
       self.close()

       configureSingleLabelWindow = ConfigureSingleLabelWindow(self.segmenter, self.modality, self.label_config_yaml, label)
       configureSingleLabelWindow.show()

   def push_remove_button(self, label):
       self.close()
       
       value_removed = -1
       for l in self.label_config_yaml['labels']:
           if l['name'] == label['name']:
               value_removed = l['value']
               self.label_config_yaml['labels'].remove(l)
    
       for l in self.label_config_yaml['labels']:
           if l['value'] > value_removed and value_removed != -1:
               l['value'] = l['value'] - 1
        
       configureLabelsWindow = ConfigureLabelsWindow(self.segmenter, self.modality, self.label_config_yaml)
       configureLabelsWindow.show()

   def push_add_label(self):
       self.close()

       configureSingleLabelWindow = ConfigureSingleLabelWindow(self.segmenter, self.modality, self.label_config_yaml)
       configureSingleLabelWindow.show()
   
   def push_save(self):
       with open(LABEL_CONFIG_FILE_PATH, 'w') as file:   
           yaml.safe_dump(self.label_config_yaml, file)

       self.close()

   def push_cancel(self):
       self.close()

class ConfigureSingleLabelWindow(qt.QWidget):
   def __init__(self, segmenter, modality, label_config_yaml, label = None, parent = None):
      super(ConfigureSingleLabelWindow, self).__init__(parent)

      self.segmenter = segmenter
      self.modality = modality
      self.initial_label = label
      self.label_config_yaml = label_config_yaml

      layout = qt.QVBoxLayout()

      name_hbox = qt.QHBoxLayout()

      name_label = qt.QLabel('Name : ')
      name_label.setStyleSheet("font-weight: bold")
      name_hbox.addWidget(name_label)

      self.name_line_edit = qt.QLineEdit('')
      name_hbox.addWidget(self.name_line_edit)
      
      layout.addLayout(name_hbox)

      value_hbox = qt.QHBoxLayout()

      value_label = qt.QLabel('Value : ')
      value_label.setStyleSheet("font-weight: bold")
      value_hbox.addWidget(value_label)

      self.value_line_edit = qt.QLineEdit('')
      self.value_line_edit.setValidator(qt.QIntValidator())
      self.value_line_edit.setEnabled(False) # To be changed at resolution of Issue #28
      value_hbox.addWidget(self.value_line_edit)
      
      layout.addLayout(value_hbox)

      color_hbox = qt.QHBoxLayout()

      color_label = qt.QLabel('Colour : ')
      color_label.setStyleSheet("font-weight: bold")
      color_hbox.addWidget(color_label)

      self.color_r_line_edit = qt.QLineEdit('R')
      colorValidator = qt.QIntValidator()
      colorValidator.setRange(0, 255)
      self.color_r_line_edit.setValidator(colorValidator)
      self.color_r_line_edit.textChanged.connect(self.color_line_edit_changed)
      color_hbox.addWidget(self.color_r_line_edit)

      self.color_g_line_edit = qt.QLineEdit('G')
      self.color_g_line_edit.setValidator(colorValidator)
      self.color_g_line_edit.textChanged.connect(self.color_line_edit_changed)
      color_hbox.addWidget(self.color_g_line_edit)

      self.color_b_line_edit = qt.QLineEdit('B')
      self.color_b_line_edit.setValidator(colorValidator)
      self.color_b_line_edit.textChanged.connect(self.color_line_edit_changed)
      color_hbox.addWidget(self.color_b_line_edit)

      self.color_display = qt.QLabel('        ')
      color_hbox.addWidget(self.color_display)

      layout.addLayout(color_hbox)

      if self.modality == 'CT':
            min_hu_hbox = qt.QHBoxLayout()

            min_hu_label = qt.QLabel('Min. HU : ')
            min_hu_label.setStyleSheet("font-weight: bold")
            min_hu_hbox.addWidget(min_hu_label)

            self.min_hu_line_edit = qt.QLineEdit('')
            self.min_hu_line_edit.setValidator(qt.QIntValidator())
            min_hu_hbox.addWidget(self.min_hu_line_edit)
            
            layout.addLayout(min_hu_hbox)

            max_hu_hbox = qt.QHBoxLayout()

            max_hu_label = qt.QLabel('Max. HU : ')
            max_hu_label.setStyleSheet("font-weight: bold")
            max_hu_hbox.addWidget(max_hu_label)

            self.max_hu_line_edit = qt.QLineEdit('')
            self.max_hu_line_edit.setValidator(qt.QIntValidator())
            max_hu_hbox.addWidget(self.max_hu_line_edit)
            
            layout.addLayout(max_hu_hbox)

      if self.initial_label is not None:
          self.name_line_edit.setText(self.initial_label['name'])
          self.name_line_edit.setEnabled(False)
          self.value_line_edit.setText(self.initial_label['value'])
          self.color_r_line_edit.setText(label['color_r'])
          self.color_g_line_edit.setText(label['color_g'])
          self.color_b_line_edit.setText(label['color_b'])
          self.color_line_edit_changed()

          if self.modality == 'CT':
              self.min_hu_line_edit.setText(self.initial_label['lower_bound_HU'])
              self.max_hu_line_edit.setText(self.initial_label['upper_bound_HU'])

      self.save_button = qt.QPushButton('Save')
      self.save_button.clicked.connect(self.push_save)
      layout.addWidget(self.save_button)

      self.cancel_button = qt.QPushButton('Cancel')
      self.cancel_button.clicked.connect(self.push_cancel)
      layout.addWidget(self.cancel_button)

      self.setLayout(layout)
      self.setWindowTitle("Configure Label")
      self.resize(400, 200)
   
   def color_line_edit_changed(self):
       # (R, G, B)
       color = f'({self.color_r_line_edit.text},{self.color_g_line_edit.text},{self.color_b_line_edit.text})'
       self.color_display.setStyleSheet(f"background-color:rgb{color}")
   
   def push_save(self):
       current_label_name = self.name_line_edit.text
    
       label_found = False
       for label in self.label_config_yaml['labels']:
           if label['name'] == current_label_name:
               # edit 
               label_found = True
               label['color_r'] = int(self.color_r_line_edit.text)
               label['color_g'] = int(self.color_g_line_edit.text)
               label['color_b'] = int(self.color_b_line_edit.text)

               if self.modality == 'CT':
                   label['lower_bound_HU'] = int(self.min_hu_line_edit.text)
                   label['upper_bound_HU'] = int(self.max_hu_line_edit.text)
               
       if label_found == False:
           # append
           new_label = copy.deepcopy(self.label_config_yaml['labels'][0])
           new_label['name'] = self.name_line_edit.text
           new_label['value'] = len(self.label_config_yaml['labels']) + 1
           new_label['color_r'] = int(self.color_r_line_edit.text)
           new_label['color_g'] = int(self.color_g_line_edit.text)
           new_label['color_b'] = int(self.color_b_line_edit.text)

           if self.modality == 'CT':
                new_label['lower_bound_HU'] = int(self.min_hu_line_edit.text)
                new_label['upper_bound_HU'] = int(self.max_hu_line_edit.text)
           self.label_config_yaml['labels'].append(new_label)
        
       configureLabelsWindow = ConfigureLabelsWindow(self.segmenter, self.modality, self.label_config_yaml)
       configureLabelsWindow.show()
       self.close() 
       
   def push_cancel(self):
       configureLabelsWindow = ConfigureLabelsWindow(self.segmenter, self.modality, self.label_config_yaml)
       configureLabelsWindow.show()
       self.close()

class LoadClassificationWindow(qt.QWidget):
   def __init__(self, segmenter, classificationInformation_df, parent = None):
      super(LoadClassificationWindow, self).__init__(parent)

      self.classificationInformation_df = classificationInformation_df
      self.segmenter = segmenter

      layout = qt.QVBoxLayout()
      self.versionTableView = qt.QTableWidget()
      layout.addWidget(self.versionTableView)

      buttonLayout = qt.QHBoxLayout()

      versionLabel = qt.QLabel()
      versionLabel.setText('Classification version to load: ')
      versionLabel.setStyleSheet("font-weight: bold")
      buttonLayout.addWidget(versionLabel)

      self.versionDropdown = qt.QComboBox()
      buttonLayout.addWidget(self.versionDropdown)

      layout.addLayout(buttonLayout)

      if classificationInformation_df.shape[0] > 0:
          available_versions = classificationInformation_df['Classification version'].to_list()
          for v in available_versions:
              self.versionDropdown.addItem(v)

          self.versionTableView.setRowCount(len(available_versions))
          self.versionTableView.setColumnCount(4)
          self.versionTableView.horizontalHeader().setStretchLastSection(True)
          self.versionTableView.horizontalHeader().setSectionResizeMode(qt.QHeaderView.Stretch)

          for index, row in classificationInformation_df.iterrows():
                cell = qt.QTableWidgetItem(row['Classification version'])
                cell.setFlags(qt.Qt.NoItemFlags)
                cell.setForeground(qt.QBrush(qt.QColor(0, 0, 0)))
                self.versionTableView.setItem(index, 0, cell)
                self.versionTableView.setHorizontalHeaderItem(0, qt.QTableWidgetItem('Version'))

                cell = qt.QTableWidgetItem(row['Annotator Name'])
                cell.setFlags(qt.Qt.NoItemFlags)
                cell.setForeground(qt.QBrush(qt.QColor(0, 0, 0)))
                self.versionTableView.setItem(index, 1, cell)
                self.versionTableView.setHorizontalHeaderItem(1, qt.QTableWidgetItem('Annotator'))

                cell = qt.QTableWidgetItem(row['Annotator degree'])
                cell.setFlags(qt.Qt.NoItemFlags)
                cell.setForeground(qt.QBrush(qt.QColor(0, 0, 0)))
                self.versionTableView.setItem(index, 2, cell)
                self.versionTableView.setHorizontalHeaderItem(2, qt.QTableWidgetItem('Degree'))

                cell = qt.QTableWidgetItem(row['Date and time'])
                cell.setFlags(qt.Qt.NoItemFlags)
                cell.setForeground(qt.QBrush(qt.QColor(0, 0, 0)))
                self.versionTableView.setItem(index, 3, cell)
                self.versionTableView.setHorizontalHeaderItem(3, qt.QTableWidgetItem('Date and Time'))

      self.loadButton = qt.QPushButton('Load')
      self.loadButton.clicked.connect(self.pushLoad)
      layout.addWidget(self.loadButton)

      self.cancelButton = qt.QPushButton('Cancel')
      self.cancelButton.clicked.connect(self.pushCancel)
      layout.addWidget(self.cancelButton)

      self.setLayout(layout)
      self.setWindowTitle("Load Classification")
      self.resize(800, 400)

   def pushLoad(self):
       selected_version = self.versionDropdown.currentText
       selected_version_df = self.classificationInformation_df[self.classificationInformation_df['Classification version']==selected_version].reset_index(drop = True)

       for i, (objectName, label) in enumerate(self.segmenter.classification_config_yaml["checkboxes"].items()):
           if selected_version_df.at[0, label] == 'Yes':
               self.segmenter.checkboxWidgets[objectName].setChecked(True)
           elif selected_version_df.at[0, label] == 'No':
               self.segmenter.checkboxWidgets[objectName].setChecked(False)

       for i, (comboBoxName, options) in enumerate(self.segmenter.classification_config_yaml["comboboxes"].items()):
          self.segmenter.comboboxWidgets[comboBoxName].setCurrentText(selected_version_df.at[0, comboBoxName.replace("_", " ").capitalize()])

       for i, (freeTextBoxObjectName, label) in enumerate(self.segmenter.classification_config_yaml["freetextboxes"].items()):
           saved_text = selected_version_df.at[0, label.capitalize()]
           if str(saved_text) != 'nan':
               self.segmenter.freeTextBoxes[freeTextBoxObjectName].setText(saved_text)
           else:
               self.segmenter.freeTextBoxes[freeTextBoxObjectName].setText("")

       self.close()

   def pushCancel(self):
       self.close()

class ShowSegmentVersionLegendWindow(qt.QWidget):
   def __init__(self, segmenter, segmentationInformation_df, parent = None):
      super(ShowSegmentVersionLegendWindow, self).__init__(parent)

      self.segmentationInformation_df = segmentationInformation_df
      self.segmenter = segmenter

      layout = qt.QVBoxLayout()

      informativeLabel = qt.QLabel()
      informativeLabel.setText(f'Legend of [{self.segmenter.labelOfCompareSegmentVersions}] segment versions')
      layout.addWidget(informativeLabel)

      self.versionTableView = qt.QTableWidget()
      layout.addWidget(self.versionTableView)

      if segmentationInformation_df.shape[0] > 0:

          self.versionTableView.setRowCount(len(self.segmenter.colorsSelectedVersionFilePathsForCompareSegmentVersions))
          self.versionTableView.setColumnCount(5)
          self.versionTableView.horizontalHeader().setStretchLastSection(True)
          self.versionTableView.horizontalHeader().setSectionResizeMode(qt.QHeaderView.Stretch)

          for index, row in segmentationInformation_df.iterrows():
                currentColor = None
                for (segment_name, color) in self.segmenter.colorsSelectedVersionFilePathsForCompareSegmentVersions.items():
                    if row['Segmentation version'] in segment_name:
                        currentColor = color

                        colorItem = qt.QTableWidgetItem()
                        colorItem.setBackground(qt.QBrush(qt.QColor(currentColor[0], currentColor[1], currentColor[2])))
                        self.versionTableView.setItem(index, 0, colorItem)
                        self.versionTableView.setHorizontalHeaderItem(0, qt.QTableWidgetItem('Color'))

                        cell = qt.QTableWidgetItem(row['Segmentation version'])
                        cell.setFlags(qt.Qt.NoItemFlags)
                        cell.setForeground(qt.QBrush(qt.QColor(0, 0, 0)))
                        self.versionTableView.setItem(index, 1, cell)
                        self.versionTableView.setHorizontalHeaderItem(1, qt.QTableWidgetItem('Version'))

                        cell = qt.QTableWidgetItem(row['Annotator Name'])
                        cell.setFlags(qt.Qt.NoItemFlags)
                        cell.setForeground(qt.QBrush(qt.QColor(0, 0, 0)))
                        self.versionTableView.setItem(index, 2, cell)
                        self.versionTableView.setHorizontalHeaderItem(2, qt.QTableWidgetItem('Annotator'))

                        cell = qt.QTableWidgetItem(row['Annotator degree'])
                        cell.setFlags(qt.Qt.NoItemFlags)
                        cell.setForeground(qt.QBrush(qt.QColor(0, 0, 0)))
                        self.versionTableView.setItem(index, 3, cell)
                        self.versionTableView.setHorizontalHeaderItem(3, qt.QTableWidgetItem('Degree'))

                        cell = qt.QTableWidgetItem(row['Date and time'])
                        cell.setFlags(qt.Qt.NoItemFlags)
                        cell.setForeground(qt.QBrush(qt.QColor(0, 0, 0)))
                        self.versionTableView.setItem(index, 4, cell)
                        self.versionTableView.setHorizontalHeaderItem(4, qt.QTableWidgetItem('Date and Time'))

      self.cancelButton = qt.QPushButton('Done')
      self.cancelButton.clicked.connect(self.pushCancel)
      layout.addWidget(self.cancelButton)

      self.setLayout(layout)
      self.setWindowTitle("Legend of Segment Versions")
      self.resize(800, 200)

   def pushCancel(self):
       self.close()

class CompareSegmentVersionsWindow(qt.QWidget):
   def __init__(self, segmenter, segmentationInformation_df, parent = None):
      super(CompareSegmentVersionsWindow, self).__init__(parent)

      self.segmentationInformation_df = segmentationInformation_df

      self.segmenter = segmenter

      layout = qt.QVBoxLayout()

      informativeLabel = qt.QLabel()
      informativeLabel.setText('READ ONLY feature. Please use the Load Segmentation button to modify an existing segmentation.')
      layout.addWidget(informativeLabel)

      self.versionTableView = qt.QTableWidget()
      layout.addWidget(self.versionTableView)

      buttonLayout = qt.QHBoxLayout()

      labelLabel = qt.QLabel()
      labelLabel.setText('Label of interest for comparison ')
      labelLabel.setStyleSheet("font-weight: bold")
      buttonLayout.addWidget(labelLabel)

      self.labelDropdown = qt.QComboBox()
      for label in self.segmenter.label_config_yaml['labels']:
          self.labelDropdown.addItem(label['name'])
      buttonLayout.addWidget(self.labelDropdown)

      layout.addLayout(buttonLayout)

      self.versionCheckboxWidgets = {}

      if segmentationInformation_df.shape[0] > 0:
          available_versions = segmentationInformation_df['Segmentation version'].to_list()

          self.versionTableView.setRowCount(len(available_versions))
          self.versionTableView.setColumnCount(5)
          self.versionTableView.horizontalHeader().setStretchLastSection(True)
          self.versionTableView.horizontalHeader().setSectionResizeMode(qt.QHeaderView.Stretch)

          for index, row in segmentationInformation_df.iterrows():
                checkboxItem = qt.QTableWidgetItem()
                checkboxItem.setFlags(qt.Qt.ItemIsUserCheckable | qt.Qt.ItemIsEnabled)
                checkboxItem.setCheckState(qt.Qt.Unchecked)
                checkboxItem.setForeground(qt.QBrush(qt.QColor(0, 0, 0)))
                self.versionTableView.setItem(index, 0, checkboxItem)
                self.versionTableView.setHorizontalHeaderItem(0, qt.QTableWidgetItem('Select'))
                self.versionCheckboxWidgets[index] = checkboxItem

                cell = qt.QTableWidgetItem(row['Segmentation version'])
                cell.setFlags(qt.Qt.NoItemFlags)
                cell.setForeground(qt.QBrush(qt.QColor(0, 0, 0)))
                self.versionTableView.setItem(index, 1, cell)
                self.versionTableView.setHorizontalHeaderItem(1, qt.QTableWidgetItem('Version'))

                cell = qt.QTableWidgetItem(row['Annotator Name'])
                cell.setFlags(qt.Qt.NoItemFlags)
                cell.setForeground(qt.QBrush(qt.QColor(0, 0, 0)))
                self.versionTableView.setItem(index, 2, cell)
                self.versionTableView.setHorizontalHeaderItem(2, qt.QTableWidgetItem('Annotator'))

                cell = qt.QTableWidgetItem(row['Annotator degree'])
                cell.setFlags(qt.Qt.NoItemFlags)
                cell.setForeground(qt.QBrush(qt.QColor(0, 0, 0)))
                self.versionTableView.setItem(index, 3, cell)
                self.versionTableView.setHorizontalHeaderItem(3, qt.QTableWidgetItem('Degree'))

                cell = qt.QTableWidgetItem(row['Date and time'])
                cell.setFlags(qt.Qt.NoItemFlags)
                cell.setForeground(qt.QBrush(qt.QColor(0, 0, 0)))
                self.versionTableView.setItem(index, 4, cell)
                self.versionTableView.setHorizontalHeaderItem(4, qt.QTableWidgetItem('Date and Time'))

      self.viewSegmentsButton = qt.QPushButton('Compare')
      self.viewSegmentsButton.clicked.connect(self.pushViewSegmentsButton)
      layout.addWidget(self.viewSegmentsButton)

      self.cancelButton = qt.QPushButton('Cancel')
      self.cancelButton.clicked.connect(self.pushCancel)
      layout.addWidget(self.cancelButton)

      self.setLayout(layout)
      self.setWindowTitle("[READ ONLY] Compare Segment Versions")
      self.resize(800, 400)

   def pushViewSegmentsButton(self):
       selected_label = self.labelDropdown.currentText
       selected_version_file_paths = {}

       segmentation_file_extension = ""
       if "nii" in INPUT_FILE_EXTENSION:
           segmentation_file_extension = ".nii.gz"
       elif "nrrd" in INPUT_FILE_EXTENSION:
           segmentation_file_extension = ".seg.nrrd"

       for index, row in self.segmentationInformation_df.iterrows():
           if self.versionCheckboxWidgets[index].checkState() > 0:
               selected_version = row['Segmentation version']
               absolute_path_to_segmentation = f'{self.segmenter.currentOutputPath}{os.sep}{self.segmenter.currentVolumeFilename}_{selected_version}{segmentation_file_extension}'
               selected_version_file_paths[f"{selected_label}_{selected_version}_{row['Annotator Name']}"] = absolute_path_to_segmentation

       self.segmenter.compareSegmentVersions(selected_label, selected_version_file_paths)

       self.close()

   def pushCancel(self):
       self.close()

class LoadSegmentationsWindow(qt.QWidget):
   def __init__(self, segmenter, segmentationInformation_df, parent = None):
      super(LoadSegmentationsWindow, self).__init__(parent)

      self.segmentationInformation_df = segmentationInformation_df

      self.segmenter = segmenter

      layout = qt.QVBoxLayout()

      self.versionTableView = qt.QTableWidget()
      layout.addWidget(self.versionTableView)

      buttonLayout = qt.QHBoxLayout()

      versionLabel = qt.QLabel()
      versionLabel.setText('Segmentation version to load: ')
      versionLabel.setStyleSheet("font-weight: bold")
      buttonLayout.addWidget(versionLabel)

      self.versionDropdown = qt.QComboBox()
      buttonLayout.addWidget(self.versionDropdown)

      layout.addLayout(buttonLayout)

      if segmentationInformation_df.shape[0] > 0:
          available_versions = segmentationInformation_df['Segmentation version'].to_list()
          for v in available_versions:
              self.versionDropdown.addItem(v)

          self.versionTableView.setRowCount(len(available_versions))
          self.versionTableView.setColumnCount(4)
          self.versionTableView.horizontalHeader().setStretchLastSection(True)
          self.versionTableView.horizontalHeader().setSectionResizeMode(qt.QHeaderView.Stretch)

          for index, row in segmentationInformation_df.iterrows():
                cell = qt.QTableWidgetItem(row['Segmentation version'])
                cell.setFlags(qt.Qt.NoItemFlags)
                cell.setForeground(qt.QBrush(qt.QColor(0, 0, 0)))
                self.versionTableView.setItem(index, 0, cell)
                self.versionTableView.setHorizontalHeaderItem(0, qt.QTableWidgetItem('Version'))

                cell = qt.QTableWidgetItem(row['Annotator Name'])
                cell.setFlags(qt.Qt.NoItemFlags)
                cell.setForeground(qt.QBrush(qt.QColor(0, 0, 0)))
                self.versionTableView.setItem(index, 1, cell)
                self.versionTableView.setHorizontalHeaderItem(1, qt.QTableWidgetItem('Annotator'))

                cell = qt.QTableWidgetItem(row['Annotator degree'])
                cell.setFlags(qt.Qt.NoItemFlags)
                cell.setForeground(qt.QBrush(qt.QColor(0, 0, 0)))
                self.versionTableView.setItem(index, 2, cell)
                self.versionTableView.setHorizontalHeaderItem(2, qt.QTableWidgetItem('Degree'))

                cell = qt.QTableWidgetItem(row['Date and time'])
                cell.setFlags(qt.Qt.NoItemFlags)
                cell.setForeground(qt.QBrush(qt.QColor(0, 0, 0)))     
                self.versionTableView.setItem(index, 3, cell) 
                self.versionTableView.setHorizontalHeaderItem(3, qt.QTableWidgetItem('Date and Time'))

      self.loadButton = qt.QPushButton('Load')
      self.loadButton.clicked.connect(self.pushLoad)
      layout.addWidget(self.loadButton)

      self.cancelButton = qt.QPushButton('Cancel')
      self.cancelButton.clicked.connect(self.pushCancel)
      layout.addWidget(self.cancelButton)

      self.setLayout(layout)
      self.setWindowTitle("Load Segmentations")
      self.resize(800, 400)

   def pushLoad(self):
       selected_version = self.versionDropdown.currentText 

       segmentation_file_extension = ""
       if "nii" in INPUT_FILE_EXTENSION:
           segmentation_file_extension = ".nii.gz"
       elif "nrrd" in INPUT_FILE_EXTENSION:
           segmentation_file_extension = ".seg.nrrd"

       absolute_path_to_segmentation = f'{self.segmenter.currentOutputPath}{os.sep}{self.segmenter.currentVolumeFilename}_{selected_version}{segmentation_file_extension}'
       self.segmenter.loadSegmentation(absolute_path_to_segmentation)

       self.close()

   def pushCancel(self):
       self.close()

class SemiAutoPheToolThresholdWindow(qt.QWidget):
   def __init__(self, segmenter, parent = None):
      super(SemiAutoPheToolThresholdWindow, self).__init__(parent)
      
      self.segmenter = segmenter
      self.LB_HU_value = segmenter.LB_HU
      self.UB_HU_value = segmenter.UB_HU

      layout = qt.QVBoxLayout()
      self.textLabel = qt.QLabel("Threshold bounds: ")
      self.textLabel.setStyleSheet("font-weight: bold")
      layout.addWidget(self.textLabel)

      self.minimumLabel = qt.QLabel("Minimum")
      layout.addWidget(self.minimumLabel)
      
      self.semiAutoPHE_LB_HU_spinbox = qt.QSpinBox()
      self.semiAutoPHE_LB_HU_spinbox.valueChanged.connect(self.LB_HU_valueChanged)
      layout.addWidget(self.semiAutoPHE_LB_HU_spinbox)
      self.semiAutoPHE_LB_HU_spinbox.setMinimum(-32000)
      self.semiAutoPHE_LB_HU_spinbox.setMaximum(29000)
      self.semiAutoPHE_LB_HU_spinbox.setValue(self.LB_HU_value)

      self.maximumLabel = qt.QLabel("Maximum")
      layout.addWidget(self.maximumLabel)
      
      self.semiAutoPHE_UB_HU_spinbox = qt.QSpinBox()
      self.semiAutoPHE_UB_HU_spinbox.valueChanged.connect(self.UB_HU_valueChanged)
      layout.addWidget(self.semiAutoPHE_UB_HU_spinbox)
      self.semiAutoPHE_UB_HU_spinbox.setMinimum(-32000)
      self.semiAutoPHE_UB_HU_spinbox.setMaximum(29000)
      self.semiAutoPHE_UB_HU_spinbox.setValue(self.UB_HU_value)

      self.continueButton = qt.QPushButton('Continue')
      self.continueButton.clicked.connect(self.pushContinue)
      layout.addWidget(self.continueButton)

      self.cancelButton = qt.QPushButton('Cancel')
      self.cancelButton.clicked.connect(self.pushCancel)
      layout.addWidget(self.cancelButton)

      self.reference_label = qt.QLabel()
      self.reference_label.setText('Volbers, B., Staykov, D., Wagner, I., Dörfler, A., Saake, M., Schwab, S., & Bardutzky, J. (2011). Semi-automatic \n volumetric assessment of perihemorrhagic edema with computed tomography. European journal of neurology, \n 18(11), 1323–1328. https://doi.org/10.1111/j.1468-1331.2011.03395.x')
      layout.addWidget(self.reference_label)

      self.setLayout(layout)
      self.setWindowTitle("Semi-automatic PHE Tool")
      self.resize(400, 200)

   def UB_HU_valueChanged(self):
      self.UB_HU_value = self.semiAutoPHE_UB_HU_spinbox.value
      self.segmenter.ApplyThresholdPHE(self.LB_HU_value, self.UB_HU_value)

   def LB_HU_valueChanged(self):
      self.LB_HU_value = self.semiAutoPHE_LB_HU_spinbox.value
      self.segmenter.ApplyThresholdPHE(self.LB_HU_value, self.UB_HU_value)

   def pushContinue(self):
       self.segmenter.setUpperAndLowerBoundHU(self.LB_HU_value, self.UB_HU_value)
       
       self.instructionsWindow = SemiAutoPheToolInstructionsWindow(self.segmenter)
       self.instructionsWindow.show()
       
       self.close()

   def pushCancel(self):
       self.segmenter.ClearPHESegment()
       self.close()

class SemiAutoPheToolInstructionsWindow(qt.QWidget):
   def __init__(self, segmenter, parent = None):
      super(SemiAutoPheToolInstructionsWindow, self).__init__(parent)
      
      self.segmenter = segmenter

      layout = qt.QVBoxLayout()
      self.textLabel = qt.QLabel("Instructions:")
      self.textLabel.setStyleSheet("font-weight: bold")
      layout.addWidget(self.textLabel)

      self.minimumLabel = qt.QLabel("Click <b>Continue</b> and draw a generous boundary of the ICH and PHE complex. Note that the boundary may be drawn in multiple views. When you are finished drawing the boundary, click on <b>Show Result</b> in the main extension menu. "
                                    + "The HU thresholds and manual fine-tuning of included voxels are left to the annotator\'s discretion. "
                                    + "\n(If a popup message about visibility shows up, click <b>No</b>.)")
      self.minimumLabel.setWordWrap(True)
      layout.addWidget(self.minimumLabel)

      self.continueButton = qt.QPushButton('Continue')
      self.continueButton.clicked.connect(self.pushContinue)
      layout.addWidget(self.continueButton)

      self.cancelButton = qt.QPushButton('Cancel')
      self.cancelButton.clicked.connect(self.pushCancel)
      layout.addWidget(self.cancelButton)

      self.setLayout(layout)
      self.setWindowTitle("Semi-automatic PHE Tool")
      self.resize(400, 200)

   def pushContinue(self):
       self.segmenter.ApplySemiAutomaticThresholdAlgorithm()
       self.close()

   def pushCancel(self):
       self.segmenter.ClearPHESegment()
       self.close()



class OptionalMethods():
    pass




class SlicerCART(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "SlicerCART"  # TODO: make this more human readable by adding spaces
    self.parent.categories = ["Examples"]  # TODO: set categories (folders where the module shows up in the module selector)
    self.parent.dependencies = []  # TODO: add here list of module names that this module requires
    self.parent.contributors = ["Delphine Pilon, An Ni Wu, Emmanuel Montagnon, Maxime Bouthillier, Laurent Letourneau-Guillon"]  # TODO: replace with "Firstname Lastname (Organization)"
    # TODO: update with short description of the module and a link to online module documentation
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#SEGMENTER_v2">module documentation</a>.
"""
    # TODO: replace with organization, grant and thanks
    self.parent.acknowledgementText = """
Module supported by funding from : 
1. Fonds de Recherche du Québec en Santé and Fondation de l’Association des Radiologistes du Québec
Radiology Research funding (299979) and Clinical Research Scholarship–Junior 1 Salary Award (311203)
2. Foundation of the Radiological Society of North America - Seed Grant (RSD2122)
3. Quebec Bio-Imaging Network, 2022 pilot project grant (Project no 21.24)
4. Support professoral du Département de radiologie, radio-oncologie et médecine nucléaire de l’Université de Montréal, Radiology departement  Centre Hospitalier de l’Université de Montréal (CHUM) and CHUM Research Center (CRCHUM) start-up funds

Thanks to the Slicer community for the support and the development of the software.

"""

class Timer():
    def __init__(self, number=None):
        with TIMER_MUTEX:
            self.number = number
            self.total_time = 0
            self.inter_time = 0
            # counting flag to allow to PAUSE the time
            self.flag = False # False = not counting, True = counting (for pause button)


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

# MB CODE BELOW: MOUSE CUSTOMIZATION CLASS
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

class SlicerCARTWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent=None):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.__init__(self, parent)
    VTKObservationMixin.__init__(self)  # needed for parameter node observation
    self.logic = None
    self._parameterNode = None
    self._updatingGUIFromParameterNode = False
    # LLG CODE BELOW
    self.predictions_names= None
    self.DefaultDir = DEFAULT_VOLUMES_DIRECTORY

    # ----- ANW Addition  ----- : Initialize called var to False so the timer only stops once
    self.called = False
    self.called_onLoadSegmentation = False

    # MB
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
  
  def get_keyboard_shortcuts_config_values(self):
      with open(KEYBOARD_SHORTCUTS_CONFIG_FILE_PATH, 'r') as file:
        self.keyboard_config_yaml = yaml.safe_load(file)
  
  def get_classification_config_values(self):
      with open(CLASSIFICATION_CONFIG_FILE_PATH, 'r') as file:
        self.classification_config_yaml = yaml.safe_load(file)

  def get_label_config_values(self):
      with open(LABEL_CONFIG_FILE_PATH, 'r') as file:
        self.label_config_yaml = yaml.safe_load(file)

  def get_general_config_values(self):
      with open(GENERAL_CONFIG_FILE_PATH, 'r') as file:
        self.general_config_yaml = yaml.safe_load(file)

        global INPUT_FILE_EXTENSION
        global DEFAULT_VOLUMES_DIRECTORY
        global DEFAULT_SEGMENTATION_DIRECTORY
        global REQUIRE_VOLUME_DATA_HIERARCHY_BIDS_FORMAT
        global MODALITY
        global IS_CLASSIFICATION_REQUESTED
        global IS_SEGMENTATION_REQUESTED
        global IS_SEMI_AUTOMATIC_PHE_TOOL_REQUESTED
        global INTERPOLATE_VALUE
        global CT_WINDOW_WIDTH
        global CT_WINDOW_LEVEL

        INPUT_FILE_EXTENSION = self.general_config_yaml["input_filetype"]
        DEFAULT_VOLUMES_DIRECTORY = self.general_config_yaml["default_volume_directory"]
        self.DefaultDir = DEFAULT_VOLUMES_DIRECTORY
        DEFAULT_SEGMENTATION_DIRECTORY = self.general_config_yaml["default_segmentation_directory"]
        MODALITY = self.general_config_yaml["modality"]
        IS_CLASSIFICATION_REQUESTED = self.general_config_yaml["is_classification_requested"]
        IS_SEGMENTATION_REQUESTED = self.general_config_yaml["is_segmentation_requested"]
        IS_SEMI_AUTOMATIC_PHE_TOOL_REQUESTED = self.general_config_yaml["is_semi_automatic_phe_tool_requested"]
        INTERPOLATE_VALUE = self.general_config_yaml["interpolate_value"]

        if MODALITY == 'CT':
            # then BIDS not mandatory because it is not yet supported 
            # therefore, either .nrrd or .nii.gz accepted 
            REQUIRE_VOLUME_DATA_HIERARCHY_BIDS_FORMAT = False
            CT_WINDOW_WIDTH = self.general_config_yaml["ct_window_width"]
            CT_WINDOW_LEVEL = self.general_config_yaml["ct_window_level"]

        elif MODALITY == 'MRI':
            # therefore, .nii.gz required  
            INPUT_FILE_EXTENSION = '*.nii.gz'
            # user can decide whether to impose bids or not
            REQUIRE_VOLUME_DATA_HIERARCHY_BIDS_FORMAT = self.general_config_yaml["impose_bids_format"]
            IS_SEMI_AUTOMATIC_PHE_TOOL_REQUESTED = False


  def setup(self):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ### Segment editor widget
    self.layout.setContentsMargins(4, 0, 4, 0)

    ScriptedLoadableModuleWidget.setup(self)

    # Load widget from .ui file (created by Qt Designer).
    # Additional widgets can be instantiated manually and added to self.layout.
    uiWidget = slicer.util.loadUI(self.resourcePath('UI/SlicerCART.ui'))
    self.layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)

    # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
    # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
    # "setMRMLScene(vtkMRMLScene*)" slot.
    uiWidget.setMRMLScene(slicer.mrmlScene)

    # Create logic class. Logic implements all computations that should be possible to run
    # in batch mode, without a graphical user interface.
    self.logic = SlicerCARTLogic()

    slicerCART_configuration_initial_window = SlicerCARTConfigurationInitialWindow(self)
    slicerCART_configuration_initial_window.show()

    self.outputFolder = None
    self.currentCasePath = None
    self.CurrentFolder = None
  
    self.ui.PauseTimerButton.setText('Pause')
    self.ui.SelectVolumeFolder.connect('clicked(bool)', self.onSelectVolumesFolderButton)
    self.ui.SlicerDirectoryListView.clicked.connect(self.getCurrentTableItem)
    self.ui.SaveSegmentationButton.connect('clicked(bool)', self.onSaveSegmentationButton)
    self.ui.SelectOutputFolder.connect('clicked(bool)', self.onSelectOutputFolder)
    self.ui.LoadSegmentation.connect('clicked(bool)', self.onLoadSegmentation)
    self.ui.CompareSegmentVersions.connect('clicked(bool)', self.onCompareSegmentVersions)
    self.ui.LoadClassification.connect('clicked(bool)', self.onLoadClassification)
    self.ui.SaveClassificationButton.connect('clicked(bool)', self.onSaveClassificationButton)
    self.ui.pushButton_Interpolate.connect('clicked(bool)', self.onPushButton_Interpolate)
    self.ui.Previous.connect('clicked(bool)', self.onPreviousButton)
    self.ui.Next.connect('clicked(bool)', self.onNextButton)
    self.ui.pushButton_Paint.connect('clicked(bool)', self.onPushButton_Paint)
    self.ui.LassoPaintButton.connect('clicked(bool)', self.onPushLassoPaint)
    self.ui.pushButton_ToggleVisibility.connect('clicked(bool)', self.onPushButton_ToggleVisibility)
    self.ui.PushButton_segmeditor.connect('clicked(bool)', self.onPushButton_segmeditor)  
    self.ui.pushButton_Erase.connect('clicked(bool)', self.onPushButton_Erase)  
    self.ui.pushButton_Smooth.connect('clicked(bool)', self.onPushButton_Smooth)  
    self.ui.pushButton_Small_holes.connect('clicked(bool)', self.onPushButton_Small_holes)  
    self.ui.pushButton_SemiAutomaticPHE_Launch.connect('clicked(bool)', self.onPushButton_SemiAutomaticPHE_Launch)
    self.ui.pushButton_SemiAutomaticPHE_ShowResult.connect('clicked(bool)', self.onPushButton_SemiAutomaticPHE_ShowResult)
    self.ui.dropDownButton_label_select.currentIndexChanged.connect(self.onDropDownButton_label_select)
    self.ui.PauseTimerButton.connect('clicked(bool)', self.togglePauseTimerButton)
    self.ui.StartTimerButton.connect('clicked(bool)', self.toggleStartTimerButton)
    self.ui.pushButton_ToggleFill.connect('clicked(bool)', self.toggleFillButton)
    self.ui.UB_HU.valueChanged.connect(self.onUB_HU)
    self.ui.LB_HU.valueChanged.connect(self.onLB_HU)
    self.ui.pushDefaultMin.connect('clicked(bool)', self.onPushDefaultMin)
    self.ui.pushDefaultMax.connect('clicked(bool)', self.onPushDefaultMax)
    self.ui.pushButton_undo.connect('clicked(bool)', self.onPushButton_undo)
    self.ui.ShowSegmentVersionLegendButton.connect('clicked(bool)', self.onPush_ShowSegmentVersionLegendButton)
    
    self.ui.ShowSegmentVersionLegendButton.setVisible(False)

    self.ui.pushButton_SemiAutomaticPHE_ShowResult.setEnabled(False)
    self.disablePauseTimerButton()
    self.disableSegmentAndPaintButtons()
    self.ui.pushButton_Interpolate.setEnabled(False)
    self.ui.SaveSegmentationButton.setEnabled(False)

    self.enableStartTimerButton()

    self.ui.LoadClassification.setEnabled(False)
    self.ui.SaveClassificationButton.setEnabled(False)
    self.ui.LoadSegmentation.setEnabled(False)

    self.ui.ThresholdLabel.setStyleSheet("font-weight: bold")
    self.ui.SemiAutomaticPHELabel.setStyleSheet("font-weight: bold")

    self.ui.UB_HU.setMinimum(-32000)
    self.ui.LB_HU.setMinimum(-32000)
    self.ui.UB_HU.setMaximum(29000)
    self.ui.LB_HU.setMaximum(29000)

    self.ui.pushButton_ToggleFill.setStyleSheet("background-color : indianred")
    self.ui.pushButton_ToggleVisibility.setStyleSheet("background-color : yellowgreen")
    self.ui.lcdNumber.setStyleSheet("background-color : black")
    
    self.MostRecentPausedCasePath = ""
  
  def setup_configuration(self):
        self.get_label_config_values()
        self.get_keyboard_shortcuts_config_values()
        self.get_classification_config_values()
        self.get_general_config_values()

        self.LB_HU = self.label_config_yaml["labels"][0]["lower_bound_HU"]
        self.UB_HU = self.label_config_yaml["labels"][0]["upper_bound_HU"]
        
        # Change the value of the upper and lower bound of the HU
        self.ui.UB_HU.setValue(self.UB_HU)
        self.ui.LB_HU.setValue(self.LB_HU)

        comboboxesStartRow = self.setupCheckboxes(3)
        freetextStartRow = self.setupComboboxes(comboboxesStartRow)
        self.setupFreeText(freetextStartRow)
        
        # Initialize timers
        self.timers = []
        timer_index = 0
        for label in self.label_config_yaml["labels"]:
            self.timers.append(Timer(number=timer_index))
            timer_index = timer_index + 1
        
        if not IS_CLASSIFICATION_REQUESTED:
            self.ui.MRMLCollapsibleButton.setVisible(False)
        if not IS_SEGMENTATION_REQUESTED:
            self.ui.MRMLCollapsibleButton_2.setVisible(False)
        if not IS_SEMI_AUTOMATIC_PHE_TOOL_REQUESTED:
            self.ui.SemiAutomaticPHELabel.setVisible(False)
            self.ui.pushButton_SemiAutomaticPHE_Launch.setVisible(False)
            self.ui.pushButton_SemiAutomaticPHE_ShowResult.setVisible(False)
        
        if MODALITY == 'MRI':
            self.ui.ThresholdLabel.setVisible(False)
            self.ui.MinimumLabel.setVisible(False)
            self.ui.MaximumLabel.setVisible(False)
            self.ui.LB_HU.setVisible(False)
            self.ui.UB_HU.setVisible(False)
            self.ui.pushDefaultMin.setVisible(False)
            self.ui.pushDefaultMax.setVisible(False)
        
        for i in self.keyboard_config_yaml["KEYBOARD_SHORTCUTS"]:

            shortcutKey = i.get("shortcut")
            callback_name = i.get("callback")
            button_name = i.get("button")

            button = getattr(self.ui, button_name)
            callback = getattr(self, callback_name)

            self.connectShortcut(shortcutKey, button, callback)
        
        # Display the selected color view at module startup
        if self.general_config_yaml['slice_view_color'] == "Yellow":
            slicer.app.layoutManager().setLayout(
                slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpYellowSliceView)
        if self.general_config_yaml['slice_view_color'] == "Red":
            slicer.app.layoutManager().setLayout(
                slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpRedSliceView)
        if self.general_config_yaml['slice_view_color'] == "Green":
            slicer.app.layoutManager().setLayout(
                slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpGreenSliceView)

        for label in self.label_config_yaml["labels"]:
            self.ui.dropDownButton_label_select.addItem(label["name"])
  
  def set_master_volume_intensity_mask_according_to_modality(self):
      if MODALITY == 'CT':
            self.segmentEditorNode.SetMasterVolumeIntensityMask(True)
      elif MODALITY == 'MRI':
            self.segmentEditorNode.SetMasterVolumeIntensityMask(False)
  
  def setupCheckboxes(self, number_of_columns):
      self.checkboxWidgets = {}

      for i, (objectName, label) in enumerate(self.classification_config_yaml["checkboxes"].items()):
        print(objectName, label)
        checkbox = qt.QCheckBox()
        checkbox.setText(label)
        checkbox.setObjectName(objectName)

        row_index = i / number_of_columns + 1
        column_index = i % number_of_columns

        self.ui.ClassificationGridLayout.addWidget(checkbox, row_index, column_index)
        self.checkboxWidgets[objectName] = checkbox


      return row_index + 1
  
  def setupComboboxes(self, start_row):
      self.comboboxWidgets = {}
      
      row_index = start_row
      for i, (comboBoxName, options) in enumerate(self.classification_config_yaml["comboboxes"].items()):
        comboboxLabel = qt.QLabel(comboBoxName.replace("_", " ").capitalize() + " :")
        comboboxLabel.setStyleSheet("font-weight: bold")
        self.ui.ClassificationGridLayout.addWidget(comboboxLabel, row_index, 0)
        
        combobox = qt.QComboBox()
        combobox.setObjectName(comboBoxName)
        for optionKey, optionLabel in options.items():
            combobox.addItem(optionLabel, optionKey)
        self.ui.ClassificationGridLayout.addWidget(combobox, row_index, 1)
        self.comboboxWidgets[comboBoxName] = combobox 
        row_index = row_index + 1
      return row_index + 1
  
  def setupFreeText(self, start_row):
      self.freeTextBoxes = {}

      row_index = start_row
      for i, (freeTextObjectName, freeTextLabel) in enumerate(self.classification_config_yaml["freetextboxes"].items()):
          freeTextQLabel = qt.QLabel(freeTextLabel.capitalize() + " :")
          freeTextQLabel.setStyleSheet("font-weight: bold")
          self.ui.ClassificationGridLayout.addWidget(freeTextQLabel, row_index, 0)
          lineEdit = qt.QLineEdit()
          self.freeTextBoxes[freeTextObjectName] = lineEdit
          self.ui.ClassificationGridLayout.addWidget(lineEdit, row_index, 1)
          row_index = row_index + 1

  def connectShortcut(self, shortcutKey, button, callback):
      shortcut = qt.QShortcut(slicer.util.mainWindow())
      shortcut.setKey(qt.QKeySequence(shortcutKey))
      shortcut.connect("activated()", lambda: self.toggleKeyboardShortcut(button, callback))
      return shortcut
  
  def toggleKeyboardShortcut(self, button, callback):
      button.toggle()
      callback()
  
  def setUpperAndLowerBoundHU(self, inputLB_HU, inputUB_HU):
      self.LB_HU = inputLB_HU
      self.UB_HU = inputUB_HU
      self.ui.UB_HU.setValue(self.UB_HU)
      self.ui.LB_HU.setValue(self.LB_HU)
  
  def enableSegmentAndPaintButtons(self):
    self.ui.pushButton_Paint.setEnabled(True)
    self.ui.LassoPaintButton.setEnabled(True)
    self.ui.pushButton_Erase.setEnabled(True)
    self.ui.pushButton_SemiAutomaticPHE_Launch.setEnabled(True)

  def disableSegmentAndPaintButtons(self):
    self.ui.pushButton_Paint.setEnabled(False)
    self.ui.LassoPaintButton.setEnabled(False)
    self.ui.pushButton_SemiAutomaticPHE_Launch.setEnabled(False)
    self.ui.pushButton_SemiAutomaticPHE_ShowResult.setEnabled(False)
    self.ui.pushButton_Erase.setEnabled(False)

  def onSelectVolumesFolderButton(self):
      self.CurrentFolder= qt.QFileDialog.getExistingDirectory(None,"Open a folder", self.DefaultDir, qt.QFileDialog.ShowDirsOnly)

      file_structure_valid = True
      if REQUIRE_VOLUME_DATA_HIERARCHY_BIDS_FORMAT == True:
          file_structure_valid = self.validateBIDS(self.CurrentFolder)
    
      if file_structure_valid == False:
          return # don't load any patient cases

      self.CasesPaths = sorted(glob(f'{self.CurrentFolder}{os.sep}**{os.sep}{INPUT_FILE_EXTENSION}', recursive = True))

      if not self.CasesPaths:
            msg_box = qt.QMessageBox()
            msg_box.setWindowTitle("No files found")
            msg_box.setIcon(qt.QMessageBox.Warning)
            text = "No files found in the selected directory!"
            text += "\n\nMake sure the configured extension is in the right format."
            text += "\n\nThen restart the module"
            msg_box.setText(text)
            msg_box.exec()
            return

      self.Cases = sorted([os.path.split(i)[-1] for i in self.CasesPaths])

      self.ui.SlicerDirectoryListView.clear()
      self.ui.SlicerDirectoryListView.addItems(self.Cases)

      self.ui.pushButton_Interpolate.setEnabled(True)

      self.currentCase_index = 0 # THIS IS THE CENTRAL THING THAT HELPS FOR CASE NAVIGATION
      self.updateCaseAll()
      self.loadPatient()

  def validateBIDS(self, path):
        validator = BIDSValidator()
        is_structure_valid = True
        class InvalidBIDS(Exception): pass

        try:
            for subdir, dirs, files in os.walk(path):
                for file in files:
                    if file.endswith(INPUT_FILE_EXTENSION.split("*")[1]):
                        try:
                            path = "/sub" + (subdir + "/" + file).split("/sub", 1)[1]
                            is_valid = validator.is_bids(path)
                        except:
                            raise InvalidBIDS

                        if is_valid == False:
                            raise InvalidBIDS
        except InvalidBIDS:
            msg_box = qt.QMessageBox()
            msg_box.setWindowTitle("BIDS Validation")
            msg_box.setText("File hierarchy not in proper BIDS format. \n\nInformation : https://bids.neuroimaging.io \n\nTool : https://bids-standard.github.io/bids-validator")
            msg_box.exec()

            is_structure_valid = False

        return is_structure_valid

  def updateCaseAll(self):
      # All below is dependent on self.currentCase_index updates, 
      self.currentCase = self.Cases[self.currentCase_index]
      self.currentCasePath = self.CasesPaths[self.currentCase_index]
      self.updateCurrentPatient()
      # Highlight the current case in the list view (when pressing on next o)
      self.ui.SlicerDirectoryListView.setCurrentItem(self.ui.SlicerDirectoryListView.item(self.currentCase_index))
      
  def getCurrentTableItem(self):
      # ----- ANW Addition ----- : Reset timer when change case and uncheck all checkboxes
      self.resetTimer()
      self.resetClassificationInformation()

      # When an item in SlicerDirectroyListView is selected the case number is printed
      # below we update the case index and we need to pass one parameter to the methods since it takes 2 (1 in addition to self)
      self.updateCaseIndex(self.ui.SlicerDirectoryListView.currentRow) # Index starts at 0
      # Update the case index
      self.currentCase_index = self.ui.SlicerDirectoryListView.currentRow
      # Same code in onBrowseFoldersButton, need to update self.currentCase
      # note that updateCaseAll() not implemented here - it is called when a case is selected from the list view or next/previous button is clicked
      self.currentCase = self.Cases[self.currentCase_index]
      self.currentCasePath = self.CasesPaths[self.currentCase_index]
      self.updateCurrentPatient()
      self.loadPatient()
      
      # ----- ANW Addition ----- : Reset timer when change case, also reset button status
      self.resetTimer()

  def updateCaseIndex(self, index):
      # ----- ANW Modification ----- : Numerator on UI should start at 1 instead of 0 for coherence
      self.ui.FileIndex.setText('{} / {}'.format(index+1, len(self.Cases)))
      
  def updateCurrentPatient(self):
      self.updateCaseIndex(self.currentCase_index)
  
  def updateCurrentPath(self):
      self.ui.CurrentPath.setReadOnly(True)
      self.ui.CurrentPath.setText(self.currentCasePath)
      
  def loadPatient(self):
      timer_index = 0
      self.timers = []
      for label in self.label_config_yaml["labels"]:
          self.timers.append(Timer(number = timer_index))
          timer_index = timer_index + 1
      
      # reset dropbox to index 0
      self.ui.dropDownButton_label_select.setCurrentIndex(0)
      
      # timer reset if we come back to same case
      self.called = False

      slicer.mrmlScene.Clear()
      slicer.util.loadVolume(self.currentCasePath)
      self.VolumeNode = slicer.util.getNodesByClass('vtkMRMLScalarVolumeNode')[0]
      self.updateCaseAll()
      # Adjust windowing (no need to use self. since this is used locally)
      Vol_displayNode = self.VolumeNode.GetDisplayNode()
      Vol_displayNode.AutoWindowLevelOff()
      Vol_displayNode.SetWindow(CT_WINDOW_WIDTH)
      Vol_displayNode.SetLevel(CT_WINDOW_LEVEL)
      Vol_displayNode.SetInterpolate(INTERPOLATE_VALUE)
      self.newSegmentation()

      self.updateCurrentOutputPathAndCurrentVolumeFilename()
  
  def updateCurrentOutputPathAndCurrentVolumeFilename(self):
      if self.currentCasePath == None or self.CurrentFolder == None or self.outputFolder == None:
          return
      
      i = 0
      relativePath = ''
      for c in self.currentCasePath:
          if i >= len(self.CurrentFolder):
              relativePath = relativePath + c
          i = i + 1

      self.currentOutputPath = os.path.split(self.outputFolder + relativePath)[0]
      self.currentVolumeFilename = os.path.split(self.outputFolder + relativePath)[1].split(".")[0]
  

  # Getter method to get the segmentation node name    - Not sure if this is really useful here. 
  @property
  def segmentationNodeName(self):
    return f"{os.path.split(self.currentCasePath)[1].split('.')[0]}_segmentation"
  
      
  def newSegments(self):
      pass
      
  def onPushButton_NewMask(self):
      self.newSegments()

  def onPushButton_Interpolate(self):
      global INTERPOLATE_VALUE
      INTERPOLATE_VALUE = 1 - INTERPOLATE_VALUE # toggle

      self.VolumeNode.GetDisplayNode().SetInterpolate(INTERPOLATE_VALUE)
            
  def onPreviousButton(self):
      # ----- ANW Addition ----- : Reset timer when change case and uncheck all checkboxes
      self.resetTimer()
      self.resetClassificationInformation()

      #Code below avoid getting in negative values. 
      self.currentCase_index = max(0, self.currentCase_index-1)
      self.updateCaseAll()
      self.loadPatient()


  

  def onNextButton(self):
      # ----- ANW Addition ----- : Reset timer when change case and uncheck all checkboxes
      self.resetTimer()
      self.resetClassificationInformation()

      # ----- ANW Modification ----- : Since index starts at 0, we need to do len(cases)-1 (instead of len(cases)+1).
      # Ex. if we have 10 cases, then len(case)=10 and index goes from 0-9,
      # so we have to take the minimum between len(self.Cases)-1 and the currentCase_index (which is incremented by 1 everytime we click the button)
      self.currentCase_index = min(len(self.Cases)-1, self.currentCase_index+1)
      self.updateCaseAll()
      self.loadPatient()




  def newSegmentation(self):
      # Create segment editor widget and node
      self.segmentEditorWidget = slicer.modules.segmenteditor.widgetRepresentation().self().editor
      self.segmentEditorNode = self.segmentEditorWidget.mrmlSegmentEditorNode()
      # Create segmentation node (keep it local since we add a new segmentation node)
      # Not for reference in other methods
      segmentationNode=slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
      # Set segmentation node name
      segmentationNode.SetName(self.segmentationNodeName)
      # Set segmentation node to segment editor
      self.segmentEditorWidget.setSegmentationNode(segmentationNode)
      # Set master volume node to segment editor
      self.segmentEditorWidget.setSourceVolumeNode(self.VolumeNode)
      # set refenrence geometry to Volume node (important for the segmentation to be in the same space as the volume)
      segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(self.VolumeNode)
      self.createNewSegments() 

      # restart the current timer 
      self.timers[self.current_label_index] = Timer(number=self.current_label_index)
      # reset tool 
      self.segmentEditorWidget.setActiveEffectByName("No editing")
      
  # Load all segments at once    
  def createNewSegments(self):
        for label in self.label_config_yaml["labels"]:
            self.onNewLabelSegm(label["name"], label["color_r"], label["color_g"], label["color_b"], label["lower_bound_HU"], label["upper_bound_HU"])
        
        first_label_name = self.label_config_yaml["labels"][0]["name"]
        first_label_segment_name = first_label_name
        self.onPushButton_select_label(first_label_segment_name, self.label_config_yaml["labels"][0]["lower_bound_HU"], self.label_config_yaml["labels"][0]["upper_bound_HU"])

  def newSegment(self, segment_name=None):
    
      self.segment_name = segment_name
      srcNode = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
      self.srcSegmentation = srcNode.GetSegmentation()
      
      # Below will create a new segment if there are no segments in the segmentation node, avoid overwriting existing segments
      if not self.srcSegmentation.GetSegmentIDs(): # if there are no segments in the segmentation node
        self.segmentationNode=slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
        self.segmentationNode.GetSegmentation().AddEmptySegment(self.segment_name)

      # if there are segments in the segmentation node, check if the segment name is already in the segmentation node
      if any([self.segment_name in i for i in self.srcSegmentation.GetSegmentIDs()]):
            pass
      else:
            self.segmentationNode=slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
            self.segmentationNode.GetSegmentation().AddEmptySegment(self.segment_name)

      return self.segment_name

  def onNewLabelSegm(self, label_name, label_color_r, label_color_g, label_color_b, label_LB_HU, label_UB_HU):
      segment_name = self.newSegment(label_name)  
      self.segmentationNode=slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
      self.segmentationNode.UndoEnabledOn()
      Segmentation = self.segmentationNode.GetSegmentation()
      self.SegmentID = Segmentation.GetSegmentIdBySegmentName(segment_name)
      segment = Segmentation.GetSegment(self.SegmentID)
      segment.SetColor(label_color_r/255,label_color_g/255,label_color_b/255) 
      self.onPushButton_select_label(segment_name, label_LB_HU, label_UB_HU)
   
  def onPushButton_select_label(self, segment_name, label_LB_HU, label_UB_HU):  
      self.segmentationNode=slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
      Segmentation = self.segmentationNode.GetSegmentation()
      self.SegmentID = Segmentation.GetSegmentIdBySegmentName(segment_name)
      self.segmentEditorNode.SetSelectedSegmentID(self.SegmentID)
      self.updateCurrentPath()
      self.LB_HU = label_LB_HU
      self.UB_HU = label_UB_HU
      self.onPushButton_Paint()
  
      if (self.MostRecentPausedCasePath != self.currentCasePath and self.MostRecentPausedCasePath != ""):
        self.timers[self.current_label_index] = Timer(number=self.current_label_index) # new path, new timer
      
      self.timer_router()

  def onPushButton_SemiAutomaticPHE_Launch(self):
      flag_PHE_label_exists = False
      PHE_label = None
      PHE_label_index = 0
      for label in self.label_config_yaml["labels"]:
          if label["name"] == "PHE":
              flag_PHE_label_exists = True 
              PHE_label = label
              break
          PHE_label_index = PHE_label_index + 1
      assert flag_PHE_label_exists

      PHE_segment_name = f"{self.currentCase}_PHE"
      self.onPushButton_select_label(PHE_segment_name, PHE_label["lower_bound_HU"], PHE_label["upper_bound_HU"])
      self.ui.dropDownButton_label_select.setCurrentIndex(PHE_label_index)
      toolWindow = SemiAutoPheToolThresholdWindow(self)
      toolWindow.show()
      
  def onPushButton_SemiAutomaticPHE_ShowResult(self):
      self.segmentationNode.GetDisplayNode().SetVisibility(True)
      self.onPushButton_Erase()
      self.ui.pushButton_SemiAutomaticPHE_ShowResult.setEnabled(False)

  def ApplyThresholdPHE(self, inLB_HU, inUB_HU):
      self.segmentEditorWidget.setActiveEffectByName("Threshold")
      effect = self.segmentEditorWidget.activeEffect()
      effect.setParameter("MinimumThreshold",f"{inLB_HU}")
      effect.setParameter("MaximumThreshold",f"{inUB_HU}")
      effect.self().onApply()

  def ApplySemiAutomaticThresholdAlgorithm(self):
      self.ui.pushButton_SemiAutomaticPHE_ShowResult.setEnabled(True)
      
      self.segmentationNode.GetDisplayNode().SetVisibility(False)

      self.segmentEditorWidget.setActiveEffectByName("Threshold")
      effect = self.segmentEditorWidget.activeEffect()
      effect.setParameter("MinimumThreshold",f"{self.LB_HU}")
      effect.setParameter("MaximumThreshold",f"{self.UB_HU}")
      effect.self().onApply()

      self.segmentEditorWidget.setActiveEffectByName("Scissors")
      effect = self.segmentEditorWidget.activeEffect()
      effect.setParameter("Operation","EraseOutside")
      effect.setParameter("Shape","FreeForm")

  def ClearPHESegment(self):
      flag_PHE_label_exists = False
      PHE_label = None
      PHE_label_index = 0
      for label in self.label_config_yaml["labels"]:
          if label["name"] == "PHE":
              flag_PHE_label_exists = True 
              PHE_label = label
              break
          PHE_label_index = PHE_label_index + 1
      assert flag_PHE_label_exists

      segm_name = f"{self.currentCase}_PHE"
      self.srcSegmentation.RemoveSegment(segm_name)
      self.onNewLabelSegm(PHE_label["name"], PHE_label["color_r"], PHE_label["color_g"], PHE_label["color_b"], PHE_label["lower_bound_HU"], PHE_label["upper_bound_HU"])

  def startTimer(self):
      with TIMER_MUTEX:
        self.counter = 0
        # Add flag to avoid counting time when user clicks on save segm button
        self.flag2 = True

        # ----- ANW Addition ----- : Code to keep track of time passed with lcdNumber on UI
        # Create a timer
        self.timer = qt.QTimer()
        self.timer.timeout.connect(self.updatelcdNumber)

        # Start the timer and update every second
        self.timer.start(100) # 1000 ms = 1 second

        # Call the updatelcdNumber function
        self.updatelcdNumber()

  def updatelcdNumber(self):
      # Get the time
      with TIMER_MUTEX:
        if self.flag2: # add flag to avoid counting time when user clicks on save segm button
                # the timer sends a signal every second (1000 ms). 
            self.counter += 1  # the self.timer.timeout.connect(self.updatelcdNumber) function is called every second and updates the counter

        self.ui.lcdNumber.display(self.counter/10)


  def stopTimer(self):
      with TIMER_MUTEX:
        # If already called once (i.e when user pressed save segm button but forgot to annotator name), simply return the time
        if self.called:
            return self.total_time
        else:
            try:
                self.total_time = self.counter/10
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
        self.flag2 = False # For case after the first one the timer stops until the user clicks on the
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

  def toggleStartTimerButton(self):
      if (self.ui.SlicerDirectoryListView.count > 0):
        if self.ui.StartTimerButton.isChecked():
            self.startTimer()
            self.timer_router()

            self.ui.StartTimerButton.setEnabled(False)
            self.ui.StartTimerButton.setStyleSheet("background-color : silver")

            self.ui.PauseTimerButton.setEnabled(True)
            self.ui.PauseTimerButton.setStyleSheet("background-color : indianred")
            
            self.enableSegmentAndPaintButtons()
      else:
        self.ui.StartTimerButton.toggle()

  def togglePauseTimerButton(self):
      # if button is checked - Time paused
      if self.ui.PauseTimerButton.isChecked():
          # setting background color to light-blue
          self.ui.PauseTimerButton.setStyleSheet("background-color : lightblue")
          self.ui.PauseTimerButton.setText('Restart')
          self.timer.stop()
          for indiv_timer in self.timers:
              indiv_timer.stop()
          self.flag = False

          self.MostRecentPausedCasePath = self.currentCasePath

          self.disableSegmentAndPaintButtons()
          self.onPushButton_Erase()

      # if it is unchecked
      else:
          # set background color back to light-grey
          self.ui.PauseTimerButton.setStyleSheet("background-color : indianred")
          self.ui.PauseTimerButton.setText('Pause')
          self.timer.start(100)
          self.timer_router()
          self.flag = True

          self.enableSegmentAndPaintButtons()

  # for the timer Class not the LCD one
  def timer_router(self):
      self.timers[self.current_label_index].start()
      self.flag = True
      
      timer_index = 0
      for timer in self.timers:
          if timer_index != self.current_label_index:
              timer.stop()
          timer_index = timer_index + 1
            
  def createFolders(self):
      self.revision_step = self.ui.RevisionStep.currentText
      if len(self.revision_step) != 0:
          if os.path.exists(self.outputFolder) == False:
                msgboxtime = qt.QMessageBox()
                msgboxtime.setText("Segmentation not saved : output folder invalid!")
                msgboxtime.exec()
          else:
                self.updateCurrentOutputPathAndCurrentVolumeFilename()

                if os.path.exists(self.currentOutputPath) == False:
                    os.makedirs(self.currentOutputPath)

      else:
          msgboxtime = qt.QMessageBox()
          msgboxtime.setText("Segmentation not saved : revision step is not defined!  \n Please save again with revision step!")
          msgboxtime.exec()

  def resetClassificationInformation(self):
        for i, (objectName, label) in enumerate(self.classification_config_yaml["checkboxes"].items()):
            self.checkboxWidgets[objectName].setChecked(False)
        for i, (comboBoxName, options) in enumerate(self.classification_config_yaml["comboboxes"].items()):
            self.comboboxWidgets[comboBoxName].currentText = list(options.items())[0][1]
        for i, (freeTextBoxObjectName, label) in enumerate(self.classification_config_yaml["freetextboxes"].items()):
            self.freeTextBoxes[freeTextBoxObjectName].setText("")
        
  
  def getClassificationInformation(self):
      label_string = ""
      data_string = ""
      for i, (objectName, label) in enumerate(self.classification_config_yaml["checkboxes"].items()):
          if label_string != "":
              label_string = label_string + ","
              data_string = data_string + ","
          
          label_string = label_string + label
          
          data = "No"
          if self.checkboxWidgets[objectName].isChecked():
              data = "Yes"
          
          data_string = data_string + data
      
      for i, (comboBoxName, options) in enumerate(self.classification_config_yaml["comboboxes"].items()):
          label = comboBoxName.replace("_", " ").capitalize()

          if label_string != "":
              label_string = label_string + ","
              data_string = data_string + ","
          
          label_string = label_string + label

          data = self.comboboxWidgets[comboBoxName].currentText
          data_string = data_string + data
      
      for i, (freeTextBoxObjectName, label) in enumerate(self.classification_config_yaml["freetextboxes"].items()):
          if label_string != "":
              label_string = label_string + ","
              data_string = data_string + ","
          
          label_string = label_string + label
          
          data = self.freeTextBoxes[freeTextBoxObjectName].text.replace("\n", " // ")
          data_string = data_string + data

      return label_string, data_string
  
  def cast_segmentation_to_uint8(self):
      for case in self.predictions_paths:
          # Load the segmentation
          input_path = os.path.basename(case)
          if input_path.endswith('.nii') or input_path.endswith('.nii.gz'):
              segm = nib.load(case)
              segm_data_dtype = segm.dataobj.dtype
              print(f'infile: {input_path}, dtype: {segm_data.dtype}')
              if segm_data_dtype != np.uint8:
                  segm_data = segm_data.astype(np.uint8)
                  segm.header.set_data_dtype(np.uint8)
                  segm_nii = nib.Nifti1Image(segm_data, segm.affine, segm.header)
                  nib.save(segm_nii, case)
                  print(f'converted file {input_path} to uint8')
          elif input_path.endswith('seg.nrrd'):
              segm_data, header = nrrd.read(case)
              print(f'infile: {input_path}, dtype: {segm_data.dtype}')
              if segm_data.dtype != np.uint8:
                  segm_data = segm_data.astype(np.uint8)
                  header['type'] = 'unsigned char'
                  nrrd.write(case, segm_data, header = header)
                  print(f'converted file {input_path} to uint8')
          else:
              raise ValueError('The input segmentation file must be in nii, nii.gz or nrrd format.')
  
  def onSaveSegmentationButton(self):
      # By default creates a new folder in the volume directory 
      # Stop the timer when the button is pressed
      self.time = self.stopTimer()
      # Stop timer of the Timer class
      for timer in self.timers:
            timer.stop()
      self.annotator_name = self.ui.Annotator_name.text
      self.annotator_degree = self.ui.AnnotatorDegree.currentText

      # Create folders if not exist
      self.createFolders()
      
      # Make sure to select the first segmentation node  (i.e. the one that was created when the module was loaded, not the one created when the user clicked on the "Load mask" button)
      self.segmentationNode = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]

      currentSegmentationVersion = self.getCurrentSegmentationVersion()

      # quality control check 
      is_valid = self.qualityControlOfLabels()
      if is_valid == False:
          return

      # Save if annotator_name is not empty and timer started:
      if self.annotator_name and self.time is not None: 
          
          self.saveSegmentationInformation(currentSegmentationVersion)
          
          if 'nrrd' in INPUT_FILE_EXTENSION:
            self.saveNrrdSegmentation(currentSegmentationVersion)
          
          if 'nii' in INPUT_FILE_EXTENSION:
            self.saveNiiSegmentation(currentSegmentationVersion)
        
          msg_box = qt.QMessageBox()
          msg_box.setWindowTitle("Success")
          msg_box.setIcon(qt.QMessageBox.Information)
          msg_box.setText("Segmentation saved successfully!")
          msg_box.exec()

      # If annotator_name empty or timer not started.
      else:
          if not self.annotator_name:
              msgboxtime = qt.QMessageBox()
              msgboxtime.setText("Segmentation not saved : no annotator name !  \n Please save again with your name!")
              msgboxtime.exec()
          elif self.time is None:
              print("Error: timer is not started for some unknown reason.")
      
      self.cast_segmentation_to_uint8()

  def qualityControlOfLabels(self):
      is_valid = True 

      segment_names = self.getAllSegmentNames()
      if len(segment_names) != len(self.label_config_yaml["labels"]):
          msg = qt.QMessageBox()
          msg.setIcon(qt.QMessageBox.Critical)
          msg.setText("ERROR : Incorrect number of labels")
          msg.setInformativeText(f'Expected {len(self.label_config_yaml["labels"])} labels but obtained {len(segment_names)}. ')
          msg.setWindowTitle("ERROR : Incorrect number of labels")
          msg.exec()
          return False
      
      for i, segment_name in enumerate(segment_names):
          if segment_name != self.label_config_yaml["labels"][i]["name"]:
              msg = qt.QMessageBox()
              msg.setIcon(qt.QMessageBox.Critical)
              msg.setText("ERROR : Label mismatch")
              msg.setInformativeText(f'Expected {self.label_config_yaml["labels"][i]["name"]} but obtained {segment_name}. ')
              msg.setWindowTitle("ERROR : Label mismatch")
              msg.exec()
              return False
      return is_valid
  
  def saveNrrdSegmentation(self, currentSegmentationVersion):
        # Save .seg.nrrd file
        self.outputSegmFile = os.path.join(self.currentOutputPath,
                                                "{}_{}.seg.nrrd".format(self.currentVolumeFilename, currentSegmentationVersion))

        if not os.path.isfile(self.outputSegmFile):
            slicer.util.saveNode(self.segmentationNode, self.outputSegmFile)

        else:
            msg2 = qt.QMessageBox()
            msg2.setWindowTitle('Save As')
            msg2.setText(
                f'The file {self.currentCase}_{self.annotator_name}_{self.revision_step[0]}.seg.nrrd already exists \n Do you want to replace the existing file?')
            msg2.setIcon(qt.QMessageBox.Warning)
            msg2.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
            msg2.buttonClicked.connect(self.msg2_clicked)
            msg2.exec()
  
  def saveNiiSegmentation(self, currentSegmentationVersion):
        # Export segmentation to a labelmap volume
        # Note to save to nifti you need to convert to labelmapVolumeNode
        self.labelmapVolumeNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLabelMapVolumeNode')
        slicer.modules.segmentations.logic().ExportVisibleSegmentsToLabelmapNode(self.segmentationNode,
                                                                                self.labelmapVolumeNode,
                                                                                self.VolumeNode)

        self.outputSegmFileNifti = os.path.join(self.currentOutputPath,
                                                "{}_{}.nii.gz".format(self.currentVolumeFilename, currentSegmentationVersion))

        if not os.path.isfile(self.outputSegmFileNifti):
            slicer.util.saveNode(self.labelmapVolumeNode, self.outputSegmFileNifti)
        else:
            msg3 = qt.QMessageBox()
            msg3.setWindowTitle('Save As')
            msg3.setText(
                f'The file {self.currentCase}_{self.annotator_name}_{self.revision_step[0]}.nii.gz already exists \n Do you want to replace the existing file?')
            msg3.setIcon(qt.QMessageBox.Warning)
            msg3.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
            msg3.buttonClicked.connect(self.msg3_clicked)
            msg3.exec()
  
  def saveSegmentationInformation(self, currentSegmentationVersion):
        tag_str = "Volume filename,Segmentation version,Annotator Name,Annotator degree,Revision step,Date and time,Duration" 
        for label in self.label_config_yaml["labels"]:
            tag_str = tag_str + "," + label["name"] + " duration"
        
        data_str = self.currentCase 
        data_str = data_str + "," + currentSegmentationVersion
        data_str = data_str + "," + self.annotator_name
        data_str = data_str + "," + self.annotator_degree
        data_str = data_str + "," + self.revision_step[0]
        data_str = data_str + "," + datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        data_str = data_str + "," + str(self.ui.lcdNumber.value)
        for timer in self.timers:
            data_str = data_str + "," + str(timer.total_time)
        
        self.outputSegmentationInformationFile = os.path.join(self.currentOutputPath,
                                            '{}_SegmentationInformation.csv'.format(self.currentVolumeFilename))
        if not os.path.isfile(self.outputSegmentationInformationFile):
            with open(self.outputSegmentationInformationFile, 'w') as f:
                f.write(tag_str)
                f.write("\n")
                f.write(data_str)
        else:
            with open(self.outputSegmentationInformationFile, 'a') as f:
                f.write("\n")
                f.write(data_str)
  
  def saveClassificationInformation(self, classification_information_labels_string, classification_information_data_string):
        currentClassificationInformationVersion = self.getClassificationInformationVersion()

        tag_str = "Volume filename,Classification version,Annotator Name,Annotator degree,Revision step,Date and time" 
        tag_str = tag_str + "," + classification_information_labels_string
        
        data_str = self.currentCase 
        data_str = data_str + "," + currentClassificationInformationVersion
        data_str = data_str + "," + self.annotator_name
        data_str = data_str + "," + self.annotator_degree
        data_str = data_str + "," + self.revision_step[0]
        data_str = data_str + "," + datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        data_str = data_str + "," + classification_information_data_string
        
        self.outputClassificationInformationFile = os.path.join(self.currentOutputPath,
                                            '{}_ClassificationInformation.csv'.format(self.currentVolumeFilename))
        if not os.path.isfile(self.outputClassificationInformationFile):
            with open(self.outputClassificationInformationFile, 'w') as f:
                f.write(tag_str)
                f.write("\n")
                f.write(data_str)
        else:
            with open(self.outputClassificationInformationFile, 'a') as f:
                f.write("\n")
                f.write(data_str)
  
  def getClassificationInformationVersion(self):
      version = "v"
      classificationInformationPath = f'{self.currentOutputPath}{os.sep}{self.currentVolumeFilename}_ClassificationInformation.csv'

      if os.path.exists(classificationInformationPath) == False:
          version = version + "01"
      else:
          csv_data = pd.read_csv(classificationInformationPath)
          existing_version_strings = csv_data['Classification version'].to_list()
          existing_version_numbers = [(int)(version_string.split("v")[1]) for version_string in existing_version_strings]
          next_version_number =  max(existing_version_numbers) + 1
          version = f'{version}{next_version_number:02d}'

      return version 
  
  def getCurrentSegmentationVersion(self):
      list_of_segmentation_filenames = glob(f'{self.currentOutputPath}{os.sep}{INPUT_FILE_EXTENSION}')
      
      version = 'v'
      if list_of_segmentation_filenames == []:
          version = version + "01"
      else:
          existing_versions = [(int)(filename.split('_v')[1].split(".")[0]) for filename in list_of_segmentation_filenames]
          next_version_number =  max(existing_versions) + 1
          next_version_number = min(next_version_number, 99) # max 99 versions
          version = f'{version}{next_version_number:02d}'
      return version
      

  def msg2_clicked(self, msg2_button):
      if msg2_button.text == 'OK':
          slicer.util.saveNode(self.segmentationNode, self.outputSegmFile)
      else:
          return

  def msg3_clicked(self, msg3_button):
      if msg3_button.text == 'OK':
          slicer.util.saveNode(self.labelmapVolumeNode, self.outputSegmFileNifti)
      else:
          return

  def msg4_clicked(self, msg4_button):
      if msg4_button.text == 'OK':
          slicer.util.saveNode(self.VolumeNode, self.outputVolfile)
      else:
          return
      
  def verifyEmpty(self):
      if self.outputFolder is not None:

        content_of_output_folder = os.listdir(self.outputFolder)
        if '.DS_Store' in content_of_output_folder:
            content_of_output_folder.remove('.DS_Store')
        
        if len(content_of_output_folder) > 0:
            self.outputFolder = None

            msg = qt.QMessageBox()
            msg.setIcon(qt.QMessageBox.Critical)
            msg.setText("Error : The output folder must be empty ")
            msg.setInformativeText('Given that there is a new configuration of SlicerCART, the output folder must be empty. ')
            msg.setWindowTitle("ERROR : The output folder must be empty ")
            msg.exec()
        else:
            path_to_saved_config_files = f'{self.outputFolder}{os.sep}{CONF_FOLDER_NAME}'

            if os.path.exists(path_to_saved_config_files) == False:
                os.makedirs(path_to_saved_config_files)

            path_to_label_config_copy = f'{path_to_saved_config_files}{os.sep}{LABEL_CONFIG_COPY_FILENAME}'
            path_to_classification_config_copy = f'{path_to_saved_config_files}{os.sep}{CLASSIFICATION_CONFIG_COPY_FILENAME}'
            path_to_keyboard_shortcuts_config_copy = f'{path_to_saved_config_files}{os.sep}{KEYBOARD_SHORTCUTS_CONFIG_COPY_FILENAME}'
            path_to_general_config_copy = f'{path_to_saved_config_files}{os.sep}{GENERAL_CONFIG_COPY_FILENAME}'

            shutil.copy(LABEL_CONFIG_FILE_PATH, path_to_label_config_copy)
            shutil.copy(CLASSIFICATION_CONFIG_FILE_PATH, path_to_classification_config_copy)
            shutil.copy(GENERAL_CONFIG_FILE_PATH, path_to_general_config_copy)
            shutil.copy(KEYBOARD_SHORTCUTS_CONFIG_FILE_PATH, path_to_keyboard_shortcuts_config_copy)
  
  def onSelectOutputFolder(self):
      self.outputFolder = qt.QFileDialog.getExistingDirectory(None,"Open a folder", self.DefaultDir, qt.QFileDialog.ShowDirsOnly)

      if REQUIRE_EMPTY: 
          self.verifyEmpty()
      
      if self.outputFolder is not None:
          self.ui.LoadClassification.setEnabled(True)
          self.ui.LoadSegmentation.setEnabled(True)

          self.ui.SaveSegmentationButton.setEnabled(True)
          self.ui.SaveClassificationButton.setEnabled(True)
          
          self.updateCurrentOutputPathAndCurrentVolumeFilename()

          self.predictions_paths = sorted(glob(os.path.join(self.outputFolder, f'{INPUT_FILE_EXTENSION}')))

  def msg_warnig_delete_segm_node_clicked(self, msg_warnig_delete_segm_node_button):
      if msg_warnig_delete_segm_node_button.text == 'OK':
        srcNode = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
        slicer.mrmlScene.RemoveNode(srcNode)
      else:
          return

  def onLoadClassification(self): 
      classificationInformationPath = f'{self.currentOutputPath}{os.sep}{self.currentVolumeFilename}_ClassificationInformation.csv'
      classificationInformation_df = None
      if os.path.exists(classificationInformationPath):
          classificationInformation_df = pd.read_csv(classificationInformationPath)
      else:
          msg = qt.QMessageBox()
          msg.setIcon(qt.QMessageBox.Information)
          msg.setText("No saved classifications")
          msg.setInformativeText('There are no classifications saved in the ClassificationInformation.csv.')
          msg.setWindowTitle("No saved classifications")
          msg.exec()
          return

      loadClassificationWindow = LoadClassificationWindow(self, classificationInformation_df)
      loadClassificationWindow.show()

  def onSaveClassificationButton(self):
      self.annotator_name = self.ui.Annotator_name.text
      self.annotator_degree = self.ui.AnnotatorDegree.currentText

      classification_information_labels_string, classification_information_data_string = self.getClassificationInformation()
      
      # Create folders if don't exist
      self.createFolders()

      if self.annotator_name is not None: 
          self.saveClassificationInformation(classification_information_labels_string, classification_information_data_string)
          msg_box = qt.QMessageBox()
          msg_box.setWindowTitle("Success")
          msg_box.setIcon(qt.QMessageBox.Information)
          msg_box.setText("Classification saved successfully!")
          msg_box.exec()

      else:
          msgboxtime = qt.QMessageBox()
          msgboxtime.setText("Classification not saved : no annotator name !  \n Please save again with your name!")
          msgboxtime.exec()

    
  def onCompareSegmentVersions(self):
      if 'Clear' in self.ui.CompareSegmentVersions.text:
          self.onClearCompareSegmentVersions()
      else:
        msg_warnig_delete_segm_node = self.warnAgainstDeletingCurrentSegmentation()
        msg_warnig_delete_segm_node.buttonClicked.connect(self.onCompareSegmentVersionsWillEraseCurrentSegmentsWarningClicked)
        msg_warnig_delete_segm_node.exec() 
  
  def onCompareSegmentVersionsWillEraseCurrentSegmentsWarningClicked(self, msg_warnig_delete_segm_node_button):
      if msg_warnig_delete_segm_node_button.text == 'OK':
        srcNode = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
        slicer.mrmlScene.RemoveNode(srcNode)
        
        self.openCompareSegmentVersionsWindow()
      else:
          return
      
  def warnAgainstDeletingCurrentSegmentation(self):
      msg_warnig_delete_segm_node = qt.QMessageBox() 
      msg_warnig_delete_segm_node.setText('This will delete the current segmentation. Do you want to continue?')
      msg_warnig_delete_segm_node.setIcon(qt.QMessageBox.Warning)
      msg_warnig_delete_segm_node.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
      
      return msg_warnig_delete_segm_node
  
  def onLoadSegmentation(self): 
      msg_warnig_delete_segm_node = self.warnAgainstDeletingCurrentSegmentation()
      msg_warnig_delete_segm_node.buttonClicked.connect(self.onLoadSegmentationWillEraseCurrentSegmentsWarningClicked)
      msg_warnig_delete_segm_node.exec() 
  
  def onLoadSegmentationWillEraseCurrentSegmentsWarningClicked(self, msg_warnig_delete_segm_node_button):
      if msg_warnig_delete_segm_node_button.text == 'OK':
        srcNode = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
        slicer.mrmlScene.RemoveNode(srcNode)
        self.openLoadSegmentationWindow()
      else:
          return
      
  def openLoadSegmentationWindow(self):
      segmentationInformationPath = f'{self.currentOutputPath}{os.sep}{self.currentVolumeFilename}_SegmentationInformation.csv'
      segmentationInformation_df = None
      if os.path.exists(segmentationInformationPath):
          segmentationInformation_df = pd.read_csv(segmentationInformationPath)
      else:
          msg = qt.QMessageBox()
          msg.setIcon(qt.QMessageBox.Information)
          msg.setText("No saved segmentations")
          msg.setInformativeText('There are no segmentations saved in the SegmentationInformation.csv.')
          msg.setWindowTitle("No saved segmentations")
          msg.exec()
          return

      loadSegmentationWindow = LoadSegmentationsWindow(self, segmentationInformation_df)
      loadSegmentationWindow.show()

  def openCompareSegmentVersionsWindow(self):
      segmentationInformationPath = f'{self.currentOutputPath}{os.sep}{self.currentVolumeFilename}_SegmentationInformation.csv'
      segmentationInformation_df = None
      if os.path.exists(segmentationInformationPath):
          segmentationInformation_df = pd.read_csv(segmentationInformationPath)
      else:
          msg = qt.QMessageBox()
          msg.setIcon(qt.QMessageBox.Information)
          msg.setText("No saved segmentations")
          msg.setInformativeText('There are no segmentations saved in the SegmentationInformation.csv.')
          msg.setWindowTitle("No saved segmentations")
          msg.exec()
          return
      
      compareSegmentVersionsWindow = CompareSegmentVersionsWindow(self, segmentationInformation_df)
      compareSegmentVersionsWindow.show()

  def compareSegmentVersions(self, selected_label, selected_version_file_paths):
      self.labelOfCompareSegmentVersions = selected_label
      self.colorsSelectedVersionFilePathsForCompareSegmentVersions = {}

      selected_label_value = 0
      for label in self.label_config_yaml['labels']:
          if selected_label == label['name']:
              selected_label_value = label['value']

      slicer.mrmlScene.Clear()
      slicer.util.loadVolume(self.currentCasePath)
      self.VolumeNode = slicer.util.getNodesByClass('vtkMRMLScalarVolumeNode')[0]
      
      Vol_displayNode = self.VolumeNode.GetDisplayNode()
      Vol_displayNode.AutoWindowLevelOff()
      Vol_displayNode.SetWindow(CT_WINDOW_WIDTH)
      Vol_displayNode.SetLevel(CT_WINDOW_LEVEL)
      Vol_displayNode.SetInterpolate(INTERPOLATE_VALUE)

      self.segmentEditorWidget = slicer.modules.segmenteditor.widgetRepresentation().self().editor
      self.segmentEditorWidget.setActiveEffectByName("No editing")

      self.resetTimer()
      
      for (segment_name, version_file_path) in selected_version_file_paths.items():
            if 'nrrd' in INPUT_FILE_EXTENSION:
                slicer.util.loadSegmentation(version_file_path)
                currentSegmentationNode = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
            elif 'nii' in INPUT_FILE_EXTENSION:
                labelmapVolumeNode = slicer.util.loadLabelVolume(version_file_path)
                currentSegmentationNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
                slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(labelmapVolumeNode, currentSegmentationNode)

            self.segmentEditorWidget = slicer.modules.segmenteditor.widgetRepresentation().self().editor
            self.segmentEditorNode =  self.segmentEditorWidget.mrmlSegmentEditorNode()
            self.segmentEditorWidget.setSegmentationNode(currentSegmentationNode)
            self.segmentEditorWidget.setSourceVolumeNode(self.VolumeNode)
            currentSegmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(self.VolumeNode)
            segmentationDisplayNode = currentSegmentationNode.GetDisplayNode()
            segmentationDisplayNode.SetAllSegmentsVisibility(False)

            currentSegmentationNode.SetName(os.path.split(version_file_path)[1].split('.')[0])

            segment = currentSegmentationNode.GetSegmentation().GetSegment(str(selected_label_value))
            
            if segment is not None :
                segment.SetName(segment_name)
            
                # OBTAIN RANDOM BRIGHT COLOR : https://stackoverflow.com/questions/43437309/get-a-bright-random-colour-python
                h,s,l = random.random(), 0.5 + random.random()/2.0, 0.4 + random.random()/5.0
                r,g,b = [int(256*i) for i in colorsys.hls_to_rgb(h,l,s)]
                self.colorsSelectedVersionFilePathsForCompareSegmentVersions[segment_name] = [r, g, b]
                segment.SetColor(r / 255, g / 255, b / 255)

                segmentationDisplayNode.SetSegmentVisibility(str(selected_label_value), True)

      self.disableSegmentAndPaintButtons()
      self.disablePauseTimerButton()
      self.ui.StartTimerButton.setEnabled(False)
      self.ui.StartTimerButton.setStyleSheet("background-color : light gray") 
      self.ui.CompareSegmentVersions.setText('Clear Read Only Segment Versions')
      self.ui.CompareSegmentVersions.setStyleSheet("background-color : yellowgreen")
      self.ui.SaveSegmentationButton.setEnabled(False)

      self.ui.ShowSegmentVersionLegendButton.setVisible(True)
  
  def onClearCompareSegmentVersions(self):
      self.loadPatient()
      
      self.enableStartTimerButton()

      self.ui.CompareSegmentVersions.setText('Compare segment versions')
      self.ui.CompareSegmentVersions.setStyleSheet("background-color : light gray") 

      self.ui.SaveSegmentationButton.setEnabled(True)

      self.ui.ShowSegmentVersionLegendButton.setVisible(False)

  def loadSegmentation(self, absolute_path_to_segmentation_file):
        if 'nrrd' in INPUT_FILE_EXTENSION:
            slicer.util.loadSegmentation(absolute_path_to_segmentation_file)
            self.segmentationNode = slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
        elif 'nii' in INPUT_FILE_EXTENSION:
            labelmapVolumeNode = slicer.util.loadLabelVolume(absolute_path_to_segmentation_file)
            self.segmentationNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
            slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(labelmapVolumeNode, self.segmentationNode)

        self.segmentEditorWidget = slicer.modules.segmenteditor.widgetRepresentation().self().editor
        self.segmentEditorNode =  self.segmentEditorWidget.mrmlSegmentEditorNode()
        self.segmentEditorWidget.setSegmentationNode(self.segmentationNode)
        self.segmentEditorWidget.setSourceVolumeNode(self.VolumeNode)
        # set refenrence geometry to Volume node
        self.segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(self.VolumeNode)
        nn = self.segmentationNode.GetDisplayNode()
        # set Segmentation visible:
        nn.SetAllSegmentsVisibility(True)

        loaded_segment_ids = self.segmentationNode.GetSegmentation().GetSegmentIDs()
        for i, segment_id in enumerate(loaded_segment_ids):
            for label in self.label_config_yaml["labels"]:
                if str(label['value']) == str(segment_id):
                    segment = self.segmentationNode.GetSegmentation().GetSegment(segment_id)
                    segment.SetName(label["name"])
                    segment.SetColor(label["color_r"]/255, label["color_g"]/255, label["color_b"]/255)

        list_of_segment_names = self.getAllSegmentNames()
        for label in self.label_config_yaml["labels"]:
            if label['name'] not in list_of_segment_names:
                self.onNewLabelSegm(label["name"], label["color_r"], label["color_g"], label["color_b"], label["lower_bound_HU"], label["upper_bound_HU"])

        for segment_id in loaded_segment_ids:
            for label in self.label_config_yaml["labels"]:
                if str(segment_id) == str(label['value']) or str(segment_id) == str(label['name']):
                    self.segmentationNode.GetSegmentation().SetSegmentIndex(str(segment_id), label['value']-1)

  def getAllSegmentNames(self):
        list_of_segment_ids = self.segmentationNode.GetSegmentation().GetSegmentIDs()
        list_of_segment_names = []
        for segment_id in list_of_segment_ids:
            segment = self.segmentationNode.GetSegmentation().GetSegment(segment_id)
            list_of_segment_names.append(segment.GetName())
        return list_of_segment_names

  def onPushDefaultMin(self):
      with open(LABEL_CONFIG_FILE_PATH, 'r') as file:
        fresh_config = yaml.safe_load(file)
        self.label_config_yaml["labels"][self.current_label_index]["lower_bound_HU"] = fresh_config["labels"][self.current_label_index]["lower_bound_HU"]
        self.setUpperAndLowerBoundHU(self.label_config_yaml["labels"][self.current_label_index]["lower_bound_HU"], self.label_config_yaml["labels"][self.current_label_index]["upper_bound_HU"])

  def onPushDefaultMax(self):
      with open(LABEL_CONFIG_FILE_PATH, 'r') as file:
        fresh_config = yaml.safe_load(file)
        self.label_config_yaml["labels"][self.current_label_index]["upper_bound_HU"] = fresh_config["labels"][self.current_label_index]["upper_bound_HU"]     
        self.setUpperAndLowerBoundHU(self.label_config_yaml["labels"][self.current_label_index]["lower_bound_HU"], self.label_config_yaml["labels"][self.current_label_index]["upper_bound_HU"])

  def onPush_ShowSegmentVersionLegendButton(self):
      segmentationInformationPath = f'{self.currentOutputPath}{os.sep}{self.currentVolumeFilename}_SegmentationInformation.csv'
      segmentationInformation_df = None
      if os.path.exists(segmentationInformationPath):
          segmentationInformation_df = pd.read_csv(segmentationInformationPath)
      else:
          msg = qt.QMessageBox()
          msg.setIcon(qt.QMessageBox.Information)
          msg.setText("No saved segmentations")
          msg.setInformativeText('There are no segmentations saved in the SegmentationInformation.csv.')
          msg.setWindowTitle("No saved segmentations")
          msg.exec()
          return
      
      showSegmentVersionLegendWindow = ShowSegmentVersionLegendWindow(self, segmentationInformation_df)
      showSegmentVersionLegendWindow.show()
  
  def onPushButton_undo(self):
      self.segmentEditorWidget.undo()

  def onDropDownButton_label_select(self, value):
      self.current_label_index = value
      label = self.label_config_yaml["labels"][value]
      self.setUpperAndLowerBoundHU(label["lower_bound_HU"], label["upper_bound_HU"])

      label_name = label["name"]
      try:
        segment_name = label_name
        self.onPushButton_select_label(segment_name, label["lower_bound_HU"], label["upper_bound_HU"])
      except:
        pass 
      
  def onPushLassoPaint(self):
        self.segmentEditorWidget.setActiveEffectByName("Scissors")
        self.segmentEditorNode.SetMasterVolumeIntensityMask(False)
        effect = self.segmentEditorWidget.activeEffect()
        effect.setParameter("Operation","FillInside")
        effect.setParameter("Shape","FreeForm")
        effect.setSliceCutMode(3)
  
  def onPushButton_Paint(self):
        selected_segment_id = self.segmentationNode.GetSegmentation().GetSegmentIdBySegmentName(self.label_config_yaml["labels"][self.current_label_index]['name'])
        self.segmentEditorNode.SetSelectedSegmentID(selected_segment_id)
        self.segmentEditorWidget.setActiveEffectByName("Paint")
        # Note it seems that sometimes you need to activate the effect first with :
        # Assign effect to the segmentEditorWidget using the active effect
        self.effect = self.segmentEditorWidget.activeEffect()
        self.effect.activate()
        self.effect.setParameter('BrushSphere',1)
        # Seems that you need to activate the effect to see it in Slicer
        # Set up the mask parameters (note that PaintAllowed...was changed to EditAllowed)
        self.segmentEditorNode.SetMaskMode(slicer.vtkMRMLSegmentationNode.EditAllowedEverywhere)
        #Set if using Editable intensity range (the range is defined below using object.setParameter)
        self.set_master_volume_intensity_mask_according_to_modality()
        self.segmentEditorNode.SetSourceVolumeIntensityMaskRange(self.LB_HU, self.UB_HU)
        self.segmentEditorNode.SetOverwriteMode(slicer.vtkMRMLSegmentEditorNode.OverwriteAllSegments)

  def toggleFillButton(self):
      if self.ui.pushButton_ToggleFill.isChecked():
          self.ui.pushButton_ToggleFill.setStyleSheet("background-color : yellowgreen")
          self.ui.pushButton_ToggleFill.setText('Fill: ON')
          self.segmentationNode.GetDisplayNode().SetOpacity2DFill(0)
      else:
          self.ui.pushButton_ToggleFill.setStyleSheet("background-color : indianred")
          self.ui.pushButton_ToggleFill.setText('Fill: OFF')
          self.segmentationNode.GetDisplayNode().SetOpacity2DFill(100)

  def onPushButton_ToggleVisibility(self):
      if self.ui.pushButton_ToggleVisibility.isChecked():
          self.ui.pushButton_ToggleVisibility.setStyleSheet("background-color : indianred")
          self.ui.pushButton_ToggleVisibility.setText('Visibility: OFF')
          self.segmentationNode.GetDisplayNode().SetAllSegmentsVisibility(False)
      else:
          self.ui.pushButton_ToggleVisibility.setStyleSheet("background-color : yellowgreen")
          self.ui.pushButton_ToggleVisibility.setText('Visibility: ON')
          self.segmentationNode.GetDisplayNode().SetAllSegmentsVisibility(True)

  def togglePaintMask(self):
        if self.ui.pushButton_TogglePaintMask.isChecked():
            self.ui.pushButton_TogglePaintMask.setStyleSheet("background-color : yellowgreen")
            self.ui.pushButton_TogglePaintMask.setText('Paint Mask ON')
            self.segmentEditorNode.SetMaskMode(slicer.vtkMRMLSegmentationNode.EditAllowedEverywhere)


  def onPushButton_segmeditor(self):
      slicer.util.selectModule("SegmentEditor")

  def onPushButton_Erase(self):
      self.segmentEditorWidget.setActiveEffectByName("Erase")
      # Note it seems that sometimes you need to activate the effect first with :
      # Assign effect to the segmentEditorWidget using the active effect
      self.effect = self.segmentEditorWidget.activeEffect()
      # Seems that you need to activate the effect to see it in Slicer
      self.effect.activate()
      self.segmentEditorNode.SetMasterVolumeIntensityMask(False)

  def onPushButton_Smooth(self):
      # pass
      # Smoothing
      self.segmentEditorWidget = slicer.modules.segmenteditor.widgetRepresentation().self().editor
      self.segmentEditorWidget.setActiveEffectByName("Smoothing")
      effect = self.segmentEditorWidget.activeEffect()
      effect.setParameter("SmoothingMethod", "MEDIAN")
      effect.setParameter("KernelSizeMm", 3)
      effect.self().onApply()


      
  def onPushButton_Small_holes(self):
      # pass
      # Fill holes smoothing
      self.segmentEditorWidget = slicer.modules.segmenteditor.widgetRepresentation().self().editor
      self.segmentEditorWidget.setActiveEffectByName("Smoothing")
      effect = self.segmentEditorWidget.activeEffect()
      effect.setParameter("SmoothingMethod", "MORPHOLOGICAL_CLOSING")
      effect.setParameter("KernelSizeMm", 3)
      effect.self().onApply()

  def onLB_HU(self):
      try:
        self.LB_HU=self.ui.LB_HU.value
        self.set_master_volume_intensity_mask_according_to_modality()
        self.segmentEditorNode.SetSourceVolumeIntensityMaskRange(self.LB_HU, self.UB_HU)
        self.label_config_yaml["labels"][self.current_label_index]["lower_bound_HU"] = self.LB_HU
      except:
        pass
      
  def onUB_HU(self):
      try:
        self.UB_HU=self.ui.UB_HU.value
        self.set_master_volume_intensity_mask_according_to_modality()
        self.segmentEditorNode.SetSourceVolumeIntensityMaskRange(self.LB_HU, self.UB_HU)
        self.label_config_yaml["labels"][self.current_label_index]["upper_bound_HU"] = self.UB_HU
      except:
        pass
      
class SlicerCARTLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self):
    """
    Called when the logic class is instantiated. Can be used for initializing member variables.
    """
    ScriptedLoadableModuleLogic.__init__(self)

  def setDefaultParameters(self, parameterNode):
    """
    Initialize parameter node with default settings.
    """
    if not parameterNode.GetParameter("Threshold"):
      parameterNode.SetParameter("Threshold", "100.0")
    if not parameterNode.GetParameter("Invert"):
      parameterNode.SetParameter("Invert", "false")

  def process(self, inputVolume, outputVolume, imageThreshold, invert=False, showResult=True):
    """
    Run the processing algorithm.
    Can be used without GUI widget.
    :param inputVolume: volume to be thresholded
    :param outputVolume: thresholding result
    :param imageThreshold: values above/below this threshold will be set to 0
    :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
    :param showResult: show output volume in slice viewers
    """

    if not inputVolume or not outputVolume:
      raise ValueError("Input or output volume is invalid")

    import time
    startTime = time.time()
    logging.info('Processing started')

    # Compute the thresholded output volume using the "Threshold Scalar Volume" CLI module
    cliParams = {
      'InputVolume': inputVolume.GetID(),
      'OutputVolume': outputVolume.GetID(),
      'ThresholdValue' : imageThreshold,
      'ThresholdType' : 'Above' if invert else 'Below'
      }
    cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True, update_display=showResult)
    # We don't need the CLI module node anymore, remove it to not clutter the scene with it
    slicer.mrmlScene.RemoveNode(cliNode)

    stopTime = time.time()
    logging.info(f'Processing completed in {stopTime-startTime:.2f} seconds')

class SlicerCARTTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear()

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_SlicerCART1()

  def test_SlicerCART1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")

    # Get/create input data

    import SampleData
    registerSampleData()
    inputVolume = SampleData.downloadSample('SlicerCART1')
    self.delayDisplay('Loaded test data set')

    inputScalarRange = inputVolume.GetImageData().GetScalarRange()
    self.assertEqual(inputScalarRange[0], 0)
    self.assertEqual(inputScalarRange[1], 695)

    outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
    threshold = 100

    # Test the module logic

    logic = SlicerCARTLogic()

    # Test algorithm with non-inverted threshold
    logic.process(inputVolume, outputVolume, threshold, True)
    outputScalarRange = outputVolume.GetImageData().GetScalarRange()
    self.assertEqual(outputScalarRange[0], inputScalarRange[0])
    self.assertEqual(outputScalarRange[1], threshold)

    # Test algorithm with inverted threshold
    logic.process(inputVolume, outputVolume, threshold, False)
    outputScalarRange = outputVolume.GetImageData().GetScalarRange()
    self.assertEqual(outputScalarRange[0], inputScalarRange[0])
    self.assertEqual(outputScalarRange[1], inputScalarRange[1])

    self.delayDisplay('Test passed')
