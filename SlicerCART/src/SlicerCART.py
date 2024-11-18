"""
    This is the main file for SlicerCART.
    That means the Slicer Python Interpreter always refer to the path of this
    script when using SlicerCART.
"""

###############################################################################
# Those imports are required to make the module working appropriately using
# separated files
from utils import * # Import all modules, packages and global variables
from scripts import * # Import all classes

###############################################################################

###############################################################################
# This main script contains the following classes:
#   SlicerCART --- main explanation script class
#   SlicerCARTWidget --- SlicerCART graphical user interface class (mainly use)

###############################################################################

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
    
  def get_config_values(self):
      with open(CONFIG_FILE_PATH, 'r') as file:
        self.config_yaml = yaml.safe_load(file)

        global INPUT_FILE_EXTENSION
        global DEFAULT_VOLUMES_DIRECTORY
        global DEFAULT_SEGMENTATION_DIRECTORY
        global REQUIRE_VOLUME_DATA_HIERARCHY_BIDS_FORMAT
        global MODALITY
        global IS_CLASSIFICATION_REQUESTED
        global IS_SEGMENTATION_REQUESTED
        global IS_MOUSE_SHORTCUTS_REQUESTED
        global IS_KEYBOARD_SHORTCUTS_REQUESTED
        global INTERPOLATE_VALUE
        global CT_WINDOW_WIDTH
        global CT_WINDOW_LEVEL
        global IS_DISPLAY_TIMER_REQUESTED
                
        IS_DISPLAY_TIMER_REQUESTED = self.config_yaml["is_display_timer_requested"]

        INPUT_FILE_EXTENSION = self.config_yaml["input_filetype"]
        DEFAULT_VOLUMES_DIRECTORY = self.config_yaml["default_volume_directory"]
        self.DefaultDir = DEFAULT_VOLUMES_DIRECTORY
        DEFAULT_SEGMENTATION_DIRECTORY = self.config_yaml["default_segmentation_directory"]
        MODALITY = self.config_yaml["modality"]
        IS_CLASSIFICATION_REQUESTED = self.config_yaml["is_classification_requested"]
        IS_SEGMENTATION_REQUESTED = self.config_yaml["is_segmentation_requested"]
        IS_MOUSE_SHORTCUTS_REQUESTED = self.config_yaml["is_mouse_shortcuts_requested"]
        IS_KEYBOARD_SHORTCUTS_REQUESTED = self.config_yaml["is_keyboard_shortcuts_requested"]
        INTERPOLATE_VALUE = self.config_yaml["interpolate_value"]

        if MODALITY == 'CT':
            # then BIDS not mandatory because it is not yet supported 
            # therefore, either .nrrd or .nii.gz accepted 
            REQUIRE_VOLUME_DATA_HIERARCHY_BIDS_FORMAT = False
            CT_WINDOW_WIDTH = self.config_yaml["ct_window_width"]
            CT_WINDOW_LEVEL = self.config_yaml["ct_window_level"]

        elif MODALITY == 'MRI':
            # therefore, .nii.gz required  
            INPUT_FILE_EXTENSION = '*.nii.gz'
            # user can decide whether to impose bids or not
            REQUIRE_VOLUME_DATA_HIERARCHY_BIDS_FORMAT = self.config_yaml["impose_bids_format"]

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
    self.lineDetails = {}
    self.previousAction = None

    #MB: code below added in the configuration setup since its absence
    # created issues when trying to load cases after selecting a volume folder.
    self.get_config_values()
    with open(CONFIG_FILE_PATH, 'r') as file:
        self.config_yaml = yaml.full_load(file)
        self.current_label_index = self.config_yaml['labels'][0]['value']
  
    self.ui.PauseTimerButton.setText('Pause')
    self.ui.SelectVolumeFolder.connect('clicked(bool)', self.onSelectVolumesFolderButton)
    self.ui.EditConfiguration.connect('clicked(bool)', self.onEditConfiguration)
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
    self.ui.Annotator_name.textChanged.connect(self.on_annotator_name_changed)
    self.ui.pushButton_Paint.connect('clicked(bool)', self.onPushButton_Paint)
    self.ui.LassoPaintButton.connect('clicked(bool)', self.onPushLassoPaint)
    self.ui.pushButton_ToggleVisibility.connect('clicked(bool)', self.onPushButton_ToggleVisibility)
    self.ui.PushButton_segmeditor.connect('clicked(bool)', self.onPushButton_segmeditor)  
    self.ui.pushButton_Erase.connect('clicked(bool)', self.onPushButton_Erase)  
    self.ui.pushButton_Smooth.connect('clicked(bool)', self.onPushButton_Smooth)  
    self.ui.pushButton_Small_holes.connect('clicked(bool)', self.onPushButton_Small_holes)  
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
    self.ui.placeMeasurementLine.connect('clicked(bool)', self.onPlacePointsAndConnect)
    
    self.ui.ShowSegmentVersionLegendButton.setVisible(False)

    self.disablePauseTimerButton()
    self.disableSegmentAndPaintButtons()
    self.ui.pushButton_Interpolate.setEnabled(False)
    self.ui.SaveSegmentationButton.setEnabled(False)

    self.enableStartTimerButton()

    self.ui.LoadClassification.setEnabled(False)
    self.ui.SaveClassificationButton.setEnabled(False)
    self.ui.LoadSegmentation.setEnabled(False)

    self.ui.ThresholdLabel.setStyleSheet("font-weight: bold")

    self.ui.UB_HU.setMinimum(-32000)
    self.ui.LB_HU.setMinimum(-32000)
    self.ui.UB_HU.setMaximum(29000)
    self.ui.LB_HU.setMaximum(29000)

    self.ui.pushButton_ToggleFill.setStyleSheet("background-color : indianred")
    self.ui.pushButton_ToggleVisibility.setStyleSheet("background-color : yellowgreen")
    self.ui.lcdNumber.setStyleSheet("background-color : black")
    
    self.MostRecentPausedCasePath = ""
  
  def setup_configuration(self):
        self.get_config_values()
        
        if not IS_DISPLAY_TIMER_REQUESTED:
            self.ui.PauseTimerButton.hide()
            self.ui.StartTimerButton.hide()  

        if IS_MOUSE_SHORTCUTS_REQUESTED:
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

        self.LB_HU = self.config_yaml["labels"][0]["lower_bound_HU"]
        self.UB_HU = self.config_yaml["labels"][0]["upper_bound_HU"]
        
        # Change the value of the upper and lower bound of the HU
        self.ui.UB_HU.setValue(self.UB_HU)
        self.ui.LB_HU.setValue(self.LB_HU)

        # clear classification widgets
        for i in reversed(range(self.ui.ClassificationGridLayout.count())): 
            if self.ui.ClassificationGridLayout.itemAt(i).widget() is not None:
                self.ui.ClassificationGridLayout.itemAt(i).widget().setParent(None)

        comboboxesStartRow = self.setupCheckboxes(3)
        freetextStartRow = self.setupComboboxes(comboboxesStartRow)
        self.setupFreeText(freetextStartRow)
        
        # Initialize timers
        self.timers = []
        timer_index = 0
        for label in self.config_yaml["labels"]:
            self.timers.append(Timer(number=timer_index))
            timer_index = timer_index + 1
        
        if not IS_CLASSIFICATION_REQUESTED:
            self.ui.MRMLCollapsibleButton.setVisible(False)
        if not IS_SEGMENTATION_REQUESTED:
            self.ui.MRMLCollapsibleButton_2.setVisible(False)

        if MODALITY == 'MRI':
            self.ui.ThresholdLabel.setVisible(False)
            self.ui.MinimumLabel.setVisible(False)
            self.ui.MaximumLabel.setVisible(False)
            self.ui.LB_HU.setVisible(False)
            self.ui.UB_HU.setVisible(False)
            self.ui.pushDefaultMin.setVisible(False)
            self.ui.pushDefaultMax.setVisible(False)

        if self.config_yaml['is_keyboard_shortcuts_requested']:
            for i in self.config_yaml["KEYBOARD_SHORTCUTS"]:

                shortcutKey = i.get("shortcut")
                callback_name = i.get("callback")
                button_name = i.get("button")

                button = getattr(self.ui, button_name)
                callback = getattr(self, callback_name)

                self.connectShortcut(shortcutKey, button, callback)
                
        if self.config_yaml['is_display_timer_requested']:
            self.ui.lcdNumber.setStyleSheet("background-color : black")
        else:
            self.ui.lcdNumber.setVisible(False)
        
        # Display the selected color view at module startup
        if self.config_yaml['slice_view_color'] == "Yellow":
            slicer.app.layoutManager().setLayout(
                slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpYellowSliceView)
        if self.config_yaml['slice_view_color'] == "Red":
            slicer.app.layoutManager().setLayout(
                slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpRedSliceView)
        if self.config_yaml['slice_view_color'] == "Green":
            slicer.app.layoutManager().setLayout(
                slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpGreenSliceView)
            
        self.ui.dropDownButton_label_select.clear()
        for label in self.config_yaml["labels"]:
            self.ui.dropDownButton_label_select.addItem(label["name"])
  
  def set_master_volume_intensity_mask_according_to_modality(self):
      if MODALITY == 'CT':
            self.segmentEditorNode.SetMasterVolumeIntensityMask(True)
      elif MODALITY == 'MRI':
            self.segmentEditorNode.SetMasterVolumeIntensityMask(False)
  
  def setupCheckboxes(self, number_of_columns):
      self.checkboxWidgets = {}

      row_index = 0

      for i, (objectName, label) in enumerate(self.config_yaml["checkboxes"].items()):
        #print(objectName, label)
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
      for i, (comboBoxName, options) in enumerate(self.config_yaml["comboboxes"].items()):
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
      for i, (freeTextObjectName, freeTextLabel) in enumerate(self.config_yaml["freetextboxes"].items()):
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
  
  #measurement line function set as a segment and paint functionality
  def enableSegmentAndPaintButtons(self):
    self.ui.pushButton_Paint.setEnabled(True)
    self.ui.LassoPaintButton.setEnabled(True)
    self.ui.pushButton_Erase.setEnabled(True)
    self.ui.placeMeasurementLine.setEnabled(True)

  def disableSegmentAndPaintButtons(self):
    self.ui.pushButton_Paint.setEnabled(False)
    self.ui.LassoPaintButton.setEnabled(False)
    self.ui.pushButton_Erase.setEnabled(False)
    self.ui.placeMeasurementLine.setEnabled(False)

  def onEditConfiguration(self):
      slicerCARTConfigurationSetupWindow = SlicerCARTConfigurationSetupWindow(self, edit_conf = True)
      slicerCARTConfigurationSetupWindow.show()

  def onSelectVolumesFolderButton(self):
      self.CurrentFolder= qt.QFileDialog.getExistingDirectory(None,"Open a folder", self.DefaultDir, qt.QFileDialog.ShowDirsOnly)

      #prevents crashing if no volume folder is selected
      if not self.CurrentFolder:
          return

      file_structure_valid = True
      if REQUIRE_VOLUME_DATA_HIERARCHY_BIDS_FORMAT == True:
          file_structure_valid = self.validateBIDS(self.CurrentFolder)
    
      if file_structure_valid == False:
          return # don't load any patient cases

      self.CasesPaths = sorted(glob(f'{self.CurrentFolder}{os.sep}**{os.sep}{INPUT_FILE_EXTENSION}', recursive = True))

      # Remove the volumes in the folder 'derivatives' (creates issues for
      # loading cases)
      self.CasesPaths = [item for item in self.CasesPaths if 'derivatives' not
                         in item]

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
      
      if not IS_DISPLAY_TIMER_REQUESTED:
          self.enableSegmentAndPaintButtons()      

      self.updateCurrentPatient()
      # Highlight the current case in the list view (when pressing on next o)
      self.ui.SlicerDirectoryListView.setCurrentItem(self.ui.SlicerDirectoryListView.item(self.currentCase_index))
      self.update_current_segmentation_status()

  def update_current_segmentation_status(self):
      current_color = self.ui.SlicerDirectoryListView.currentItem().foreground().color()
      if current_color == qt.QColor('black'):
          self.ui.CurrentStatus.setText('Segmentation Status : Not done')
      elif current_color == qt.QColor('orange'):
          self.ui.CurrentStatus.setText('Segmentation Status : Done by another annotator')
      elif current_color == qt.QColor('green'):
          self.ui.CurrentStatus.setText('Segmentation Status : Done by this annotator')
      
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
      self.update_current_segmentation_status()
      
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
      for label in self.config_yaml["labels"]:
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
      # print('self volumenode get display node', self.VolumeNode.GetDisplayNode())
      # print(' node', self.VolumeNode)

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

  def on_annotator_name_changed(self):
      self.update_case_list_colors()
      self.ui.SlicerDirectoryListView.setCurrentItem(self.ui.SlicerDirectoryListView.item(self.currentCase_index))
      self.update_current_segmentation_status()
  
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
        for label in self.config_yaml["labels"]:
            self.onNewLabelSegm(label["name"], label["color_r"], label["color_g"], label["color_b"], label["lower_bound_HU"], label["upper_bound_HU"])
        
        first_label_name = self.config_yaml["labels"][0]["name"]
        first_label_segment_name = first_label_name
        self.onPushButton_select_label(first_label_segment_name, self.config_yaml["labels"][0]["lower_bound_HU"], self.config_yaml["labels"][0]["upper_bound_HU"])

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
  
      if (self.MostRecentPausedCasePath != self.currentCasePath and self.MostRecentPausedCasePath != ""):
        self.timers[self.current_label_index] = Timer(number=self.current_label_index) # new path, new timer
      
      self.timer_router()


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
    
        if not IS_DISPLAY_TIMER_REQUESTED:
            self.enableSegmentAndPaintButtons()
        else:
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
      #allow users to start the timer by clicking on any of the segmentation-related buttons
      if (self.ui.SlicerDirectoryListView.count > 0):
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
          
  def startTimerForActions(self):  
    with TIMER_MUTEX:
        try:
            if not self.flag2:
                self.toggleStartTimerButton()     
        except AttributeError:
            self.toggleStartTimerButton() 


  def resetClassificationInformation(self):
        # Try/Except to prevent crashing when selecting another file in the
        # UI case list if no classification_config_yaml file is already created.
        try :
            self.config_yaml["checkboxes"]
            for i, (objectName, label) in enumerate(self.config_yaml["checkboxes"].items()):
                self.checkboxWidgets[objectName].setChecked(False)
            for i, (comboBoxName, options) in enumerate(self.config_yaml["comboboxes"].items()):
                self.comboboxWidgets[comboBoxName].currentText = list(options.items())[0][1]
            for i, (freeTextBoxObjectName, label) in enumerate(self.config_yaml["freetextboxes"].items()):
                self.freeTextBoxes[freeTextBoxObjectName].setText("")
        except:
            pass

        
  
  def getClassificationInformation(self):
      self.outputClassificationInformationFile = os.path.join(self.currentOutputPath,
                                            '{}_ClassificationInformation.csv'.format(self.currentVolumeFilename))
      header = None
      if os.path.exists(self.outputClassificationInformationFile) and os.path.isfile(self.outputClassificationInformationFile):
            with open(self.outputClassificationInformationFile, 'r') as f:
                header = f.readlines()[0]
    
      label_string = ""
      data_string = ""

      if header is not None:
            label_string = header.split('time,')[1]

            labels = label_string.split(',')

            number_of_checkboxes = len(self.config_yaml["checkboxes"].items())
            number_of_comboboxes = len(self.config_yaml["comboboxes"].items())
            number_of_freetextboxes = len(self.config_yaml["freetextboxes"].items())

            for i, label in enumerate(labels):
                data = ""
                if '\n' in label:
                    label = label.replace('\n', '')
                if 0 <= i < number_of_checkboxes:
                    for _, (objectName, checkbox_label) in enumerate(self.config_yaml["checkboxes"].items()):
                        if label == checkbox_label:
                            data = "No"
                            if self.checkboxWidgets[objectName].isChecked():
                                data = "Yes"
                elif number_of_checkboxes <= i < number_of_checkboxes + number_of_comboboxes:
                    for _, (comboBoxName, options) in enumerate(self.config_yaml["comboboxes"].items()):
                        combobox_label = comboBoxName.replace("_", " ").capitalize()
                        if label == combobox_label:
                            data = self.comboboxWidgets[comboBoxName].currentText
                elif number_of_checkboxes + number_of_comboboxes <= i < number_of_checkboxes + number_of_comboboxes + number_of_freetextboxes:
                    for _, (freeTextBoxObjectName, free_text_label) in enumerate(self.config_yaml["freetextboxes"].items()):
                        if label == free_text_label:
                            data = self.freeTextBoxes[freeTextBoxObjectName].text.replace("\n", " // ")

                if i > 0:
                    data_string = data_string + ","
                data_string = data_string + data

      else:
            for i, (objectName, label) in enumerate(self.config_yaml["checkboxes"].items()):
                if label_string != "":
                    label_string = label_string + ","
                    data_string = data_string + ","
                
                label_string = label_string + label
                
                data = "No"
                if self.checkboxWidgets[objectName].isChecked():
                    data = "Yes"
                
                data_string = data_string + data
            
            for i, (comboBoxName, options) in enumerate(self.config_yaml["comboboxes"].items()):
                label = comboBoxName.replace("_", " ").capitalize()

                if label_string != "":
                    label_string = label_string + ","
                    data_string = data_string + ","
                
                label_string = label_string + label

                data = self.comboboxWidgets[comboBoxName].currentText
                data_string = data_string + data
            
            for i, (freeTextBoxObjectName, label) in enumerate(self.config_yaml["freetextboxes"].items()):
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

      self.update_case_list_colors()

  def qualityControlOfLabels(self):
      is_valid = True 

      segment_names = self.getAllSegmentNames()
      if len(segment_names) != len(self.config_yaml["labels"]):
          msg = qt.QMessageBox()
          msg.setIcon(qt.QMessageBox.Critical)
          msg.setText("ERROR : Incorrect number of labels")
          msg.setInformativeText(f'Expected {len(self.config_yaml["labels"])} labels but obtained {len(segment_names)}. ')
          msg.setWindowTitle("ERROR : Incorrect number of labels")
          msg.exec()
          return False
      
      for i, segment_name in enumerate(segment_names):
          if segment_name != self.config_yaml["labels"][i]["name"]:
              msg = qt.QMessageBox()
              msg.setIcon(qt.QMessageBox.Critical)
              msg.setText("ERROR : Label mismatch")
              msg.setInformativeText(f'Expected {self.config_yaml["labels"][i]["name"]} but obtained {segment_name}. ')
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
    # Header row
    self.previousAction = None
    tag_str = "Volume filename,Segmentation version,Annotator Name,Annotator degree,Revision step,Date and time,Duration"

    for label in self.config_yaml["labels"]:
        tag_str += "," + label["name"] + " duration"

    # Add line detail headers
    for line_key in self.lineDetails:
        tag_str += f",{line_key} ControlPoint1,{line_key} ControlPoint2,{line_key} Length"

    data_str = self.currentCase
    data_str += "," + currentSegmentationVersion
    data_str += "," + self.annotator_name
    data_str += "," + self.annotator_degree
    data_str += "," + self.revision_step[0]
    data_str += "," + datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    data_str += "," + str(self.ui.lcdNumber.value)

    for timer in self.timers:
        data_str += "," + str(timer.total_time)

    # Add line details, ensuring control points are kept in one cell
    for line_key, line_data in self.lineDetails.items():
        control_point1 = ';'.join(map(str, line_data["ControlPoint1"]))  # Join with semicolon
        control_point2 = ';'.join(map(str, line_data["ControlPoint2"]))  # Join with semicolon
        length = line_data["Length"]  # Length is a number, no need for conversion

        # Add control points and length to the data string
        data_str += f",{control_point1},{control_point2},{length}"
        
    self.outputSegmentationInformationFile = os.path.join(self.currentOutputPath,
                                                          f'{self.currentVolumeFilename}_SegmentationInformation.csv')

    if os.path.isfile(self.outputSegmentationInformationFile):
        # Read existing contents
        with open(self.outputSegmentationInformationFile, 'r') as f:
            existing_content = f.readlines()
            existing_content = existing_content[1:] if len(existing_content) > 1 else []

        # Rewrite the file with the new header and existing data
        with open(self.outputSegmentationInformationFile, 'w') as f:
            f.write(tag_str + "\n")  # Write the new header
            f.writelines(existing_content)  # Write the old content

        # Append the new data
        with open(self.outputSegmentationInformationFile, 'a') as f:
            f.write(data_str + "\n")
    else:
        # If the file doesn't exist, create it and write the header and data
        with open(self.outputSegmentationInformationFile, 'w') as f:
            f.write(tag_str + "\n")
            f.write(data_str + "\n")
        
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
      
  def verify_empty(self):
      if self.outputFolder is not None and os.path.exists(self.outputFolder):

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

            path_to_config_copy = f'{path_to_saved_config_files}{os.sep}{CONFIG_COPY_FILENAME}'

            shutil.copy(CONFIG_FILE_PATH, path_to_config_copy)

  def onSelectOutputFolder(self):
      self.outputFolder = qt.QFileDialog.getExistingDirectory(None,"Open a folder", self.DefaultDir, qt.QFileDialog.ShowDirsOnly)

      if REQUIRE_EMPTY: 
          self.verify_empty()
      
      if self.outputFolder is not None:
          self.ui.LoadClassification.setEnabled(True)
          self.ui.LoadSegmentation.setEnabled(True)

          self.ui.SaveSegmentationButton.setEnabled(True)
          self.ui.SaveClassificationButton.setEnabled(True)
          
          if self.CurrentFolder is not None:
                self.updateCurrentOutputPathAndCurrentVolumeFilename()

                self.update_case_list_colors()

                self.ui.SlicerDirectoryListView.setCurrentItem(self.ui.SlicerDirectoryListView.item(self.currentCase_index))
                self.update_current_segmentation_status()

                self.predictions_paths = sorted(glob(os.path.join(self.outputFolder, f'{INPUT_FILE_EXTENSION}')))

  def update_case_list_colors(self):
      if self.outputFolder is None or self.CurrentFolder is None:
          return
      
      segmentation_information_path = f'{self.currentOutputPath}{os.sep}{self.currentVolumeFilename}_SegmentationInformation.csv'
      segmentation_information_df = None
      if os.path.exists(segmentation_information_path):
          segmentation_information_df = pd.read_csv(segmentation_information_path)

          self.ui.SlicerDirectoryListView.clear()
          for case in self.Cases:
            case_id = case.split('.')[0]
            item = qt.QListWidgetItem(case_id)
 
            currentCaseSegmentationStatus = self.get_segmentation_status(case, segmentation_information_df)
            if currentCaseSegmentationStatus == 0:
                item.setForeground(qt.QColor('black'))
            elif currentCaseSegmentationStatus == 1:
                item.setForeground(qt.QColor('orange'))
            elif currentCaseSegmentationStatus == 2:
                item.setForeground(qt.QColor('green'))
            
            self.ui.SlicerDirectoryListView.addItem(item)
      else:
          return
  
  def get_segmentation_status(self, case, segmentation_information_df):
      self.annotator_name = self.ui.Annotator_name.text

      found_case = 0
      if self.annotator_name is None:
            msg = qt.QMessageBox()
            msg.setIcon(qt.QMessageBox.Warning)
            msg.setText("No annotator name defined")
            msg.setInformativeText('The annotator name is empty, therefore, the case list colors are not updated. ')
            msg.setWindowTitle("No annotator name defined")
            msg.exec()

      else:
            for _, row in segmentation_information_df.iterrows():
                if row['Volume filename'] == case and row['Annotator Name'] == self.annotator_name:
                    return 2
                elif row['Volume filename'] == case:
                    found_case = 1
          
      return found_case
          
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
      for label in self.config_yaml['labels']:
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
            for label in self.config_yaml["labels"]:
                if str(label['value']) == str(segment_id):
                    segment = self.segmentationNode.GetSegmentation().GetSegment(segment_id)
                    segment.SetName(label["name"])
                    segment.SetColor(label["color_r"]/255, label["color_g"]/255, label["color_b"]/255)

        list_of_segment_names = self.getAllSegmentNames()
        for label in self.config_yaml["labels"]:
            if label['name'] not in list_of_segment_names:
                self.onNewLabelSegm(label["name"], label["color_r"], label["color_g"], label["color_b"], label["lower_bound_HU"], label["upper_bound_HU"])

        for segment_id in loaded_segment_ids:
            for label in self.config_yaml["labels"]:
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
      with open(CONFIG_FILE_PATH, 'r') as file:
        fresh_config = yaml.safe_load(file)
        self.config_yaml["labels"][self.current_label_index]["lower_bound_HU"] = fresh_config["labels"][self.current_label_index]["lower_bound_HU"]
        self.setUpperAndLowerBoundHU(self.config_yaml["labels"][self.current_label_index]["lower_bound_HU"], self.config_yaml["labels"][self.current_label_index]["upper_bound_HU"])

  def onPushDefaultMax(self):
      with open(CONFIG_FILE_PATH, 'r') as file:
        fresh_config = yaml.safe_load(file)
        self.config_yaml["labels"][self.current_label_index]["upper_bound_HU"] = fresh_config["labels"][self.current_label_index]["upper_bound_HU"]     
        self.setUpperAndLowerBoundHU(self.config_yaml["labels"][self.current_label_index]["lower_bound_HU"], self.config_yaml["labels"][self.current_label_index]["upper_bound_HU"])

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
      if self.previousAction == 'segmentation':  
        self.segmentEditorWidget.undo()

      elif self.previousAction == 'markups':
              # Get the last added markup node (or customize based on specific markup type)
        markupsNodeList = slicer.mrmlScene.GetNodesByClass("vtkMRMLMarkupsNode")
        markupsNodeList.InitTraversal()

        lastMarkupNode = None
        while True:
            markupNode = markupsNodeList.GetNextItemAsObject()
            if markupNode:
                lastMarkupNode = markupNode  # Keep track of the last markup node
            else:
                break

        # Remove the last control point from the markup node (or remove the whole node if needed)
        if lastMarkupNode and lastMarkupNode.GetNumberOfControlPoints() > 0:
            lastMarkupNode.RemoveNthControlPoint(lastMarkupNode.GetNumberOfControlPoints() - 1)
        else:
            slicer.mrmlScene.RemoveNode(lastMarkupNode)  # Remove the whole markup node if no points remain

        removedNode = self.lineDetails.pop(lastMarkupNode.GetName())
        
  def onDropDownButton_label_select(self, value):
      self.current_label_index = value
      label = self.config_yaml["labels"][value]
      self.setUpperAndLowerBoundHU(label["lower_bound_HU"], label["upper_bound_HU"])

      label_name = label["name"]
      try:
        segment_name = label_name
        self.onPushButton_select_label(segment_name, label["lower_bound_HU"], label["upper_bound_HU"])
      except:
        pass 
      
  def onPushLassoPaint(self):
        self.startTimerForActions()
        self.previousAction = 'segmentation'
        self.segmentEditorWidget.setActiveEffectByName("Scissors")
        self.segmentEditorNode.SetMasterVolumeIntensityMask(False)
        effect = self.segmentEditorWidget.activeEffect()
        effect.setParameter("Operation","FillInside")
        effect.setParameter("Shape","FreeForm")
        effect.setSliceCutMode(3)
  
  def onPushButton_Paint(self):
        self.startTimerForActions()
        self.previousAction = 'segmentation'
        selected_segment_id = self.segmentationNode.GetSegmentation().GetSegmentIdBySegmentName(self.config_yaml["labels"][self.current_label_index]['name'])
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
      self.startTimerForActions()
      self.previousAction = 'segmentation'
      if self.ui.pushButton_ToggleFill.isChecked():
          self.ui.pushButton_ToggleFill.setStyleSheet("background-color : yellowgreen")
          self.ui.pushButton_ToggleFill.setText('Fill: ON')
          self.segmentationNode.GetDisplayNode().SetOpacity2DFill(0)
      else:
          self.ui.pushButton_ToggleFill.setStyleSheet("background-color : indianred")
          self.ui.pushButton_ToggleFill.setText('Fill: OFF')
          self.segmentationNode.GetDisplayNode().SetOpacity2DFill(100)

  def onPushButton_ToggleVisibility(self):
      self.startTimerForActions()
      self.previousAction = 'segmentation'
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
      self.startTimerForActions()
      slicer.util.selectModule("SegmentEditor")

  def onPushButton_Erase(self):
      self.startTimerForActions()
      self.previousAction = 'segmentation'
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
      self.startTimerForActions()
      self.previousAction = 'segmentation'
      self.segmentEditorWidget = slicer.modules.segmenteditor.widgetRepresentation().self().editor
      self.segmentEditorWidget.setActiveEffectByName("Smoothing")
      effect = self.segmentEditorWidget.activeEffect()
      effect.setParameter("SmoothingMethod", "MEDIAN")
      effect.setParameter("KernelSizeMm", 3)
      effect.self().onApply()
      
  def onPlacePointsAndConnect(self):
    self.startTimerForActions()
    self.previousAction = 'markups'
    self.lineNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsLineNode")

    lineName = f"Line_{slicer.mrmlScene.GetNumberOfNodesByClass('vtkMRMLMarkupsLineNode')}"
    self.lineNode.SetName(lineName)

    slicer.modules.markups.logic().SetActiveListID(self.lineNode)
    interactionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
    interactionNode.SetCurrentInteractionMode(interactionNode.Place)

    self.lineNode.AddObserver(self.lineNode.PointModifiedEvent, self.onLinePlaced)

  def onLinePlaced(self, caller, event):
    if caller.GetNumberOfControlPoints() < 2:
        return

    # Retrieve the control point coordinates after the user places the points
    p1 = [0, 0, 0]
    p2 = [0, 0, 0]
    caller.GetNthControlPointPosition(0, p1)  # First control point
    caller.GetNthControlPointPosition(1, p2)  # Second control point

    lineLength = caller.GetLineLengthWorld()
    lineName = caller.GetName()

    self.lineDetails[lineName] = {
        "ControlPoint1": p1,
        "ControlPoint2": p2,
        "Length": lineLength
    }

  def onPushButton_Small_holes(self):
      # pass
      # Fill holes smoothing
      self.startTimerForActions()
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
        self.config_yaml["labels"][self.current_label_index]["lower_bound_HU"] = self.LB_HU
      except:
        pass
      
  def onUB_HU(self):
      try:
        self.UB_HU=self.ui.UB_HU.value
        self.set_master_volume_intensity_mask_according_to_modality()
        self.segmentEditorNode.SetSourceVolumeIntensityMaskRange(self.LB_HU, self.UB_HU)
        self.config_yaml["labels"][self.current_label_index]["upper_bound_HU"] = self.UB_HU
      except:
        pass
