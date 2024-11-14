
class Interactions_items():
    def __init__(self):
        pass
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

    def push_cancel(self):
        configureClassificationWindow = ConfigureClassificationWindow(
            self.segmenter, self.edit_conf, self.config_yaml)
        configureClassificationWindow.show()
        self.close()

    # from classification
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
