###############################################################################
# Those lines need to be copy-pasted in each script file for appropriate use.
from utils import *
from scripts.Interactions import *
# # Get actual script filepath and filename
# filepath = os.path.abspath(__file__)
# filename = os.path.basename(filepath)
#
# # Extract and import a list of all modules in the same subFolder (e.g. scripts)
# modules_list = list_modules_in_folder('scripts', filename)
# for module_name in modules_list:
#     module = import_all_from_module(module_name)
#     # Load all attributes of the module into the current namespace
#     globals().update(vars(module))
#
# ###############################################################################

# from scripts.SlicerCARTConfigurationSetupWindow import *


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
        self.reuse_configuration_selected_option = (
            self.new_config_radio_button.text)

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

    # def push_next(self):
    #     if (self.reuse_configuration_selected_option ==
    #             self.reuse_config_radio_button.text):
    #         msg = qt.QMessageBox()
    #         msg.setWindowTitle('Informative Message')
    #         msg.setText('Please select the working output directory. ')
    #         msg.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
    #         msg.buttonClicked.connect(self.select_output_folder_clicked)
    #         msg.exec()
    #     elif (self.reuse_configuration_selected_option ==
    #           self.use_template_config_radio_button.text):
    #         msg = qt.QMessageBox()
    #         msg.setWindowTitle('Informative Message')
    #         msg.setText(
    #             'Please select the _conf folder containing the template '
    #             'configuration files. ')
    #         msg.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
    #         msg.buttonClicked.connect(self.select_template_folder_clicked)
    #         msg.exec()
    #     elif (self.reuse_configuration_selected_option ==
    #           self.new_config_radio_button.text):
    #         slicerCARTConfigurationSetupWindow = (
    #             SlicerCARTConfigurationSetupWindow(self.segmenter))
    #         slicerCARTConfigurationSetupWindow.show()
    #         self.segmenter.ui.SelectOutputFolder.setVisible(True)
    #         self.close()

    def select_output_folder_clicked(self, button):
        if button.text == 'OK':
            global REQUIRE_EMPTY
            REQUIRE_EMPTY = False
            self.segmenter.onSelectOutputFolder()
            REQUIRE_EMPTY = True
            self.segmenter.ui.SelectOutputFolder.setVisible(False)
            if (os.path.exists(
                    f'{self.segmenter.outputFolder}{os.sep}{CONF_FOLDER_NAME}')
                    and os.path.exists(
                        f'{self.segmenter.outputFolder}'
                        f'{os.sep}{CONF_FOLDER_NAME}{os.sep}'
                        f'{CONFIG_COPY_FILENAME}')):
                # use this configuration directly
                shutil.copy(
                    f'{self.segmenter.outputFolder}{os.sep}'
                    f'{CONF_FOLDER_NAME}{os.sep}{CONFIG_COPY_FILENAME}',
                    CONFIG_FILE_PATH)
                self.segmenter.setup_configuration()
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

    def error_msg_for_output_folder_selection_clicked(self, button):
        slicerCART_configuration_initial_window = (
            SlicerCARTConfigurationInitialWindow(
            self.segmenter))
        slicerCART_configuration_initial_window.show()
        self.close()

    # def select_template_folder_clicked(self, button):
    #     if button.text == 'OK':
    #         conf_folder_path = qt.QFileDialog.getExistingDirectory(None,
    #                                                                "Open a "
    #                                                                "folder",
    #                                                                '',
    #                                                                qt.QFileDialog.ShowDirsOnly)
    #         if (os.path.split(conf_folder_path)[1] == CONF_FOLDER_NAME and
    #                 os.path.exists(
    #                     f'{conf_folder_path}{os.sep}{CONFIG_COPY_FILENAME}')):
    #
    #             slicerCARTConfigurationSetupWindow = (
    #                 SlicerCARTConfigurationSetupWindow(
    #                 self.segmenter, conf_folder_path))
    #             slicerCARTConfigurationSetupWindow.show()
    #             self.segmenter.ui.SelectOutputFolder.setVisible(True)
    #             self.close()
    #
    #         else:
    #             msg = qt.QMessageBox()
    #             msg.setWindowTitle('Informative Message')
    #             msg.setText(
    #                 'The selected output folder does not contain the required '
    #                 'configuration files for SlicerCART. Please try again. ')
    #             msg.setStandardButtons(
    #                 qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
    #             msg.buttonClicked.connect(
    #                 self.error_msg_for_output_folder_selection_clicked)
    #             msg.exec()
    #
    #     else:
    #         slicerCART_configuration_initial_window = (
    #             SlicerCARTConfigurationInitialWindow(
    #             self.segmenter))
    #         slicerCART_configuration_initial_window.show()
    #         self.close()
    #         return

    def push_cancel(self):
        msg = qt.QMessageBox()
        msg.setWindowTitle('Informative Message')
        msg.setText(
            'Using default configurations. To select a different '
            'configuration, restart the application. ')
        msg.exec()

        self.segmenter.setup_configuration()
        self.close()
