class SlicerCARTConfigurationSetupWindow(qt.QWidget):
    def __init__(self, segmenter, conf_folder_path=None, edit_conf=False,
                 parent=None):
        super(SlicerCARTConfigurationSetupWindow, self).__init__(parent)

        self.edit_conf = edit_conf

        if conf_folder_path is not None:
            shutil.copy(f'{conf_folder_path}{os.sep}{CONFIG_COPY_FILENAME}',
                        CONFIG_FILE_PATH)

        with open(CONFIG_FILE_PATH, 'r') as file:
            self.config_yaml = yaml.full_load(file)

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

        self.ct_window_level_line_edit = qt.QLineEdit(
            self.ct_window_level_selected)
        onlyInt = qt.QIntValidator()
        self.ct_window_level_line_edit.setValidator(onlyInt)
        self.ct_window_level_line_edit.setInputMask("0000;x")
        ct_window_level_hbox.addWidget(self.ct_window_level_line_edit)

        layout.addLayout(ct_window_level_hbox)

        ct_window_width_hbox = qt.QHBoxLayout()

        self.ct_window_width_label = qt.QLabel()
        self.ct_window_width_label.setText('Window Width : ')
        self.ct_window_width_label.setStyleSheet("font-weight: bold")
        ct_window_width_hbox.addWidget(self.ct_window_width_label)

        self.ct_window_width_line_edit = qt.QLineEdit(
            self.ct_window_width_selected)
        self.ct_window_width_line_edit.setValidator(onlyInt)
        self.ct_window_width_line_edit.setInputMask("0000")
        ct_window_width_hbox.addWidget(self.ct_window_width_line_edit)

        layout.addLayout(ct_window_width_hbox)

        keyboard_shortcuts_hbox = qt.QHBoxLayout()

        keyboard_shortcuts_label = qt.QLabel('Use Custom Keyboard Shortcuts? ')
        keyboard_shortcuts_label.setStyleSheet("font-weight: bold")
        keyboard_shortcuts_hbox.addWidget(keyboard_shortcuts_label)

        self.keyboard_shortcuts_checkbox = qt.QCheckBox()
        keyboard_shortcuts_hbox.addWidget(self.keyboard_shortcuts_checkbox)

        layout.addLayout(keyboard_shortcuts_hbox)

        toggle_fill_ks_hbox = qt.QHBoxLayout()

        self.toggle_fill_ks_label = qt.QLabel()
        self.toggle_fill_ks_label.setText('Toggle Fill Keyboard Shortcut : ')
        self.toggle_fill_ks_label.setStyleSheet("font-style: italic")
        toggle_fill_ks_hbox.addWidget(self.toggle_fill_ks_label)

        self.toggle_fill_ks_line_edit = qt.QLineEdit(
            self.toggle_fill_ks_selected)
        self.toggle_fill_ks_line_edit.setMaxLength(1)
        toggle_fill_ks_hbox.addWidget(self.toggle_fill_ks_line_edit)

        layout.addLayout(toggle_fill_ks_hbox)

        toggle_visibility_ks_hbox = qt.QHBoxLayout()

        self.toggle_visibility_ks_label = qt.QLabel()
        self.toggle_visibility_ks_label.setText(
            'Toggle Visibility Keyboard Shortcut : ')
        self.toggle_visibility_ks_label.setStyleSheet("font-style: italic")
        toggle_visibility_ks_hbox.addWidget(self.toggle_visibility_ks_label)

        self.toggle_visibility_ks_line_edit = qt.QLineEdit(
            self.toggle_visibility_ks_selected)
        self.toggle_visibility_ks_line_edit.setMaxLength(1)
        toggle_visibility_ks_hbox.addWidget(self.toggle_visibility_ks_line_edit)

        layout.addLayout(toggle_visibility_ks_hbox)

        undo_ks_hbox = qt.QHBoxLayout()

        self.undo_ks_label = qt.QLabel()
        self.undo_ks_label.setText('Undo Keyboard Shortcut : ')
        self.undo_ks_label.setStyleSheet("font-style: italic")
        undo_ks_hbox.addWidget(self.undo_ks_label)

        self.undo_ks_line_edit = qt.QLineEdit(self.undo_ks_selected)
        self.undo_ks_line_edit.setMaxLength(1)
        undo_ks_hbox.addWidget(self.undo_ks_line_edit)

        layout.addLayout(undo_ks_hbox)

        save_seg_ks_hbox = qt.QHBoxLayout()

        self.save_seg_ks_label = qt.QLabel()
        self.save_seg_ks_label.setText('Save Segmentation Keyboard Shortcut : ')
        self.save_seg_ks_label.setStyleSheet("font-style: italic")
        save_seg_ks_hbox.addWidget(self.save_seg_ks_label)

        self.save_seg_ks_line_edit = qt.QLineEdit(self.save_seg_ks_selected)
        self.save_seg_ks_line_edit.setMaxLength(1)
        save_seg_ks_hbox.addWidget(self.save_seg_ks_line_edit)

        layout.addLayout(save_seg_ks_hbox)

        smooth_ks_hbox = qt.QHBoxLayout()

        self.smooth_ks_label = qt.QLabel()
        self.smooth_ks_label.setText('Smooth Margins Keyboard Shortcut : ')
        self.smooth_ks_label.setStyleSheet("font-style: italic")
        smooth_ks_hbox.addWidget(self.smooth_ks_label)

        self.smooth_ks_line_edit = qt.QLineEdit(self.smooth_ks_selected)
        self.smooth_ks_line_edit.setMaxLength(1)
        smooth_ks_hbox.addWidget(self.smooth_ks_line_edit)

        layout.addLayout(smooth_ks_hbox)

        remove_small_holes_ks_hbox = qt.QHBoxLayout()

        self.remove_small_holes_ks_label = qt.QLabel()
        self.remove_small_holes_ks_label.setText(
            'Remove Small Holes Keyboard Shortcut : ')
        self.remove_small_holes_ks_label.setStyleSheet("font-style: italic")
        remove_small_holes_ks_hbox.addWidget(self.remove_small_holes_ks_label)

        self.remove_small_holes_ks_line_edit = qt.QLineEdit(
            self.remove_small_holes_ks_selected)
        self.remove_small_holes_ks_line_edit.setMaxLength(1)
        remove_small_holes_ks_hbox.addWidget(
            self.remove_small_holes_ks_line_edit)

        layout.addLayout(remove_small_holes_ks_hbox)

        interpolate_ks_hbox = qt.QHBoxLayout()

        self.interpolate_ks_label = qt.QLabel()
        self.interpolate_ks_label.setText(
            'Interpolate Image Keyboard Shortcut : ')
        self.interpolate_ks_label.setStyleSheet("font-style: italic")
        interpolate_ks_hbox.addWidget(self.interpolate_ks_label)

        self.interpolate_ks_line_edit = qt.QLineEdit(
            self.interpolate_ks_selected)
        self.interpolate_ks_line_edit.setMaxLength(1)
        interpolate_ks_hbox.addWidget(self.interpolate_ks_line_edit)

        layout.addLayout(interpolate_ks_hbox)

        mouse_shortcuts_hbox = qt.QHBoxLayout()

        mouse_shortcuts_label = qt.QLabel('Use Custom Mouse Shortcuts? ')
        mouse_shortcuts_label.setStyleSheet("font-weight: bold")
        mouse_shortcuts_hbox.addWidget(mouse_shortcuts_label)

        self.mouse_shortcuts_checkbox = qt.QCheckBox()
        mouse_shortcuts_hbox.addWidget(self.mouse_shortcuts_checkbox)

        layout.addLayout(mouse_shortcuts_hbox)
        self.configure_segmentation_button = qt.QPushButton(
            'Configure Segmentation...')
        self.configure_segmentation_button.setStyleSheet(
            "background-color : yellowgreen")
        layout.addWidget(self.configure_segmentation_button)

        self.configure_classification_button = qt.QPushButton(
            'Configure Classification...')
        self.configure_classification_button.setStyleSheet(
            "background-color : yellowgreen")
        layout.addWidget(self.configure_classification_button)

        self.previous_button = qt.QPushButton('Previous')
        layout.addWidget(self.previous_button)

        self.apply_button = qt.QPushButton('Apply')
        layout.addWidget(self.apply_button)

        self.cancel_button = qt.QPushButton('Cancel')
        layout.addWidget(self.cancel_button)

        self.connect_buttons_to_callbacks()

        if self.edit_conf:
            self.disableWidgetsForEditConfiguration()

        self.setLayout(layout)
        self.setWindowTitle("Configure SlicerCART")
        self.resize(800, 200)

    def disableWidgetsForEditConfiguration(self):
        self.classification_task_checkbox.setEnabled(False)
        self.segmentation_task_checkbox.setEnabled(False)

        if self.bids_selected == False:
            self.bids_combobox.setEnabled(False)

        self.file_extension_combobox.setEnabled(False)
        self.ct_modality_radio_button.setEnabled(False)
        self.mri_modality_radio_button.setEnabled(False)
        self.previous_button.setVisible(False)

    def connect_buttons_to_callbacks(self):
        self.segmentation_task_checkbox.stateChanged.connect(
            self.segmentation_checkbox_state_changed)
        self.classification_task_checkbox.stateChanged.connect(
            self.classification_checkbox_state_changed)
        self.keyboard_shortcuts_checkbox.stateChanged.connect(
            self.keyboard_shortcuts_checkbox_state_changed)
        self.ct_modality_radio_button.toggled.connect(
            lambda: self.update_selected_modality(
                self.ct_modality_radio_button.text))
        self.mri_modality_radio_button.toggled.connect(
            lambda: self.update_selected_modality(
                self.mri_modality_radio_button.text))
        self.bids_combobox.currentIndexChanged.connect(self.update_bids)
        self.file_extension_combobox.currentIndexChanged.connect(
            self.update_file_extension)
        self.initial_view_combobox.currentIndexChanged.connect(
            self.update_initial_view)
        self.interpolate_combobox.currentIndexChanged.connect(
            self.update_interpolate)
        self.ct_window_level_line_edit.textChanged.connect(
            self.update_ct_window_level)
        self.ct_window_width_line_edit.textChanged.connect(
            self.update_ct_window_width)
        self.toggle_fill_ks_line_edit.textChanged.connect(
            self.update_toggle_fill_ks)
        self.toggle_visibility_ks_line_edit.textChanged.connect(
            self.update_toggle_visibility_ks)
        self.undo_ks_line_edit.textChanged.connect(self.update_undo_ks)
        self.save_seg_ks_line_edit.textChanged.connect(self.update_save_seg_ks)
        self.smooth_ks_line_edit.textChanged.connect(self.update_smooth_ks)
        self.remove_small_holes_ks_line_edit.textChanged.connect(
            self.update_remove_small_holes_ks)
        self.interpolate_ks_line_edit.textChanged.connect(
            self.update_interpolate_ks)
        self.configure_classification_button.clicked.connect(
            self.push_configure_classification)
        self.previous_button.clicked.connect(self.push_previous)
        self.apply_button.clicked.connect(self.push_apply)
        self.cancel_button.clicked.connect(self.push_cancel)
        self.configure_segmentation_button.clicked.connect(
            self.push_configure_segmentation)

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
        self.classification_task_checkbox.setChecked(
            self.classification_selected)
        self.mouse_shortcuts_checkbox.setChecked(self.mouse_shortcuts_selected)
        self.keyboard_shortcuts_checkbox.setChecked(
            self.keyboard_shortcuts_selected)

        self.segmentation_checkbox_state_changed()
        self.keyboard_shortcuts_checkbox_state_changed()

    def set_default_values(self):
        self.segmentation_selected = self.config_yaml[
            'is_segmentation_requested']
        self.classification_selected = self.config_yaml[
            'is_classification_requested']
        self.mouse_shortcuts_selected = self.config_yaml[
            'is_mouse_shortcuts_requested']
        self.keyboard_shortcuts_selected = self.config_yaml[
            'is_keyboard_shortcuts_requested']

        self.modality_selected = self.config_yaml['modality']

        self.bids_selected = self.config_yaml['impose_bids_format']

        self.ct_window_level_selected = self.config_yaml['ct_window_level']
        self.ct_window_width_selected = self.config_yaml['ct_window_width']
        self.file_extension_selected = self.config_yaml['input_filetype']

        if self.config_yaml['slice_view_color'] == 'Red':
            self.initial_view_selected = 'Red (axial)'
        elif self.config_yaml['slice_view_color'] == 'Yellow':
            self.initial_view_selected = 'Yellow (sagittal)'
        elif self.config_yaml['slice_view_color'] == 'Green':
            self.initial_view_selected = 'Green (coronal)'

        self.interpolate_selected = self.config_yaml['interpolate_value']

        self.toggle_fill_ks_selected = \
        self.config_yaml['KEYBOARD_SHORTCUTS'][0]['shortcut']
        self.toggle_visibility_ks_selected = \
        self.config_yaml['KEYBOARD_SHORTCUTS'][1]['shortcut']
        self.undo_ks_selected = self.config_yaml['KEYBOARD_SHORTCUTS'][2][
            'shortcut']
        self.save_seg_ks_selected = self.config_yaml['KEYBOARD_SHORTCUTS'][3][
            'shortcut']
        self.smooth_ks_selected = self.config_yaml['KEYBOARD_SHORTCUTS'][4][
            'shortcut']
        self.remove_small_holes_ks_selected = \
        self.config_yaml['KEYBOARD_SHORTCUTS'][5]['shortcut']
        self.interpolate_ks_selected = \
        self.config_yaml['KEYBOARD_SHORTCUTS'][6]['shortcut']

    def classification_checkbox_state_changed(self):
        self.classification_selected = self.classification_task_checkbox.isChecked()
        self.configure_classification_button.setEnabled(
            self.classification_selected)

    def keyboard_shortcuts_checkbox_state_changed(self):
        self.keyboard_shortcuts_selected = self.keyboard_shortcuts_checkbox.isChecked()

        self.toggle_fill_ks_label.setVisible(self.keyboard_shortcuts_selected)
        self.toggle_fill_ks_line_edit.setVisible(
            self.keyboard_shortcuts_selected)
        self.toggle_visibility_ks_label.setVisible(
            self.keyboard_shortcuts_selected)
        self.toggle_visibility_ks_line_edit.setVisible(
            self.keyboard_shortcuts_selected)
        self.undo_ks_label.setVisible(self.keyboard_shortcuts_selected)
        self.undo_ks_line_edit.setVisible(self.keyboard_shortcuts_selected)
        self.save_seg_ks_label.setVisible(self.keyboard_shortcuts_selected)
        self.save_seg_ks_line_edit.setVisible(self.keyboard_shortcuts_selected)
        self.smooth_ks_label.setVisible(self.keyboard_shortcuts_selected)
        self.smooth_ks_line_edit.setVisible(self.keyboard_shortcuts_selected)
        self.remove_small_holes_ks_label.setVisible(
            self.keyboard_shortcuts_selected)
        self.remove_small_holes_ks_line_edit.setVisible(
            self.keyboard_shortcuts_selected)
        self.interpolate_ks_label.setVisible(self.keyboard_shortcuts_selected)
        self.interpolate_ks_line_edit.setVisible(
            self.keyboard_shortcuts_selected)

    def segmentation_checkbox_state_changed(self):
        self.segmentation_selected = self.segmentation_task_checkbox.isChecked()
        self.configure_segmentation_button.setEnabled(
            self.segmentation_selected)

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

    def update_selected_modality(self, option):
        self.modality_selected = option

        if self.modality_selected == 'CT':
            self.bids_combobox.setEnabled(False)

            self.ct_window_level_line_edit.setEnabled(True)
            self.ct_window_width_line_edit.setEnabled(True)

        else:
            self.bids_combobox.setEnabled(True)

            self.ct_window_level_line_edit.setEnabled(False)
            self.ct_window_width_line_edit.setEnabled(False)

    def push_configure_segmentation(self):
        self.configureSegmentationWindow = ConfigureSegmentationWindow(
            self.segmenter, self.modality_selected, self.edit_conf)
        self.configureSegmentationWindow.show()
        self.close()

    def push_configure_classification(self):
        configureClassificationWindow = ConfigureClassificationWindow(
            self.segmenter, self.edit_conf)
        configureClassificationWindow.show()
        self.close()

    def push_previous(self):
        self.close()
        slicerCART_configuration_initial_window = SlicerCARTConfigurationInitialWindow(
            self.segmenter)
        slicerCART_configuration_initial_window.show()

    def push_apply(self):
        self.config_yaml[
            'is_segmentation_requested'] = self.segmentation_task_checkbox.isChecked()
        self.config_yaml[
            'is_classification_requested'] = self.classification_task_checkbox.isChecked()
        self.config_yaml[
            'is_mouse_shortcuts_requested'] = self.mouse_shortcuts_checkbox.isChecked()
        self.config_yaml[
            'is_keyboard_shortcuts_requested'] = self.keyboard_shortcuts_checkbox.isChecked()
        self.config_yaml['modality'] = self.modality_selected

        if self.bids_selected == 'Yes':
            self.config_yaml['impose_bids_format'] = True
        elif self.bids_selected == 'No':
            self.config_yaml['impose_bids_format'] = False

        self.config_yaml['input_filetype'] = self.file_extension_selected

        self.config_yaml['interpolate_value'] = self.interpolate_selected

        if 'Red' in self.initial_view_selected:
            self.config_yaml['slice_view_color'] = 'Red'
        elif 'Yellow' in self.initial_view_selected:
            self.config_yaml['slice_view_color'] = 'Yellow'
        elif 'Green' in self.initial_view_selected:
            self.config_yaml['slice_view_color'] = 'Green'

        self.config_yaml['ct_window_level'] = int(self.ct_window_level_selected)
        self.config_yaml['ct_window_width'] = int(self.ct_window_width_selected)

        self.config_yaml['KEYBOARD_SHORTCUTS'][0][
            'shortcut'] = self.toggle_fill_ks_selected
        self.config_yaml['KEYBOARD_SHORTCUTS'][1][
            'shortcut'] = self.toggle_visibility_ks_selected
        self.config_yaml['KEYBOARD_SHORTCUTS'][2][
            'shortcut'] = self.undo_ks_selected
        self.config_yaml['KEYBOARD_SHORTCUTS'][3][
            'shortcut'] = self.save_seg_ks_selected
        self.config_yaml['KEYBOARD_SHORTCUTS'][4][
            'shortcut'] = self.smooth_ks_selected
        self.config_yaml['KEYBOARD_SHORTCUTS'][5][
            'shortcut'] = self.remove_small_holes_ks_selected
        self.config_yaml['KEYBOARD_SHORTCUTS'][6][
            'shortcut'] = self.interpolate_ks_selected

        with open(CONFIG_FILE_PATH, 'w') as file:
            yaml.safe_dump(self.config_yaml, file)

        self.segmenter.setup_configuration()

        if self.edit_conf and self.segmenter.outputFolder is not None and os.path.exists(
                f'{self.segmenter.outputFolder}{os.sep}{CONF_FOLDER_NAME}'):
            shutil.copy(CONFIG_FILE_PATH,
                        f'{self.segmenter.outputFolder}{os.sep}{CONF_FOLDER_NAME}{os.sep}{CONFIG_COPY_FILENAME}')
        self.close()

    def push_cancel(self):
        if self.edit_conf == False:
            msg = qt.QMessageBox()
            msg.setWindowTitle('Informative Message')
            msg.setText(
                'Using default configurations. To select a different configuration, restart the application. ')
            msg.exec()

        self.segmenter.setup_configuration()
        self.close()


