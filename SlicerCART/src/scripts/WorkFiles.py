import shutil
from utils import *

global KEEP_WORKING_LIST
KEEP_WORKING_LIST = False


class WorkFiles():
    def __init__(self, currentFolder, outputFolder):
        self.CurrentFolder = currentFolder
        self.outputFolder = outputFolder
        self.working_list_filepath = os.path.join(self.outputFolder,
                                             WORKING_LIST_FILENAME)
        self.remaining_list_filepath = os.path.join(self.outputFolder,
                                               REMAINING_LIST_FILENAME)

        self.output_folder_files = os.listdir(self.outputFolder)

        self.all_cases_path = WorkFiles.get_working_list(self)
        self.all_cases_path = WorkFiles.filter_working_list(self, self.all_cases_path)

        self.all_cases_filenames = self.get_filenames_in_working_list(self.all_cases_path)

    @enter_function
    def check_working_list(self):
        """
        Check in already selected output folder if a working list is defined.
        """
        # working_list_filepath = os.path.join(self.outputFolder,
        #                                      WORKING_LIST_FILENAME)
        # remaining_list_filepath = os.path.join(self.outputFolder,
        #                                        REMAINING_LIST_FILENAME)
        #
        # output_folder_files = os.listdir(self.outputFolder)
        #
        # all_cases_path = WorkFiles.get_working_list(self)
        # all_cases_path = WorkFiles.filter_working_list(self, all_cases_path)
        #
        # all_cases_filenames = self.get_filenames_in_working_list(all_cases_path)

        if WORKING_LIST_FILENAME in self.output_folder_files:
            good_match = self.check_correspondence(self.working_list_filepath,
                                                   self.all_cases_filenames)
            if good_match:
                if self.check_remaining_list(
                        self.all_cases_filenames):
                    print('in good match self check remianing list ready to '
                          'start')
                    pass
                else:
                    print('in good match remaining list incorrect return false')
                    return False

                # if remaining_list_status:
                #     with open(remaining_list_filepath, 'r') as file:
                #         first_element = yaml.safe_load(file)['CASES'][0]
                #     if first_element in all_cases_filenames:
                #         print('First element of remaining list in working '
                #               'list. READY TO START.')
                #
                #     else:
                #         print('First element of the remaining list IS NOT in '
                #               'the working list. Please double check list '
                #               'correspondences.')
                #         return False
                #
                # else:
                #     print(' *** ATTENTION! *** No remaining list file found '
                #           'although working list is defined. Double check for '
                #           'any manipulation errors. A new remaining file is '
                #           'created right now corresponding to the working '
                #           'list.')
                #     self.write_file_list(remaining_list_filepath,
                #                          all_cases_filenames)


            else:
                print('discordances found')
                if KEEP_WORKING_LIST:
                    print('in  adjust correpsondance')
                    if WorkFiles.check_working_list_in_volumes(
                            self, self.working_list_filepath, self.all_cases_filenames):
                        print('workling list ok with volume folder although '
                              'discordant')
                        with open(self.working_list_filepath, 'r') as file:
                            working_list_filenames = yaml.safe_load(file)[
                                'CASES']
                        if WorkFiles.check_remaining_list(self,
                                working_list_filenames):
                            print(' keep working list remaining list ok')
                            pass
                    else:
                        print('working list not in volume folder')
                        Dev.show_message_box(self, f'INVALID WORKING LIST FILE')
                        return False
                else:
                    print('in else adjust correspondence')
                    print('RESET WORKING LIST AND ')
                    self.create_backup()



                    # # Create backup of working list
                    # working_list_backup_path = (f'{self.outputFolder}{os.sep}ol'
                    #                        f'd_{WORKING_LIST_FILENAME}')
                    # remaining_list_backup_path = \
                    #     (f'{self.outputFolder}'
                    #      f'{os.sep}old_{REMAINING_LIST_FILENAME}')
                    # shutil.copy(working_list_filepath, working_list_backup_path)
                    # shutil.copy(remaining_list_filepath, remaining_list_backup_path)
                    # print('copied old version')
                    # create new working list
                    # Create initial working list and remaining list.
                    self.write_file_list(self.working_list_filepath,
                                         self.all_cases_filenames)
                    self.write_file_list(self.remaining_list_filepath,
                                         self.all_cases_filenames)

                    pass


        else:
            # Create initial working list and remaining list.
            self.write_file_list(self.working_list_filepath, self.all_cases_filenames)

            working_list_filenames = WorkFiles.get_working_list_filenames(self)
            print('got working list filenames in else', working_list_filenames)

            if os.path.exists(self.remaining_list_filepath):
                if self.check_remaining_list(working_list_filenames):
                    print('check remianing files else ok 3332')
                else:
                    print('There is a remaining list file in the output '
                          'folder, but it is inconsistent with working '
                          'list. \n\n Please double check. ')
                    return False
                    # message = ('There is a remaining list file in the output '
                    #            'folder, but it is inconsistent with working '
                    #            'list. \n\n Please double check.')
                    # Dev.show_message_box(self, message)
            else:
                print(' no remaining file exit. one is being created')
                self.write_file_list(self.remaining_list_filepath, self.all_cases_filenames)

        return True

    @enter_function
    def get_working_list(self):
        """
        Get all files that have the correct file extension.
        """
        self.CasesPaths = sorted(glob(f'{self.CurrentFolder}{os.sep}*'
                                           f'*{os.sep}{INPUT_FILE_EXTENSION}',
                                           recursive=True))
        return self.CasesPaths

    @enter_function
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

    @enter_function
    def get_filenames_in_working_list(self, all_cases_path):
        """
        Get all filenames from filepaths.
        """
        cases = sorted([os.path.split(i)[-1] for i in all_cases_path])
        return cases

    @enter_function
    def check_correspondence(self, working_list_filepath, all_cases_filenames):
        """
        Verify if the first element of the working list is in the volumes
        folder.
        """
        with open(working_list_filepath, 'r') as file:
            working_list_filenames = yaml.safe_load(file)['CASES']


        if working_list_filenames == all_cases_filenames:
            if WorkFiles.check_remaining_list(self, working_list_filenames):
                print('a;l cases in folder')
                pass
            else:
                print('not all cases in folder will create remaing list')
                WorkFiles.write_file_list(self, self.remaining_list_filepath,
                                          all_cases_filenames)

            return True

        else:
            # Find differing elements
            missing_in_elements = [f for f in all_cases_filenames if
                                   f not in working_list_filenames]
            missing_in_all_cases = [f for f in working_list_filenames if
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
            # def print_message(elements):
            #     """
            #     Formats a list of elements into a string with each element on a new line.
            #     """
            #     return "\n".join(f"{element}" for element in
            #                      elements)  # Add optional bullet points for clarity
            def print_message(elements):
                """
                Formats a list of elements into a string with each element on a new line.
                """
                if len(elements) > 10:
                    return "\n".join(f"{element}" for element in
                                     elements[:10]) + "\n..."  # Add optional bullet
                    # points for clarity
                else:
                    return "\n".join(f"{element}" for element in
                                 elements)  # Add optional bullet points for clarity

            # Print differing elements
            message = (
                f"WORKING_LIST AND VOLUMES FOLDER ARE INCONSISTENT.\n"
                f"PLEASE DOUBLE CHECK:\n\n"
                f"{WORKING_LIST_FILENAME} misses cases from volumes folder\n"
                f"that should be included in the working list:\n\n"
                f"{print_message(missing_in_elements)}\n\n"
                f"Cases that should not be included in {WORKING_LIST_FILENAME}\n"
                f"according to configuration:\n\n"
                f"{print_message(missing_in_all_cases)}"
            )

            # For console debugging (optional)
            print("Missing in 'working_list_filepath':", missing_in_elements)
            print("Missing in 'all_cases_filenames':", missing_in_all_cases)

            # Display message box in 3D Slicer
            Dev.show_message_box(self, message, box_title='ATTENTION!')


        return False

    @enter_function
    def check_remaining_list(self, working_list_filenames):

        # # List all files in the folder
        # output_folder_files = os.listdir(outputFolder)

        if REMAINING_LIST_FILENAME in self.output_folder_files:
            with open(self.remaining_list_filepath, 'r') as file:
                elements = yaml.safe_load(file)['CASES']
                first_element = elements[0]
            print('first element555', first_element)
            print('wqorking list filenames', working_list_filenames)
            if first_element in working_list_filenames:
                print('First element of remaining list in working '
                      'list. READY TO START.')
                if Dev.check_list_in_another(self, elements,
                                          working_list_filenames):
                    print('all element sin remainign liust are in volumes')
                    pass
                else:
                    print(' *** ATTENTION! *** Not all elements in remaining '
                          'list file found in working list. Please double '
                          'check.')
                    message = ('INVALID REMAINING LIST FILE!\n\n'
                               ' *** ATTENTION! *** Not all elements '
                               'in remaining list file found in working list. \n \n '
                               'Please double check.')
                    Dev.show_message_box(self, message)

                    return False


            else:
                print('First element of the remaining list IS NOT in '
                      'the working list. Please double check list '
                      'correspondences.')
                Dev.show_message_box(self, f'INVALID REMAINING LIST FILE!')

                return False

        else:
            print(' *** ATTENTION! *** No remaining list file found '
                  'although working list is defined. Double check for '
                  'any manipulation errors. A new remaining file is '
                  'created right now corresponding to the working '
                  'list.')
            with open(self.working_list_filepath, 'r') as file:
                working_list_filenames = yaml.safe_load(file)['CASES']
            self.write_file_list(self.remaining_list_filepath,
                                 working_list_filenames)

        return True

    @enter_function
    def write_file_list(self, filepath, filenames):
        all_cases_data = {
            'CASES': filenames
        }
        with open(filepath, 'w') as file:
            yaml.dump(all_cases_data, file)

    @enter_function
    def check_working_list_in_volumes(self, working_list_filepath,
                               all_cases_filenames):
        """
        Verify if the first element of the working list is in the volumes
        folder.
        """

        with open(working_list_filepath, 'r') as file:
            elements = yaml.safe_load(file)['CASES']
        print('working list in volume folder')
        return Dev.check_list_in_another(self, elements, all_cases_filenames)
        # for element in elements:
        #     if element in all_cases_filenames:
        #         continue
        #     else:
        #         # print('working list not in volume folder')
        #         # Dev.show_message_box(self, f'INVALID WORKING LIST FILE')
        #         return False



    @enter_function
    def create_backup(self):
        # Create backup of working list
        working_list_backup_path = (f'{self.outputFolder}{os.sep}ol'
                                    f'd_{WORKING_LIST_FILENAME}')
        remaining_list_backup_path = \
            (f'{self.outputFolder}'
             f'{os.sep}old_{REMAINING_LIST_FILENAME}')
        if os.path.exists(self.working_list_filepath):
            shutil.copy(self.working_list_filepath, working_list_backup_path)
        if os.path.exists(self.remaining_list_filepath):
            shutil.copy(self.remaining_list_filepath,
                        remaining_list_backup_path)

        # shutil.copy(self.working_list_filepath, working_list_backup_path)
        # shutil.copy(self.remaining_list_filepath, remaining_list_backup_path)
        print('copied old version')

    @enter_function
    def create_working_and_remaining_cases_files(self, all_cases_filenames):
        pass

    # @enter_function
    # def check_list_in_another(self, list1, list2):
    #     for element in list:
    #         if element in list2:
    #             continue
    #         else:
    #             # print('working list not in volume folder')
    #             # Dev.show_message_box(self, f'INVALID WORKING LIST FILE')
    #             return False

    @enter_function
    def get_working_list_filenames(self):
        with open(self.working_list_filepath, 'r') as file:
            working_list_filenames = yaml.safe_load(file)['CASES']
            return working_list_filenames






# currentFolder1 = '/Users/maximebouthillier/gitmax/data_confid/praxis/site_007'
# outputFolder1 = '/Users/maximebouthillier/gitmax/data_confid/test_bidon'
# outputFolder2 = '/Users/maximebouthillier/gitmax/data_confid/test_bidon2'
# WorkFiles = WorkFiles(currentFolder1, outputFolder1)
#
# WorkFiles.check_working_list()
