# add improts
from utils import *
# from . import *

class ConfigureSingleLabelWindow(qt.QWidget):
    def __init__(self, segmenter, modality, edit_conf, label_config_yaml,
                 label=None, parent=None):
        super(ConfigureSingleLabelWindow, self).__init__(parent)

        self.segmenter = segmenter
        self.modality = modality
        self.initial_label = label
        self.config_yaml = label_config_yaml
        self.edit_conf = edit_conf

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
        self.value_line_edit.setEnabled(
            False)  # To be changed at resolution of Issue #28
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
        self.color_r_line_edit.setInputMask("000")
        self.color_r_line_edit.textChanged.connect(self.color_line_edit_changed)
        color_hbox.addWidget(self.color_r_line_edit)

        self.color_g_line_edit = qt.QLineEdit('G')
        self.color_g_line_edit.setValidator(colorValidator)
        self.color_g_line_edit.setInputMask("000")
        self.color_g_line_edit.textChanged.connect(self.color_line_edit_changed)
        color_hbox.addWidget(self.color_g_line_edit)

        self.color_b_line_edit = qt.QLineEdit('B')
        # self.color_b_line_edit.setValidator(colorValidator)
        self.color_b_line_edit.setInputMask("000")
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
            self.min_hu_line_edit.setInputMask("0000")
            min_hu_hbox.addWidget(self.min_hu_line_edit)

            layout.addLayout(min_hu_hbox)

            max_hu_hbox = qt.QHBoxLayout()

            max_hu_label = qt.QLabel('Max. HU : ')
            max_hu_label.setStyleSheet("font-weight: bold")
            max_hu_hbox.addWidget(max_hu_label)

            self.max_hu_line_edit = qt.QLineEdit('')
            self.max_hu_line_edit.setValidator(qt.QIntValidator())
            self.max_hu_line_edit.setInputMask("0000")
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
                self.min_hu_line_edit.setText(
                    self.initial_label['lower_bound_HU'])
                self.max_hu_line_edit.setText(
                    self.initial_label['upper_bound_HU'])

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
        for label in self.config_yaml['labels']:
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
            new_label = {'color_b': 10, 'color_g': 10, 'color_r': 255,
                         'lower_bound_HU': 30, 'name': 'ICH',
                         'upper_bound_HU': 90, 'value': 1}
            new_label['name'] = self.name_line_edit.text
            new_label['value'] = len(self.config_yaml['labels']) + 1
            new_label['color_r'] = int(self.color_r_line_edit.text)
            new_label['color_g'] = int(self.color_g_line_edit.text)
            new_label['color_b'] = int(self.color_b_line_edit.text)

            if self.modality == 'CT':
                new_label['lower_bound_HU'] = int(self.min_hu_line_edit.text)
                new_label['upper_bound_HU'] = int(self.max_hu_line_edit.text)
            self.config_yaml['labels'].append(new_label)

        with open(CONFIG_FILE_PATH, 'w') as file:
            yaml.safe_dump(self.config_yaml, file)

        self.configureSegmentationWindow = ConfigureSegmentationWindow(
            self.segmenter, self.modality, self.edit_conf)
        self.configureSegmentationWindow.show()
        self.close()

    def push_cancel(self):
        self.configureSegmentationWindow = ConfigureSegmentationWindow(
            self.segmenter, self.modality, self.edit_conf)
        self.configureSegmentationWindow.show()
        self.close()
