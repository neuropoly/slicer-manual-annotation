# Function that list all the modules in the same folder except the current file
import os
import glob
from utils.requirements import *


def list_modules_in_folder(folder_name, filename):
    print('in list current folder***8')
    # # Get the current file's directory
    current_folder = os.path.dirname(__file__)
    print('current folder***', current_folder)
    reversed_path = current_folder[::-1]
    print('reversed path', reversed_path)
    parts = reversed_path.split(os.sep, 1)
    print('parts', parts)
    extracted_path = parts[1][::-1]
    print('extracted path', extracted_path)
    real_path = os.path.join(extracted_path, folder_name)
    print('real_path', real_path)
    list_of_files = [f for f in os.listdir(real_path) if os.path.isfile(
        os.path.join(
        real_path, f))]
    print('list_of_files', list_of_files, 'len', len(list_of_files))
    list_of_files.remove(filename)
    list_of_files.remove('__init__.py')
    print('list_of_files', list_of_files, 'len', len(list_of_files))
    list_of_files = [os.path.splitext(file)[0] for file in list_of_files]
    print('list_of_files3', list_of_files, 'len', len(list_of_files))


    return list_of_files

    # # Get the current file's name (excluding extension)
    # current_file = os.path.splitext(os.path.basename(__file__))[0]
    #
    # # List all Python files in the directory except the current file
    # modules = [
    #     os.path.splitext(os.path.basename(f))[0]
    #     # Remove path and .py extension
    #     for f in glob.glob(os.path.join(current_folder, "*.py"))
    #     if os.path.isfile(f) and os.path.splitext(os.path.basename(f))[
    #         0] != current_file
    # ]

    # return modules

# import importlib

def import_modules_from_scripts(modules_list):
    for module_name in modules_list:
        try:
            # Import each module dynamically from 'scripts'
            full_module_name = f"scripts.{module_name}"
            module = importlib.import_module(full_module_name)
            # Load all contents of the module into the global namespace
            globals().update(vars(module))
        except ImportError as e:
            print(f"Could not import module {module_name}: {e}")

