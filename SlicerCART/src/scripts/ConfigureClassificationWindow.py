from utils import *

from scripts.ConfigureSingleClassificationItemWindow import *

class ConfigureClassificationWindow(qt.QWidget):
    def __init__(self, segmenter, edit_conf, classification_config_yaml=None,
                 parent=None):
        super(ConfigureClassificationWindow, self).__init__(parent)

        self.segmenter = segmenter
        self.edit_conf = edit_conf

        if classification_config_yaml is None:
            with open(CONFIG_FILE_PATH, 'r') as file:
                self.config_yaml = yaml.full_load(file)
        else:
            self.config_yaml = classification_config_yaml

        layout = qt.QVBoxLayout()

        self.checkbox_table_view = qt.QTableWidget()
        layout.addWidget(self.checkbox_table_view)

        if len(self.config_yaml['checkboxes']) > 0:
            number_of_checkboxes = len(self.config_yaml['checkboxes'])

            self.checkbox_table_view.setRowCount(number_of_checkboxes)
            self.checkbox_table_view.setColumnCount(2)
            self.checkbox_table_view.horizontalHeader().setStretchLastSection(
                True)
            self.checkbox_table_view.horizontalHeader().setSectionResizeMode(
                qt.QHeaderView.Stretch)

            for index, (objectName, checkbox_label) in enumerate(
                    self.config_yaml["checkboxes"].items()):
                remove_button = qt.QPushButton('Remove')
                remove_button.clicked.connect(lambda state,
                                                     checkbox_label=checkbox_label: self.push_remove_checkbox_button(
                    checkbox_label))
                remove_button_hbox = qt.QHBoxLayout()
                remove_button_hbox.addWidget(remove_button)
                remove_button_hbox.setAlignment(qt.Qt.AlignCenter)
                remove_button_hbox.setContentsMargins(0, 0, 0, 0)
                remove_button_widget = qt.QWidget()
                remove_button_widget.setLayout(remove_button_hbox)
                self.checkbox_table_view.setCellWidget(index, 0,
                                                       remove_button_widget)
                self.checkbox_table_view.setHorizontalHeaderItem(0,
                                                                 qt.QTableWidgetItem(
                                                                     ''))

                if self.edit_conf:
                    remove_button.setEnabled(False)

                cell = qt.QTableWidgetItem(checkbox_label)
                cell.setFlags(qt.Qt.NoItemFlags)
                cell.setForeground(qt.QBrush(qt.QColor(0, 0, 0)))
                self.checkbox_table_view.setItem(index, 1, cell)
                self.checkbox_table_view.setHorizontalHeaderItem(1,
                                                                 qt.QTableWidgetItem(
                                                                     'Label'))

        self.add_checkbox_button = qt.QPushButton('Add Checkbox')
        self.add_checkbox_button.clicked.connect(self.push_add_checkbox)
        layout.addWidget(self.add_checkbox_button)

        self.combobox_table_view = qt.QTableWidget()
        layout.addWidget(self.combobox_table_view)

        if len(self.config_yaml['comboboxes']) > 0:
            number_of_comboboxes = len(self.config_yaml['comboboxes'])

            self.combobox_table_view.setRowCount(number_of_comboboxes)
            self.combobox_table_view.setColumnCount(3)
            self.combobox_table_view.horizontalHeader().setStretchLastSection(
                True)
            self.combobox_table_view.horizontalHeader().setSectionResizeMode(
                qt.QHeaderView.Stretch)
            self.combobox_table_view.verticalHeader().setSectionResizeMode(
                qt.QHeaderView.Stretch)

            for index, (combo_box_name, combo_box_options) in enumerate(
                    self.config_yaml["comboboxes"].items()):
                remove_button = qt.QPushButton('Remove')
                remove_button.clicked.connect(lambda state,
                                                     combo_box_name=combo_box_name: self.push_remove_combobox_button(
                    combo_box_name))
                remove_button_hbox = qt.QHBoxLayout()
                remove_button_hbox.addWidget(remove_button)
                remove_button_hbox.setAlignment(qt.Qt.AlignCenter)
                remove_button_hbox.setContentsMargins(0, 0, 0, 0)
                remove_button_widget = qt.QWidget()
                remove_button_widget.setLayout(remove_button_hbox)
                self.combobox_table_view.setCellWidget(index, 0,
                                                       remove_button_widget)
                self.combobox_table_view.setHorizontalHeaderItem(0,
                                                                 qt.QTableWidgetItem(
                                                                     ''))

                if self.edit_conf:
                    remove_button.setEnabled(False)

                cell = qt.QTableWidgetItem(
                    combo_box_name.replace('_', ' ').capitalize())
                cell.setFlags(qt.Qt.NoItemFlags)
                cell.setForeground(qt.QBrush(qt.QColor(0, 0, 0)))
                self.combobox_table_view.setItem(index, 1, cell)
                self.combobox_table_view.setHorizontalHeaderItem(1,
                                                                 qt.QTableWidgetItem(
                                                                     'Label'))

                combobox = qt.QComboBox()
                for i, (name, label) in enumerate(combo_box_options.items()):
                    combobox.addItem(label)

                combobox_hbox = qt.QHBoxLayout()
                combobox_hbox.addWidget(combobox)
                combobox_hbox.setAlignment(qt.Qt.AlignCenter)
                combobox_hbox.setContentsMargins(0, 0, 0, 0)
                widget = qt.QWidget()
                widget.setLayout(combobox_hbox)
                self.combobox_table_view.setCellWidget(index, 2, widget)
                self.combobox_table_view.setHorizontalHeaderItem(2,
                                                                 qt.QTableWidgetItem(
                                                                     ''))

        self.add_combobox_button = qt.QPushButton('Add Drop Down')
        self.add_combobox_button.clicked.connect(self.push_add_combobox)
        layout.addWidget(self.add_combobox_button)

        self.freetext_table_view = qt.QTableWidget()
        layout.addWidget(self.freetext_table_view)

        if len(self.config_yaml['freetextboxes']) > 0:
            number_of_freetextboxes = len(self.config_yaml['freetextboxes'])

            self.freetext_table_view.setRowCount(number_of_freetextboxes)
            self.freetext_table_view.setColumnCount(2)
            self.freetext_table_view.horizontalHeader().setStretchLastSection(
                True)
            self.freetext_table_view.horizontalHeader().setSectionResizeMode(
                qt.QHeaderView.Stretch)

            for index, (objectName, freetextbox_label) in enumerate(
                    self.config_yaml["freetextboxes"].items()):
                remove_button = qt.QPushButton('Remove')
                remove_button.clicked.connect(lambda state,
                                                     freetextbox_label=freetextbox_label: self.push_remove_freetextbox_button(
                    freetextbox_label))
                remove_button_hbox = qt.QHBoxLayout()
                remove_button_hbox.addWidget(remove_button)
                remove_button_hbox.setAlignment(qt.Qt.AlignCenter)
                remove_button_hbox.setContentsMargins(0, 0, 0, 0)
                remove_button_widget = qt.QWidget()
                remove_button_widget.setLayout(remove_button_hbox)
                self.freetext_table_view.setCellWidget(index, 0,
                                                       remove_button_widget)
                self.freetext_table_view.setHorizontalHeaderItem(0,
                                                                 qt.QTableWidgetItem(
                                                                     ''))

                if self.edit_conf:
                    remove_button.setEnabled(False)

                cell = qt.QTableWidgetItem(freetextbox_label)
                cell.setFlags(qt.Qt.NoItemFlags)
                cell.setForeground(qt.QBrush(qt.QColor(0, 0, 0)))
                self.freetext_table_view.setItem(index, 1, cell)
                self.freetext_table_view.setHorizontalHeaderItem(1,
                                                                 qt.QTableWidgetItem(
                                                                     'Label'))

        self.add_freetextbox_button = qt.QPushButton('Add Text Field')
        self.add_freetextbox_button.clicked.connect(self.push_add_freetextbox)
        layout.addWidget(self.add_freetextbox_button)

        self.save_button = qt.QPushButton('Save')
        self.save_button.clicked.connect(self.push_save)
        layout.addWidget(self.save_button)

        self.cancel_button = qt.QPushButton('Cancel')
        self.cancel_button.clicked.connect(self.push_cancel)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)
        self.setWindowTitle("Configure Classification")
        self.resize(500, 600)

    def push_remove_combobox_button(self, combo_box_name):
        self.close()

        self.config_yaml['comboboxes'].pop(combo_box_name, None)

        configureClassificationWindow = ConfigureClassificationWindow(
            self.segmenter, self.edit_conf, self.config_yaml)
        configureClassificationWindow.show()

    def push_remove_checkbox_button(self, checkbox_label):
        self.close()

        object_name_to_remove = None

        for i, (object_name, label) in enumerate(
                self.config_yaml['checkboxes'].items()):
            if label == checkbox_label:
                object_name_to_remove = object_name

        if object_name_to_remove is not None:
            self.config_yaml['checkboxes'].pop(object_name_to_remove, None)

        configureClassificationWindow = ConfigureClassificationWindow(
            self.segmenter, self.edit_conf, self.config_yaml)
        configureClassificationWindow.show()

    def push_remove_freetextbox_button(self, freetextbox_label):
        self.close()

        object_name_to_remove = None

        for i, (object_name, label) in enumerate(
                self.config_yaml['freetextboxes'].items()):
            if label == freetextbox_label:
                object_name_to_remove = object_name

        if object_name_to_remove is not None:
            self.config_yaml['freetextboxes'].pop(object_name_to_remove, None)

        configureClassificationWindow = ConfigureClassificationWindow(
            self.segmenter, self.edit_conf, self.config_yaml)
        configureClassificationWindow.show()

    # def push_add_freetextbox(self):
    #     self.close()
    #
    #     configureSingleClassificationItemWindow = ConfigureSingleClassificationItemWindow(
    #         self.segmenter, self.config_yaml, 'freetextbox', self.edit_conf)
    #     configureSingleClassificationItemWindow.show()
    #
    # def push_add_combobox(self):
    #     self.close()
    #
    #     configureSingleClassificationItemWindow = ConfigureSingleClassificationItemWindow(
    #         self.segmenter, self.config_yaml, 'combobox', self.edit_conf)
    #     configureSingleClassificationItemWindow.show()
    #
    # def push_add_checkbox(self):
    #     self.close()
    #
    #     configureSingleClassificationItemWindow = ConfigureSingleClassificationItemWindow(
    #         self.segmenter, self.config_yaml, 'checkbox', self.edit_conf)
    #     configureSingleClassificationItemWindow.show()

    def push_save(self):
        with open(CONFIG_FILE_PATH, 'w') as file:
            yaml.safe_dump(self.config_yaml, file)

        if self.edit_conf:
            if self.segmenter.outputFolder is not None and os.path.exists(
                    self.segmenter.outputFolder):
                list_of_paths_to_classification_information_files = sorted(glob(
                    f'{self.segmenter.outputFolder}{os.sep}**{os.sep}*ClassificationInformation.csv',
                    recursive=True))

                for path in list_of_paths_to_classification_information_files:
                    with open(path, 'r+') as file:
                        lines = file.readlines()

                        indices_to_populate_with_empty = []
                        total_number_of_items_in_new_setup = len(
                            self.config_yaml['checkboxes'].items()) + len(
                            self.config_yaml['comboboxes'].items()) + len(
                            self.config_yaml['freetextboxes'].items())

                        for i in range(len(lines)):
                            if i == 0:
                                header = lines[0]

                                header_items = header.split(',')

                                header_item_counter = 6  # start of the classification items
                                new_header = header_items[0] + ',' + \
                                             header_items[1] + ',' + \
                                             header_items[2] + ',' + \
                                             header_items[3] + ',' + \
                                             header_items[4] + ',' + \
                                             header_items[5]

                                for j, (_, label) in enumerate(
                                        self.config_yaml['checkboxes'].items()):
                                    if header_items[
                                        header_item_counter] == label:
                                        header_item_counter = header_item_counter + 1
                                    else:
                                        indices_to_populate_with_empty.append(
                                            j + 6)
                                    new_header = new_header + ',' + label

                                for j, (combo_box_name, _) in enumerate(
                                        self.config_yaml["comboboxes"].items()):
                                    name = combo_box_name.replace('_',
                                                                  ' ').capitalize()
                                    if header_items[
                                        header_item_counter] == name:
                                        header_item_counter = header_item_counter + 1
                                    else:
                                        indices_to_populate_with_empty.append(
                                            j + 6 + len(self.config_yaml[
                                                            'checkboxes'].items()))
                                    new_header = new_header + ',' + name

                                for j, (_, label) in enumerate(self.config_yaml[
                                                                   'freetextboxes'].items()):
                                    if header_item_counter < len(
                                            header_items) and '\n' in \
                                            header_items[header_item_counter]:
                                        header_items[header_item_counter] = \
                                        header_items[header_item_counter].split(
                                            '\n')[0]

                                    if header_item_counter < len(
                                            header_items) and header_items[
                                        header_item_counter] == label:
                                        header_item_counter = header_item_counter + 1
                                    else:
                                        indices_to_populate_with_empty.append(
                                            j + 6 + len(self.config_yaml[
                                                            'checkboxes'].items()) + len(
                                                self.config_yaml[
                                                    "comboboxes"].items()))
                                    new_header = new_header + ',' + label
                                lines[0] = new_header
                            else:
                                line = '\n' + lines[i]

                                line_items = line.split(',')

                                item_counter = 6  # start of the classification items
                                new_line = line_items[0] + ',' + line_items[
                                    1] + ',' + line_items[2] + ',' + line_items[
                                               3] + ',' + line_items[4] + ',' + \
                                           line_items[5]

                                for j in range(6,
                                               total_number_of_items_in_new_setup + 6):
                                    if j in indices_to_populate_with_empty:
                                        new_line = new_line + ','
                                    else:
                                        if '\n' in line_items[item_counter]:
                                            line_items[item_counter] = \
                                            line_items[item_counter].replace(
                                                '\n', '')
                                        new_line = new_line + ',' + line_items[
                                            item_counter]
                                        item_counter = item_counter + 1
                                lines[i] = new_line
                        file.truncate(0)
                        file.seek(0)
                        file.writelines(lines)
        slicerCARTConfigurationSetupWindow = SlicerCARTConfigurationSetupWindow(
            self.segmenter)
        slicerCARTConfigurationSetupWindow.show()
        self.close()

    def push_cancel(self):
        slicerCARTConfigurationSetupWindow = SlicerCARTConfigurationSetupWindow(
            self.segmenter)
        slicerCARTConfigurationSetupWindow.show()
        self.close()
