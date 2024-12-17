# from utils import *
import os
import yaml
import glob
from pathlib import Path

WORKING_LIST_FILENAME = 'working_list.yaml'
REMAINING_LIST_FILENAME = 'remaining_list.yaml'

INPUT_FILE_EXTENSION = '*.nii.gz'


class WorkFiles():
    def __init__(self, currentFolder, outputFolder):
        self.CurrentFolder = currentFolder
        self.outputFolder = outputFolder

    def check_working_list(self):
        """
        Check in already selected output folder if a working list is defined.
        """
        output_folder_files = os.listdir(self.outputFolder)

        all_cases_path = WorkFiles.get_working_list()
        print('all_cases: ', all_cases_path)
        print('len all cases before derivatives: ', len(all_cases_path))
        all_cases_path = self.filter_working_list(all_cases_path)

        all_cases_filenames = self.get_filenames_in_working_list(all_cases_path)
        print('len all casesfilenames ', len(all_cases_filenames))

        # print('len all cases after derivatives: ', len(all_cases))
        working_list_filepath = os.path.join(self.outputFolder,
                                             WORKING_LIST_FILENAME)
        remaining_list_filepath = os.path.join(self.outputFolder,
                                               REMAINING_LIST_FILENAME)

        all_cases_data = {
            'CASES': all_cases_filenames
        }

        if WORKING_LIST_FILENAME in output_folder_files:
            print('yesah!')
            good_match = self.verify_correspondence(working_list_filepath,
                                                    all_cases_filenames)
            if good_match:
                remaining_list_status = self.check_remaining_list(
                    self.outputFolder)
                print('remaining list stauts', remaining_list_status)
                if remaining_list_status:
                    with open(remaining_list_filepath, 'r') as file:
                        first_element = yaml.safe_load(file)['CASES'][0]
                        print('first element in remaining list', first_element)

                    if first_element in all_cases_filenames:
                        print('first element in all_cases filenames')
                        return True
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

                # # Check if all elements in remaining_list are in
                # all_cases_filenames
                # all_present = all(
                #     item in all_cases_filenames for item in remaining_list)

            print('test if first element')
            # with open(working_list_filepath, 'r') as file:
            #     first_element = yaml.safe_load(file)['CASES'][0]
            #     print('first_element: ', first_element)

        else:
            # all_cases_data = {
            #     'CASES': all_cases_filenames
            # }

            print('working_list_filepath: ', working_list_filepath)

            self.write_file_list(working_list_filepath, all_cases_filenames)
            self.write_file_list(remaining_list_filepath, all_cases_filenames)

            # # Creating working list
            # with open(working_list_filepath, 'w') as file:
            #     yaml.dump(all_cases_data, file)
            #
            #
            # # Creating remaining list
            # with open(remaining_list_filepath, 'w') as file:
            #     yaml.dump(all_cases_data, file)

    def get_working_list(self):
        """
        Get all files that have the correct file extension.
        """
        self.CasesPaths = sorted(glob.glob(f'{self.CurrentFolder}{os.sep}*'
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
        print('filtered_list: ', filtered_list)
        print('len filtered_list: ', len(filtered_list))
        return filtered_list

    def get_filenames_in_working_list(self, all_cases_path):
        """
        Get all filenames from filepaths.
        """
        self.Cases = sorted([os.path.split(i)[-1] for i in all_cases_path])
        print('self Cases: ', self.Cases)
        return self.Cases

    def verify_correspondence(self, working_list_filepath, all_cases_filenames):
        """
        Verify if the first element of the working list is in the volumes
        folder.
        """
        with open(working_list_filepath, 'r') as file:
            elements = yaml.safe_load(file)['CASES']
            print('first_element: ', elements)
        print('elements&*******', len(elements))
        print('all_cases_filenames', len(all_cases_filenames))
        if elements == all_cases_filenames:
            print('elements == all_case')
            return True
        else:
            print('false elemnts not all cases filenames')
            # Find differing elements
            missing_in_elements = [f for f in all_cases_filenames if
                                   f not in elements]
            missing_in_all_cases = [f for f in elements if
                                    f not in all_cases_filenames]

            # Print differing elements
            print("Missing in 'elements':", missing_in_elements)
            print("Missing in 'all_cases_filenames':", missing_in_all_cases)

        return False

    def check_remaining_list(self, outputFolder):
        remaining_list_filepath = os.path.join(self.outputFolder,
                                               REMAINING_LIST_FILENAME)
        # Convert folder_path to a Path object
        outputFolder = Path(outputFolder)
        # List all files in the folder
        output_folder_files = [str(file) for file in outputFolder.iterdir() if
                  file.is_file()]

        print('output_folder_files: ', output_folder_files)

        if remaining_list_filepath in output_folder_files:
            print('yesah remainign list file is in outpuf doler!')
            return True
        print('no remaining list filenam ein outpufdoler', REMAINING_LIST_FILENAME)
        print('outputFolder: ', outputFolder)
        return False

    def write_file_list(self, filepath, filenames):
        all_cases_data = {
            'CASES': filenames
        }
        with open(filepath, 'w') as file:
            yaml.dump(all_cases_data, file)


currentFolder1 = '/Users/maximebouthillier/gitmax/data_confid/praxis/site_007'
outputFolder1 = '/Users/maximebouthillier/gitmax/data_confid/test_bidon'
outputFolder2 = '/Users/maximebouthillier/gitmax/data_confid/test_bidon2'
WorkFiles = WorkFiles(currentFolder1, outputFolder1)

WorkFiles.check_working_list()
