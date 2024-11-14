class InteractionsClassificationSetup:
    def __init__(self):
        pass

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


    # from Coonfiguration SetUp
    def push_configure_classification(self):
        configureClassificationWindow = ConfigureClassificationWindow(
            self.segmenter, self.edit_conf)
        configureClassificationWindow.show()
        self.close()