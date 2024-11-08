# add imports


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
           elif selected_version_df.at[0, label] == 'No' or str(selected_version_df.at[0, label]) == 'nan':
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
