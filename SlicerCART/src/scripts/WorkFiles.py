from utils import *
# import os
# import yaml
# import glob
#
# WORKING_LIST_FILENAME = 'working_list.yaml'
# REMAINING_LIST_FILENAME = 'remaining_list.yaml'
#
# INPUT_FILE_EXTENSION = '*.nii.gz'


class WorkFiles():
    def __init__(self, currentFolder, outputFolder):
        self.CurrentFolder = currentFolder
        self.outputFolder = outputFolder

    def check_working_list(self):
        """
        Check in already selected output folder if a working list is defined.
        """
        working_list_filepath = os.path.join(self.outputFolder,
                                             WORKING_LIST_FILENAME)
        remaining_list_filepath = os.path.join(self.outputFolder,
                                               REMAINING_LIST_FILENAME)

        output_folder_files = os.listdir(self.outputFolder)

        all_cases_path = WorkFiles.get_working_list(self)
        all_cases_path = WorkFiles.filter_working_list(self, all_cases_path)

        all_cases_filenames = self.get_filenames_in_working_list(all_cases_path)

        if WORKING_LIST_FILENAME in output_folder_files:
            good_match = self.check_correspondence(working_list_filepath,
                                                   all_cases_filenames)
            if good_match:
                remaining_list_status = self.check_remaining_list(
                    self.outputFolder)

                if remaining_list_status:
                    with open(remaining_list_filepath, 'r') as file:
                        first_element = yaml.safe_load(file)['CASES'][0]
                    if first_element in all_cases_filenames:
                        print('First element of remaining list in working '
                              'list. READY TO START.')

                    else:
                        print('First element of the remaining list IS NOT in '
                              'the working list. Please double check list '
                              'correspondences.')
                        return False

                else:
                    print(' *** ATTENTION! *** No remaining list file found '
                          'although working list is defined. Double check for '
                          'any manipulation errors. A new remaining file is '
                          'created right now corresponding to the working '
                          'list.')
                    self.write_file_list(remaining_list_filepath,
                                         all_cases_filenames)
                    return False

        else:
            # Create initial working list and remaining list.
            self.write_file_list(working_list_filepath, all_cases_filenames)
            self.write_file_list(remaining_list_filepath, all_cases_filenames)

        return True

    def get_working_list(self):
        """
        Get all files that have the correct file extension.
        """
        self.CasesPaths = sorted(glob(f'{self.CurrentFolder}{os.sep}*'
                                           f'*{os.sep}{INPUT_FILE_EXTENSION}',
                                           recursive=True))
        return self.CasesPaths

    def filter_working_list(self, working_list):
        """
        Filter all files that have the correct working_list.
        Can use elif to build up and handle different inclusion criteria.
        """
        filtered_list = []
        for element in working_list:
            if 'derivatives' in element:
                continue
            else:
                filtered_list.append(element)
        return filtered_list

    def get_filenames_in_working_list(self, all_cases_path):
        """
        Get all filenames from filepaths.
        """
        cases = sorted([os.path.split(i)[-1] for i in all_cases_path])
        return cases

    def check_correspondence(self, working_list_filepath, all_cases_filenames):
        """
        Verify if the first element of the working list is in the volumes
        folder.
        """
        with open(working_list_filepath, 'r') as file:
            elements = yaml.safe_load(file)['CASES']

        if elements == all_cases_filenames:
            return True

        else:
            # Find differing elements
            missing_in_elements = [f for f in all_cases_filenames if
                                   f not in elements]
            missing_in_all_cases = [f for f in elements if
                                    f not in all_cases_filenames]

            # def print_message(message):
            #     message = message.join(message)
            #     return message
            #
            #     # ele = ''
            #     # for element in message:
            #     #     ele = ele.join(print(element))
            #     # return ele
            #
            #
            #
            # # Print differing elements
            # message = (f"Missing in 'working_list_filepath': "
            #            f"{print_message(missing_in_elements)} \n"
            #            f"Missing in 'all_cases_filenames': "
            #            f"{print_message(missing_in_all_cases)} ")
            #
            # print("Missing in 'working_list_filepath':", missing_in_elements)
            # print("Missing in 'all_cases_filenames':", missing_in_all_cases)
            # Dev.show_message_box(self, message,
            #              box_title='ATTENTION!')
            def print_message(elements):
                """
                Formats a list of elements into a string with each element on a new line.
                """
                return "\n".join(f"{element}" for element in
                                 elements)  # Add optional bullet points for clarity

            # Print differing elements
            message = (
                f"Missing in 'working_list_filepath':\n"
                f"{print_message(missing_in_elements)}\n\n"
                f"Missing in 'all_cases_filenames':\n"
                f"{print_message(missing_in_all_cases)}"
            )

            # For console debugging (optional)
            print("Missing in 'working_list_filepath':", missing_in_elements)
            print("Missing in 'all_cases_filenames':", missing_in_all_cases)

            # Display message box in 3D Slicer
            Dev.show_message_box(self, message, box_title='ATTENTION!')


        return False

    def check_remaining_list(self, outputFolder):

        # List all files in the folder
        output_folder_files = os.listdir(outputFolder)

        if REMAINING_LIST_FILENAME in output_folder_files:
            return True

        return False

    def write_file_list(self, filepath, filenames):
        all_cases_data = {
            'CASES': filenames
        }
        with open(filepath, 'w') as file:
            yaml.dump(all_cases_data, file)


# currentFolder1 = '/Users/maximebouthillier/gitmax/data_confid/praxis/site_007'
# outputFolder1 = '/Users/maximebouthillier/gitmax/data_confid/test_bidon'
# outputFolder2 = '/Users/maximebouthillier/gitmax/data_confid/test_bidon2'
# WorkFiles = WorkFiles(currentFolder1, outputFolder1)
#
# WorkFiles.check_working_list()
