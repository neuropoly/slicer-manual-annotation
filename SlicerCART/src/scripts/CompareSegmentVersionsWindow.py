from utils import *

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
