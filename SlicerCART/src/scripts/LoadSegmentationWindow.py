from utils import *

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
                cell.setForeground(qt.QBrush(qt.QColor(self.segmenter.foreground)))
                self.versionTableView.setItem(index, 0, cell)
                self.versionTableView.setHorizontalHeaderItem(0, qt.QTableWidgetItem('Version'))

                cell = qt.QTableWidgetItem(row['Annotator Name'])
                cell.setFlags(qt.Qt.NoItemFlags)
                cell.setForeground(qt.QBrush(qt.QColor(self.segmenter.foreground)))
                self.versionTableView.setItem(index, 1, cell)
                self.versionTableView.setHorizontalHeaderItem(1, qt.QTableWidgetItem('Annotator'))

                cell = qt.QTableWidgetItem(row['Annotator degree'])
                cell.setFlags(qt.Qt.NoItemFlags)
                cell.setForeground(qt.QBrush(qt.QColor(self.segmenter.foreground)))
                self.versionTableView.setItem(index, 2, cell)
                self.versionTableView.setHorizontalHeaderItem(2, qt.QTableWidgetItem('Degree'))

                cell = qt.QTableWidgetItem(row['Date and time'])
                cell.setFlags(qt.Qt.NoItemFlags)
                cell.setForeground(qt.QBrush(qt.QColor(self.segmenter.foreground)))
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
       if "nii" in ConfigPath.INPUT_FILE_EXTENSION:
           segmentation_file_extension = ".nii.gz"
       elif "nrrd" in ConfigPath.INPUT_FILE_EXTENSION:
           segmentation_file_extension = ".seg.nrrd"

       absolute_path_to_segmentation = f'{self.segmenter.currentOutputPath}{os.sep}{self.segmenter.currentVolumeFilename}_{selected_version}{segmentation_file_extension}'
       self.segmenter.loadSegmentation(absolute_path_to_segmentation)

       self.close()

   def pushCancel(self):
       self.close()