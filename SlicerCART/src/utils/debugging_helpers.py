import functools
import inspect
from utils.global_variables import ENABLE_DEBUG


class Debug:
    """
    This class is used for facilitating debugging using the 3D Slicer python
    console. Feel free to add any function that is useful for debugging.

    Usage: in any python that has imported the utils folder, do:
            Debug.function_name(self, *args, **kwargs)
            where function_name is the function in the Debug class
    """

    def __init__(self):
        pass

    def set_debug(self, enable):
        """
        Allows to set activate or deactivate debugging mode.
        """
        print('set_debug: ENABLE_DEBUG =', enable)
        global ENABLE_DEBUG
        ENABLE_DEBUG = enable

    def print_dictionary(self, dictionary, name=None):
        """
        Prints out a dictionary with keys as keys and values as values on
        multiples lines.
        """
        if ENABLE_DEBUG:
            if name is None:
                name = "dictionary"
            for element in dictionary:
                print(f"{name} {element}: ", dictionary[element])

    def print(self, statement='', ):
        """
        Prints out a statement only if debugging mode is enabled. Allows to
        keep print statement in the code without contaminating the python
        console for non-debugging usage.
        """
        if ENABLE_DEBUG:
            print(statement)

def enter_function(func):
    """
    Decorator that enables to print the function name in the python console
    and the name of the class that the function is associated with.
    """

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        def print_enter_function(self_of_cls, *args, **kwargs):
            # This function should not return the func, but rather print the
            # message
            if ENABLE_DEBUG:
                print('\n *** enter_function ***:', func.__name__,
                      '*** from class ***:', self_of_cls.__class__.__name__,
                      '\n')

        print_enter_function(self, *args, **kwargs)

        # Use inspect module to get argument names in the original function
        sig = inspect.signature(func)
        args_list = list(sig.parameters)

        # Call the original function with the provided arguments and return
        # its result. Calling method depends on the method signature.
        if len(args_list) == 1:
            # Mean that the original function has only self (no other parameter)
            result = func(self)
        else:
            # Mean that the original function uses arguments
            result = func(self, *args, **kwargs)

        return result

    return wrapper