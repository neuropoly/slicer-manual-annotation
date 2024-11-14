
class Interactions:
    def __init__(self):
        pass

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