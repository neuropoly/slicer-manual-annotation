from utils import *

from scripts.SlicerCARTConfigurationInitialWindow import *
from scripts.SlicerCARTConfigurationSetupWindow import *
from scripts.ConfigureSegmentationWindow import *
from scripts.ConfigureSingleLabelWindow import *


class Interactions:
    def __init__(self):
        pass

    #from segmentation
    def push_add_label(self):
        self.close()
        configureSingleLabelWindow = ConfigureSingleLabelWindow(self.segmenter,
                                                                self.modality,
                                                                self.edit_conf,
                                                                self.config_yaml)
        configureSingleLabelWindow.show()


    def push_edit_button(self, label):
        self.close()

        configureSingleLabelWindow = ConfigureSingleLabelWindow(self.segmenter,
                                                                self.modality,
                                                                self.edit_conf,
                                                                self.config_yaml,
                                                                label)
        configureSingleLabelWindow.show()

    # from single label
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


    #from segmentation window
    def push_configure_segmentation(self):
        self.configureSegmentationWindow = ConfigureSegmentationWindow(
            self.segmenter, self.modality_selected, self.edit_conf)
        self.configureSegmentationWindow.show()
        self.close()


    # from initial window

    def select_template_folder_clicked(self, button):
        if button.text == 'OK':
            conf_folder_path = qt.QFileDialog.getExistingDirectory(None,
                                                                   "Open a "
                                                                   "folder",
                                                                   '',
                                                                   qt.QFileDialog.ShowDirsOnly)
            if (os.path.split(conf_folder_path)[1] == CONF_FOLDER_NAME and
                    os.path.exists(
                        f'{conf_folder_path}{os.sep}{CONFIG_COPY_FILENAME}')):

                slicerCARTConfigurationSetupWindow = (
                    SlicerCARTConfigurationSetupWindow(
                        self.segmenter, conf_folder_path))
                slicerCARTConfigurationSetupWindow.show()
                self.segmenter.ui.SelectOutputFolder.setVisible(True)
                self.close()

            else:
                msg = qt.QMessageBox()
                msg.setWindowTitle('Informative Message')
                msg.setText(
                    'The selected output folder does not contain the required '
                    'configuration files for SlicerCART. Please try again. ')
                msg.setStandardButtons(
                    qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
                msg.buttonClicked.connect(
                    self.error_msg_for_output_folder_selection_clicked)
                msg.exec()

        else:
            slicerCART_configuration_initial_window = (
                SlicerCARTConfigurationInitialWindow(
                    self.segmenter))
            slicerCART_configuration_initial_window.show()
            self.close()
            return

    def push_previous(self):
        self.close()
        slicerCART_configuration_initial_window = SlicerCARTConfigurationInitialWindow(
            self.segmenter)
        slicerCART_configuration_initial_window.show()



    #from part 2 ***
    # from initial window
    def push_next(self):
        if (self.reuse_configuration_selected_option ==
                self.reuse_config_radio_button.text):
            msg = qt.QMessageBox()
            msg.setWindowTitle('Informative Message')
            msg.setText('Please select the working output directory. ')
            msg.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
            msg.buttonClicked.connect(self.select_output_folder_clicked)
            msg.exec()
        elif (self.reuse_configuration_selected_option ==
              self.use_template_config_radio_button.text):
            msg = qt.QMessageBox()
            msg.setWindowTitle('Informative Message')
            msg.setText(
                'Please select the _conf folder containing the template '
                'configuration files. ')
            msg.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
            msg.buttonClicked.connect(self.select_template_folder_clicked)
            msg.exec()
        elif (self.reuse_configuration_selected_option ==
              self.new_config_radio_button.text):
            slicerCARTConfigurationSetupWindow = (
                SlicerCARTConfigurationSetupWindow(self.segmenter))
            slicerCARTConfigurationSetupWindow.show()
            self.segmenter.ui.SelectOutputFolder.setVisible(True)
            self.close()


    ## portion 2
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
