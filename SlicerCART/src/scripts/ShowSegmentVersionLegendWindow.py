# add improts


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