class SlicerCARTConfigurationInitialWindow(qt.QWidget):
    def __init__(self, segmenter, parent=None):
        super(SlicerCARTConfigurationInitialWindow, self).__init__(parent)

        self.segmenter = segmenter

        layout = qt.QVBoxLayout()

        self.reuse_configuration_hbox = qt.QHBoxLayout()

        self.new_config_radio_button = qt.QRadioButton('New configuration',
                                                       self)
        self.reuse_config_radio_button = qt.QRadioButton(
            'Continue from existing output folder', self)
        self.use_template_config_radio_button = qt.QRadioButton(
            'Use template configuration', self)

        self.reuse_configuration_hbox.addWidget(self.new_config_radio_button)
        self.reuse_configuration_hbox.addWidget(self.reuse_config_radio_button)
        self.reuse_configuration_hbox.addWidget(
            self.use_template_config_radio_button)

        self.new_config_radio_button.toggled.connect(
            lambda: self.update_selected_reuse_config_option(
                self.new_config_radio_button.text))
        self.reuse_config_radio_button.toggled.connect(
            lambda: self.update_selected_reuse_config_option(
                self.reuse_config_radio_button.text))
        self.use_template_config_radio_button.toggled.connect(
            lambda: self.update_selected_reuse_config_option(
                self.use_template_config_radio_button.text))

        self.new_config_radio_button.setChecked(True)  # par défaut
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
            msg.setText(
                'Please select the _conf folder containing the template configuration files. ')
            msg.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
            msg.buttonClicked.connect(self.select_template_folder_clicked)
            msg.exec()
        elif self.reuse_configuration_selected_option == self.new_config_radio_button.text:
            slicerCARTConfigurationSetupWindow = SlicerCARTConfigurationSetupWindow(
                self.segmenter)
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
            if (os.path.exists(
                    f'{self.segmenter.outputFolder}{os.sep}{CONF_FOLDER_NAME}') and
                    os.path.exists(
                        f'{self.segmenter.outputFolder}{os.sep}{CONF_FOLDER_NAME}{os.sep}{CONFIG_COPY_FILENAME}')):
                # use this configuration directly
                shutil.copy(
                    f'{self.segmenter.outputFolder}{os.sep}{CONF_FOLDER_NAME}{os.sep}{CONFIG_COPY_FILENAME}',
                    CONFIG_FILE_PATH)
                self.segmenter.setup_configuration()
                self.close()
            else:
                msg = qt.QMessageBox()
                msg.setWindowTitle('Informative Message')
                msg.setText(
                    'The selected output folder does not contain the required configuration files for SlicerCART. Please try again. ')
                msg.setStandardButtons(
                    qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
                msg.buttonClicked.connect(
                    self.error_msg_for_output_folder_selection_clicked)
                msg.exec()

        else:
            slicerCART_configuration_initial_window = SlicerCARTConfigurationInitialWindow(
                self.segmenter)
            slicerCART_configuration_initial_window.show()
            self.close()
            return

    def error_msg_for_output_folder_selection_clicked(self, button):
        slicerCART_configuration_initial_window = SlicerCARTConfigurationInitialWindow(
            self.segmenter)
        slicerCART_configuration_initial_window.show()
        self.close()

    def select_template_folder_clicked(self, button):
        if button.text == 'OK':
            conf_folder_path = qt.QFileDialog.getExistingDirectory(None,
                                                                   "Open a folder",
                                                                   '',
                                                                   qt.QFileDialog.ShowDirsOnly)
            if (os.path.split(conf_folder_path)[1] == CONF_FOLDER_NAME and
                    os.path.exists(
                        f'{conf_folder_path}{os.sep}{CONFIG_COPY_FILENAME}')):

                slicerCARTConfigurationSetupWindow = SlicerCARTConfigurationSetupWindow(
                    self.segmenter, conf_folder_path)
                slicerCARTConfigurationSetupWindow.show()
                self.segmenter.ui.SelectOutputFolder.setVisible(True)
                self.close()

            else:
                msg = qt.QMessageBox()
                msg.setWindowTitle('Informative Message')
                msg.setText(
                    'The selected output folder does not contain the required configuration files for SlicerCART. Please try again. ')
                msg.setStandardButtons(
                    qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
                msg.buttonClicked.connect(
                    self.error_msg_for_output_folder_selection_clicked)
                msg.exec()

        else:
            slicerCART_configuration_initial_window = SlicerCARTConfigurationInitialWindow(
                self.segmenter)
            slicerCART_configuration_initial_window.show()
            self.close()
            return

    def push_cancel(self):
        msg = qt.QMessageBox()
        msg.setWindowTitle('Informative Message')
        msg.setText(
            'Using default configurations. To select a different configuration, restart the application. ')
        msg.exec()

        self.segmenter.setup_configuration()
        self.close()