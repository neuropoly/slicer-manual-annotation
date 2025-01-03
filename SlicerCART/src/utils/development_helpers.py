import os
import slicer
import qt
from utils.debugging_helpers import *

class Dev:
    def __init__(self):
        pass

    @enter_function
    def show_message_box(self, message,
                         box_title=None,
                         buttons=False):

        # Create a message box
        messageBox = qt.QMessageBox()

        # Set the message box title
        if box_title is None:
            messageBox.setWindowTitle("Message Box")
        else:
            messageBox.setWindowTitle(box_title)

        # Set the message box text
        messageBox.setText(message)

        if buttons:
            # Add Yes and No buttons
            messageBox.addButton(qt.QMessageBox.Yes)
            messageBox.addButton(qt.QMessageBox.No)

        # Display the message box as modal
        return messageBox.exec_()

    # MB Get nodes easily with functions
    def get_volume_node(self):
        # In this project, note that we can also get the first node with the
        # following: slicer.util.getNodesByClass('vtkMRMLScalarVolumeNode')[0]
        return slicer.mrmlScene.GetFirstNodeByClass(
            "vtkMRMLScalarVolumeNode")

    def get_segmentation_node(self):
        # In this project, note that we can also get the first node with the
        # following: slicer.util.getNodesByClass('vtkMRMLSegmentationNode')[0]
        return slicer.mrmlScene.GetFirstNodeByClass(
            'vtkMRMLSegmentationNode')

    def get_label_map_display_node(self):
        return slicer.mrmlScene.GetFirstNodeByClass(
            'vtkMRMLLabelMapVolumeDisplayNode')

    def get_storage_node(self):
        return slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLStorageNode')

    def get_transform_node(self):
        return slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLTransformNode')

    def get_active_segments(self, segmentation_node):
        return segmentation_node.GetSegmentation()

    def get_number_of_segments(self, segments):
        return segments.GetNumberOfSegments()


    # Check functions
    @enter_function
    def check_if_folder_exists(self, folder_path):
        # Check if a folder path exists and return True/False
        if os.path.exists(folder_path):
            print("Folder exists: ", folder_path)
            return True
        else:
            print("Folder does not exist: ", folder_path)
            return False

    @enter_function
    def check_list_in_another(self, list1, list2):
        for element in list1:
            if element in list2:
                continue
            else:
                return False
        return True
