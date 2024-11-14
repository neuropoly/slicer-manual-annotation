
class Interactions:
    def __init__(self):
        pass

    #from single label
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

    #from segmentation window
    def push_configure_segmentation(self):
        self.configureSegmentationWindow = ConfigureSegmentationWindow(
            self.segmenter, self.modality_selected, self.edit_conf)
        self.configureSegmentationWindow.show()
        self.close()


    # from initial window
    def push_previous(self):
        self.close()
        slicerCART_configuration_initial_window = SlicerCARTConfigurationInitialWindow(
            self.segmenter)
        slicerCART_configuration_initial_window.show()

    # from cONFIGUREClassification
    def push_add_freetextbox(self):
        self.close()

        configureSingleClassificationItemWindow = ConfigureSingleClassificationItemWindow(
            self.segmenter, self.config_yaml, 'freetextbox', self.edit_conf)
        configureSingleClassificationItemWindow.show()

    def push_add_combobox(self):
        self.close()

        configureSingleClassificationItemWindow = ConfigureSingleClassificationItemWindow(
            self.segmenter, self.config_yaml, 'combobox', self.edit_conf)
        configureSingleClassificationItemWindow.show()

    def push_add_checkbox(self):
        self.close()

        configureSingleClassificationItemWindow = ConfigureSingleClassificationItemWindow(
            self.segmenter, self.config_yaml, 'checkbox', self.edit_conf)
        configureSingleClassificationItemWindow.show()

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
