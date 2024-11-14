from utils import *

# The class in this file requires the use of another class in the same
# subfolder. Only the used file is imported (not all) to avoid circular imports
from scripts.ConfigureSingleLabelWindow import *
# from scripts.SlicerCARTConfigurationSetupWindow import *
from scripts.Interactions import *

class ConfigureSegmentationWindow(qt.QWidget):
    def __init__(self, segmenter, modality, edit_conf,
                 segmentation_config_yaml=None, label_config_yaml=None,
                 parent=None):
        super(ConfigureSegmentationWindow, self).__init__(parent)

        #   with open(CONFIG_FILE_PATH, 'r') as file:
        #     self.config_yaml = yaml.full_load(file)

        if label_config_yaml is None:
            with open(CONFIG_FILE_PATH, 'r') as file:
                self.config_yaml = yaml.full_load(file)
        else:
            self.config_yaml = label_config_yaml

        self.segmenter = segmenter
        self.modality = modality
        self.edit_conf = edit_conf

        layout = qt.QVBoxLayout()

        self.label_table_view = qt.QTableWidget()
        layout.addWidget(self.label_table_view)

        if len(self.config_yaml['labels']) > 0:
            number_of_labels = len(self.config_yaml['labels'])

            self.label_table_view.setRowCount(number_of_labels)
            if self.modality == 'MRI':
                self.label_table_view.setColumnCount(
                    5)  # edit button, remove button, name, value, color
            elif self.modality == 'CT':
                self.label_table_view.setColumnCount(
                    7)  # edit button, remove button, name, value, color, range HU min, range HU max
            self.label_table_view.horizontalHeader().setStretchLastSection(True)
            self.label_table_view.horizontalHeader().setSectionResizeMode(
                qt.QHeaderView.Stretch)

            for index, label in enumerate(self.config_yaml['labels']):
                edit_button = qt.QPushButton('Edit')
                edit_button.clicked.connect(
                    lambda state, label=label: self.push_edit_button(label))
                edit_button_hbox = qt.QHBoxLayout()
                edit_button_hbox.addWidget(edit_button)
                edit_button_hbox.setAlignment(qt.Qt.AlignCenter)
                edit_button_hbox.setContentsMargins(0, 0, 0, 0)
                edit_button_widget = qt.QWidget()
                edit_button_widget.setLayout(edit_button_hbox)
                self.label_table_view.setCellWidget(index, 0,
                                                    edit_button_widget)
                self.label_table_view.setHorizontalHeaderItem(0,
                                                              qt.QTableWidgetItem(
                                                                  ''))

                remove_button = qt.QPushButton('Remove')
                remove_button.clicked.connect(
                    lambda state, label=label: self.push_remove_button(label))
                remove_button_hbox = qt.QHBoxLayout()
                remove_button_hbox.addWidget(remove_button)
                remove_button_hbox.setAlignment(qt.Qt.AlignCenter)
                remove_button_hbox.setContentsMargins(0, 0, 0, 0)
                remove_button_widget = qt.QWidget()
                remove_button_widget.setLayout(remove_button_hbox)
                self.label_table_view.setCellWidget(index, 1,
                                                    remove_button_widget)
                self.label_table_view.setHorizontalHeaderItem(1,
                                                              qt.QTableWidgetItem(
                                                                  ''))

                if self.edit_conf:
                    remove_button.setEnabled(False)

                cell = qt.QTableWidgetItem(label['name'])
                cell.setFlags(qt.Qt.NoItemFlags)
                cell.setForeground(qt.QBrush(qt.QColor(0, 0, 0)))
                self.label_table_view.setItem(index, 2, cell)
                self.label_table_view.setHorizontalHeaderItem(2,
                                                              qt.QTableWidgetItem(
                                                                  'Name'))

                cell = qt.QTableWidgetItem(str(label['value']))
                cell.setFlags(qt.Qt.NoItemFlags)
                cell.setForeground(qt.QBrush(qt.QColor(0, 0, 0)))
                self.label_table_view.setItem(index, 3, cell)
                self.label_table_view.setHorizontalHeaderItem(3,
                                                              qt.QTableWidgetItem(
                                                                  'Value'))

                cell = qt.QTableWidgetItem('')
                cell.setFlags(qt.Qt.NoItemFlags)
                cell.setBackground(qt.QBrush(
                    qt.QColor(label['color_r'], label['color_g'],
                              label['color_b'])))
                self.label_table_view.setItem(index, 4, cell)
                self.label_table_view.setHorizontalHeaderItem(4,
                                                              qt.QTableWidgetItem(
                                                                  'Colour'))

                if self.modality == 'CT':
                    cell = qt.QTableWidgetItem(str(label['lower_bound_HU']))
                    cell.setFlags(qt.Qt.NoItemFlags)
                    cell.setForeground(qt.QBrush(qt.QColor(0, 0, 0)))
                    self.label_table_view.setItem(index, 5, cell)
                    self.label_table_view.setHorizontalHeaderItem(5,
                                                                  qt.QTableWidgetItem(
                                                                      'Min. HU'))

                    cell = qt.QTableWidgetItem(str(label['upper_bound_HU']))
                    cell.setFlags(qt.Qt.NoItemFlags)
                    cell.setForeground(qt.QBrush(qt.QColor(0, 0, 0)))
                    self.label_table_view.setItem(index, 6, cell)
                    self.label_table_view.setHorizontalHeaderItem(6,
                                                                  qt.QTableWidgetItem(
                                                                      'Max. HU'))

        self.label_table_view.setSizePolicy(qt.QSizePolicy.Expanding,
                                            qt.QSizePolicy.Fixed)

        self.add_label_button = qt.QPushButton('Add Label')
        self.add_label_button.clicked.connect(self.push_add_label)
        layout.addWidget(self.add_label_button)

        display_timer_hbox = qt.QHBoxLayout()

        self.display_timer_label = qt.QLabel(
            'Display timer during segmentation? ')
        self.display_timer_label.setStyleSheet("font-weight: bold")
        display_timer_hbox.addWidget(self.display_timer_label)

        self.display_timer_checkbox = qt.QCheckBox()
        display_timer_hbox.addWidget(self.display_timer_checkbox)

        layout.addLayout(display_timer_hbox)

        self.apply_button = qt.QPushButton('Apply')
        layout.addWidget(self.apply_button)

        self.cancel_button = qt.QPushButton('Cancel')
        layout.addWidget(self.cancel_button)

        self.populate_default_values()
        self.connect_buttons_to_callbacks()

        self.setLayout(layout)
        self.setWindowTitle("Configure Segmentation")
        self.resize(500, 600)


    Interactions

    # def push_add_label(self):
    #     self.close()
    #     configureSingleLabelWindow = ConfigureSingleLabelWindow(self.segmenter,
    #                                                             self.modality,
    #                                                             self.edit_conf,
    #                                                             self.config_yaml)
    #     configureSingleLabelWindow.show()
    #
    # def push_edit_button(self, label):
    #     self.close()
    #
    #     configureSingleLabelWindow = ConfigureSingleLabelWindow(self.segmenter,
    #                                                             self.modality,
    #                                                             self.edit_conf,
    #                                                             self.config_yaml,
    #                                                             label)
    #     configureSingleLabelWindow.show()

    def push_remove_button(self, label):
        self.close()

        value_removed = -1
        for l in self.config_yaml['labels']:
            if l['name'] == label['name']:
                value_removed = l['value']
                self.config_yaml['labels'].remove(l)

        for l in self.config_yaml['labels']:
            if l['value'] > value_removed and value_removed != -1:
                l['value'] = l['value'] - 1

        with open(CONFIG_FILE_PATH, 'w') as file:
            yaml.safe_dump(self.config_yaml, file)

        configureSegmentationWindow = ConfigureSegmentationWindow(
            self.segmenter, self.modality, self.edit_conf, self.config_yaml)
        configureSegmentationWindow.show()

    def set_default_values(self):
        self.config_yaml[
            'is_display_timer_requested'] = self.display_timer_checkbox.isChecked()

    def populate_default_values(self):
        self.display_timer_selected = self.config_yaml[
            'is_display_timer_requested']
        self.display_timer_checkbox.setChecked(self.display_timer_selected)

    def connect_buttons_to_callbacks(self):
        self.apply_button.clicked.connect(self.push_apply)
        self.cancel_button.clicked.connect(self.push_cancel)

    def push_apply(self):
        self.config_yaml[
            'is_display_timer_requested'] = self.display_timer_checkbox.isChecked()

        if len(self.config_yaml['labels']) == 0:
            msg = qt.QMessageBox()
            msg.setWindowTitle('ERROR : Label list is empty')
            msg.setText(
                'The label list cannot be empty. Using the previous label configuration. ')
            msg.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
            msg.buttonClicked.connect(self.push_error_label_list_empty)
            msg.exec()
        else:
            with open(CONFIG_FILE_PATH, 'w') as file:
                yaml.safe_dump(self.config_yaml, file)

        if self.edit_conf and self.segmenter.outputFolder is not None and os.path.exists(
                f'{self.segmenter.outputFolder}{os.sep}{CONF_FOLDER_NAME}'):
            shutil.copy(CONFIG_FILE_PATH,
                        f'{self.segmenter.outputFolder}{os.sep}{CONF_FOLDER_NAME}{os.sep}{CONFIG_COPY_FILENAME}')

        slicerCARTConfigurationSetupWindow = SlicerCARTConfigurationSetupWindow(
            self.segmenter)
        slicerCARTConfigurationSetupWindow.show()
        self.close()

    def push_error_label_list_empty(self):
        self.push_cancel()

    def push_cancel(self):
        slicerCARTConfigurationSetupWindow = SlicerCARTConfigurationSetupWindow(
            self.segmenter)
        slicerCARTConfigurationSetupWindow.show()
        self.close()

    # combine the action of going back to configuration setup into one
    def go_back_to_configuration_setup_window(self):
        slicerCARTConfigurationSetupWindow = SlicerCARTConfigurationSetupWindow(
            self.segmenter)
        slicerCARTConfigurationSetupWindow.show()
