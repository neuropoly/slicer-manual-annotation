# add imports
from utils import *
from . import *

class ConfigureSingleClassificationItemWindow(qt.QWidget):
    def __init__(self, segmenter, classification_config_yaml, item_added,
                 edit_conf, parent=None):
        super(ConfigureSingleClassificationItemWindow, self).__init__(parent)

        self.segmenter = segmenter
        self.config_yaml = classification_config_yaml
        self.item_added = item_added
        self.edit_conf = edit_conf

        layout = qt.QVBoxLayout()

        name_hbox = qt.QHBoxLayout()

        name_label = qt.QLabel('Item Name : ')
        name_label.setStyleSheet("font-weight: bold")
        name_hbox.addWidget(name_label)

        self.name_line_edit = qt.QLineEdit('')
        name_hbox.addWidget(self.name_line_edit)

        layout.addLayout(name_hbox)

        if self.item_added == 'combobox':
            options_hbox = qt.QHBoxLayout()

            options_label = qt.QLabel('Options : ')
            options_label.setStyleSheet("font-weight: bold")
            options_hbox.addWidget(options_label)

            self.options_combobox = qt.QComboBox()
            self.options_combobox.setEditable(True)

            options_hbox.addWidget(self.options_combobox)

            layout.addLayout(options_hbox)

        self.save_button = qt.QPushButton('Save')
        self.save_button.clicked.connect(self.push_save)
        layout.addWidget(self.save_button)

        self.cancel_button = qt.QPushButton('Cancel')
        self.cancel_button.clicked.connect(self.push_cancel)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)
        self.setWindowTitle("Configure Classification Item")
        self.resize(200, 100)

    def push_save(self):
        current_label_name = self.name_line_edit.text
        object_name = current_label_name.replace(' ', '_')

        if self.item_added == 'checkbox':
            label_found = False
            for i, (_, label) in enumerate(
                    self.config_yaml['checkboxes'].items()):
                if label == current_label_name:
                    label_found = True

            if label_found == False:
                # append
                self.config_yaml['checkboxes'].update(
                    {object_name: current_label_name.capitalize()})
        elif self.item_added == 'combobox':
            if self.options_combobox.count == 0:
                msg = qt.QMessageBox()
                msg.setWindowTitle('ERROR : No Drop Down Options Defined')
                msg.setText(
                    'At least one drop down option must be defined. The previous classification configuration will be used. ')
                msg.setStandardButtons(
                    qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
                msg.buttonClicked.connect(
                    self.push_error_no_dropdown_option_defined)
                msg.exec()
            else:
                options_dict = {}
                combobox_option_items = [self.options_combobox.itemText(i) for i
                                         in range(self.options_combobox.count)]
                for option in combobox_option_items:
                    options_dict.update({option.replace(' ', '_'): option})

                item_found = False
                for i, (combobox_name, _) in enumerate(
                        self.config_yaml['comboboxes'].items()):
                    if combobox_name == object_name:
                        item_found = True

                if item_found == False:
                    # append
                    self.config_yaml['comboboxes'].update(
                        {object_name: options_dict})
        elif self.item_added == 'freetextbox':
            label_found = False
            for i, (_, label) in enumerate(
                    self.config_yaml['freetextboxes'].items()):
                if label == current_label_name:
                    label_found = True

            if label_found == False:
                # append
                self.config_yaml['freetextboxes'].update(
                    {object_name: current_label_name.capitalize()})

        configureClassificationWindow = ConfigureClassificationWindow(
            self.segmenter, self.edit_conf, self.config_yaml)
        configureClassificationWindow.show()
        self.close()

    def push_error_no_dropdown_option_defined(self):
        self.push_cancel()

    def push_cancel(self):
        configureClassificationWindow = ConfigureClassificationWindow(
            self.segmenter, self.edit_conf, self.config_yaml)
        configureClassificationWindow.show()
        self.close()