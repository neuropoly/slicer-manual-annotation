from utils import *

class WorkFiles():
    """
    This class is intended to manipulate different cases list in order to
    continue/facilitate the workflow from, for example when continuing from
    previous work sessions.
    """

    def __init__(self, currentFolder, outputFolder):
        self.CurrentFolder = currentFolder
        self.outputFolder = outputFolder
        self.working_list_filepath = os.path.join(self.outputFolder,
                                             ConfigPath.WORKING_LIST_FILENAME)
        self.remaining_list_filepath = os.path.join(self.outputFolder,
                                               ConfigPath.REMAINING_LIST_FILENAME)

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

        if ConfigPath.WORKING_LIST_FILENAME in self.output_folder_files:
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
                if ConfigPath.KEEP_WORKING_LIST:
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
                                           f'*{os.sep}{ConfigPath.INPUT_FILE_EXTENSION}',
                                           recursive=True))
        return self.CasesPaths

    @enter_function
    def filter_working_list(self, working_list):
        """
        Filter all files that have the correct working list configuration.
        Can use elif to build up and handle different inclusion criteria.
        """
        # ToDo: see issue 118
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
                remaining_list_filenames = (
                    WorkFiles.get_remaining_list_filenames(self))
                if WorkFiles.check_remaining_first_element(
                        self, remaining_list_filenames):

                    Debug.print(
                        self, ('Issues with remaining list. Creating one '
                                       'from the working list.'))
                    WorkFiles.write_file_list(
                        self, self.remaining_list_filepath,
                                              all_cases_filenames)
                else:
                    Debug.print(self, 'Remaining list is empty, but a new one '
                                      'will not be created '
                                      '(according to user preferences).')
                    pass

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
                # Limit to 10 elements the displayed pop-up.
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
                f"{ConfigPath.WORKING_LIST_FILENAME} misses cases from volumes folder\n"
                f"that should be included in the working list:\n\n"
                f"{print_message(missing_in_elements)}\n\n"
                f"Cases that should not be included in {ConfigPath.WORKING_LIST_FILENAME}\n"
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
        """
        Important function related to this class. Check the validity of the
        remaining list and create or not a new one depending on the scenario.

        Param: working_list_filenames: list of filenames in the working list
        (Attention! It is not the remaining list.)
        """

        if ConfigPath.REMAINING_LIST_FILENAME in self.output_folder_files:
            with open(self.remaining_list_filepath, 'r') as file:
                elements = yaml.safe_load(file)['CASES']
                if WorkFiles.check_remaining_first_element(self, elements):
                    first_element = elements[0]
                else:
                    Debug.print(self, 'First element in remaining list is '
                                      'none.')
                    if len(elements) > 1:
                        message = (' !!! PROBLEM !!! Remaining list might be '
                                   'corrupted. Please double check.')
                        Debug.print(self, message)
                        # Dev.show_message_box(self, message,
                        #                      box_title='ATTENTION!')
                        pass
                        return False
                    else:
                        Debug.print(self, 'Remaining list is empty, but this '
                                          'is ok for now.')
                        pass
                        return True

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
                    pass
                    return False

            else:
                message = ('First element of the remaining list IS NOT in '
                      'the working list. Please double check list '
                      'correspondences. A backup is created')
                Debug.print(self, message)
                # Dev.show_message_box(self, message)

                # Any old file (e.g. previous backup of working or
                # remaining list will be overwritten).
                self.create_backup()

                working_list_filenames = (
                    WorkFiles.get_working_list_filenames(self))

                # Overwrite any working list and/or remaining list.
                self.write_file_list(self.remaining_list_filepath,
                                     working_list_filenames)

        else:
            message = (' *** ATTENTION! *** No remaining list file found '
                  'although working list is defined. Double check for '
                  'any manipulation errors. A new remaining file is '
                  'created right now corresponding to the working '
                  'list.')
            Debug.print(self, message)

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
                                    f'd_{ConfigPath.WORKING_LIST_FILENAME}')
        remaining_list_backup_path = \
            (f'{self.outputFolder}'
             f'{os.sep}old_{ConfigPath.REMAINING_LIST_FILENAME}')

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

    @enter_function
    def get_remaining_list_filenames(self):
        """
        Get all filenames from the remaining list.
        """
        with open(self.remaining_list_filepath, 'r') as file:
            remaining_list_filenames = yaml.safe_load(file)['CASES']
            return remaining_list_filenames

    @enter_function
    def get_working_list_filepaths(self, working_list_filenames):
        """
        Get all working list filepaths.
        """
        filenames_path = []
        for element in working_list_filenames:
            for path in self.all_cases_path:
                if element in path:
                    filenames_path.append(path)
        return filenames_path

    @enter_function
    def get_remaining_list_filepaths(self, remaining_list_filenames):
        """
        Get all remaining list filepaths.
        """
        filenames_path = []
        for element in remaining_list_filenames:
            for path in self.all_cases_path:
                if element in path:
                    filenames_path.append(path)
        return filenames_path

    @enter_function
    def check_remaining_first_element(self, remaining_list):
        """
        Check validity of the remaining list, based on first element.
        """
        if remaining_list != None and remaining_list != []:
            if remaining_list[0] != None:
                Debug.print(self, f"Remaining list 1st element is: "
                                  f"{remaining_list[0]}")
                pass
                return True
        return False

    @enter_function
    def get_all_cases_path(self):
        """
        Get all cases path from the working list filepaths.
        """
        return self.working_list_filepath

    @enter_function
    def find_index_from_filename(self, filename, list):
        """
        Allow to find the index of an element (e.g. filename) in a list.
        """
        index = list.index(filename)
        return index

    @enter_function
    def find_path_from_filename(self, filename):
        """
        Find path from a filename.
        """
        for filepath in self.all_cases_path:
            if filename in filepath:
                return filepath

    @enter_function
    def adjust_remaining_list(self, filename):
        """
        Adjust the remaining list by removing a specific filename.
        """
        remaining_list_filenames = WorkFiles.get_remaining_list_filenames(self)
        remaining_list_filenames.remove(filename)

        WorkFiles.write_file_list(self, self.remaining_list_filepath,
                                  remaining_list_filenames)
