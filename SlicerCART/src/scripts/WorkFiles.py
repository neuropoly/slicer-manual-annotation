from utils import *

global KEEP_WORKING_LIST
KEEP_WORKING_LIST = True


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
        self.all_cases_path = WorkFiles.filter_working_list(self,
                                                            self.all_cases_path)

        self.all_cases_filenames = (
            self.get_filenames_in_working_list(self.all_cases_path))

    @enter_function
    def check_working_list(self):
        """
        Important function related to this class. Check in an already selected
        output folder if a working list is defined.
        """

        if WORKING_LIST_FILENAME in self.output_folder_files:
            # Check if the working list file corresponds to the volumes folder.
            good_match = self.check_correspondence(self.all_cases_filenames)
            if good_match:
                if self.check_remaining_list(
                        self.all_cases_filenames):
                    Debug.print(self, ('Working list corresponds to the '
                                       'filtered list from volumes folder. '
                                       'READY TO START!'))
                    pass
                else:
                    Debug.print(self, ('Good match of working list with '
                                       'filtered list from volumes folder. '
                                       'However, the remaining list is '
                                       'incorrect.'))
                    return False
            else:
                # Means that working list is different from filtered list
                # from volumes folder.

                # The user wants to keep the working list as is currently in
                # output folder.
                if KEEP_WORKING_LIST:
                    if WorkFiles.check_working_list_in_volumes(
                            self, self.all_cases_filenames):
                        Debug.print(self, 'All elements in working list are '
                                          'in the filtered list from volumes '
                                          'folder.')
                        working_list_filenames = (
                            WorkFiles.get_working_list_filenames(self))
                        if WorkFiles.check_remaining_list(self,
                                working_list_filenames):
                            Debug.print(self,
                                        'All elements in remaining list are '
                                        'in the working list from volumes. '
                                        'READY TO START!')
                            pass
                    else:
                        Debug.print(self, 'Some elements in the working list '
                                    'is/are not in the volumes folder.')
                        Dev.show_message_box(self, f'INVALID WORKING LIST FILE')
                        return False

                else:
                    # The user wants to take the working list associated with
                    # the filtered list from volumes folder.
                    # Any previous working list will be erased.

                    # Any old file (e.g. previous backup of working or
                    # remaining list will be overwritten).
                    self.create_backup()

                    # Overwrite any working list and/or remaining list.
                    self.write_file_list(self.working_list_filepath,
                                         self.all_cases_filenames)
                    self.write_file_list(self.remaining_list_filepath,
                                         self.all_cases_filenames)

                    pass


        else:
            # Create initial working list and remaining list.
            self.write_file_list(self.working_list_filepath,
                                 self.all_cases_filenames)

            working_list_filenames = WorkFiles.get_working_list_filenames(self)

            if os.path.exists(self.remaining_list_filepath):
                if self.check_remaining_list(working_list_filenames):
                    Debug.print(self, 'Cases in remaining list are in the '
                                      'working list. READY TO START!')
                    pass
                else:
                    Debug.print(self, ('There is a remaining list file in the '
                                   'output folder, but it is inconsistent with'
                                       ' working list. \n\n Please double '
                                       'check.'))
                    return False

            else:
                Debug.print(self, 'No remaining file exists. One is being '
                                 'created.')
                self.write_file_list(self.remaining_list_filepath,
                                     self.all_cases_filenames)

        return True

    @enter_function
    def get_working_list(self):
        """
        Get all files that have the correct file extension from volumes folder.
        """
        self.CasesPaths = sorted(glob(f'{self.CurrentFolder}{os.sep}*'
                                           f'*{os.sep}{INPUT_FILE_EXTENSION}',
                                           recursive=True))
        return self.CasesPaths

    @enter_function
    def filter_working_list(self, working_list):
        """
        Filter all files that have the correct working list configuration.
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
        Get all filenames from filepaths in the working list.
        """
        cases = sorted([os.path.split(i)[-1] for i in all_cases_path])
        return cases

    @enter_function
    def check_correspondence(self, all_cases_filenames):
        """
        Verify if the first element of the working list is in the volumes
        folder.
        """
        working_list_filenames = WorkFiles.get_working_list_filenames(self)

        if working_list_filenames == all_cases_filenames:
            if WorkFiles.check_remaining_list(self, working_list_filenames):
                Debug.print(self, 'All files in the working list are in the '
                                  'volumes folder. READY TO START!')
                pass

            else:
                Debug.print(self, ('Issues with remaining list. Creating one '
                                   'from the working list.'))
                WorkFiles.write_file_list(self, self.remaining_list_filepath,
                                          all_cases_filenames)

            return True

        else:
            # Find differing elements
            missing_in_elements = [f for f in all_cases_filenames if
                                   f not in working_list_filenames]
            missing_in_all_cases = [f for f in working_list_filenames if
                                    f not in all_cases_filenames]

            def print_message(elements):
                """
                Formats a list of elements into a string with
                each element on a new line.
                """
                if len(elements) > 10:
                    return "\n".join(f"{element}" for element in
                                     elements[:10]) + "\n..."
                else:
                    return "\n".join(f"{element}" for element in
                                 elements)

            # Print differing elements in a pop-up message.
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

            # For console debugging
            print("Missing in 'working_list_filepath':", missing_in_elements)
            print("Missing in 'all_cases_filenames':", missing_in_all_cases)

            # Display message box in 3D Slicer
            Dev.show_message_box(self, message, box_title='ATTENTION!')

        return False

    @enter_function
    def check_remaining_list(self, working_list_filenames):

        if REMAINING_LIST_FILENAME in self.output_folder_files:
            with open(self.remaining_list_filepath, 'r') as file:
                elements = yaml.safe_load(file)['CASES']
                first_element = elements[0]

            # Check if first element of remaining list is in working list
            # before looping (optimize performance).
            if first_element in working_list_filenames:
                if Dev.check_list_in_another(self, elements,
                                          working_list_filenames):
                    Debug.print(self, 'All element of remaining list are in '
                                      'working list. READY TO START!')
                    pass

                else:
                    message = ('INVALID REMAINING LIST FILE!\n\n'
                               ' *** ATTENTION! *** Not all elements '
                               'in remaining list file found in working list. '
                               '\n \n '
                               'Please double check.')
                    Debug.print(self, message)
                    Dev.show_message_box(self, message)

                    return False

            else:
                message = ('First element of the remaining list IS NOT in '
                      'the working list. Please double check list '
                      'correspondences.')
                Debug.print(self, message)
                Dev.show_message_box(self, message)

                return False

        else:
            message = (' *** ATTENTION! *** No remaining list file found '
                  'although working list is defined. Double check for '
                  'any manipulation errors. A new remaining file is '
                  'created right now corresponding to the working '
                  'list.')
            Debut.print(self, message)

            working_list_filenames = WorkFiles.get_working_list_filenames(self)
            self.write_file_list(self.remaining_list_filepath,
                                 working_list_filenames)

        return True

    @enter_function
    def write_file_list(self, filepath, filenames):
        """
        Write all filenames in a specific filepath.
        """
        all_cases_data = {
            'CASES': filenames
        }
        with open(filepath, 'w') as file:
            yaml.dump(all_cases_data, file)

    # @enter_function
    # def check_working_list_in_volumes(self, working_list_filepath,
    #                            all_cases_filenames):
    #     """
    #     Verify if elements of the working list are in the volumes folder list.
    #     """
    #     with open(working_list_filepath, 'r') as file:
    #         elements = yaml.safe_load(file)['CASES']
    #     return Dev.check_list_in_another(self, elements, all_cases_filenames)
    @enter_function
    def check_working_list_in_volumes(self, all_cases_filenames):
        """
        Verify if elements of the working list are in the volumes folder list.
        """
        working_list_filenames = WorkFiles.get_working_list_filenames(self)
        return Dev.check_list_in_another(self, working_list_filenames,
                                         all_cases_filenames)

    @enter_function
    def create_backup(self):
        """
        Create a backup of the working list file and/or the remaining list file.
        """
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
        Debug.print(self, 'Old versions created.')

    @enter_function
    def get_working_list_filenames(self):
        """
        Get all filenames from the working list.
        """
        with open(self.working_list_filepath, 'r') as file:
            working_list_filenames = yaml.safe_load(file)['CASES']
            return working_list_filenames

