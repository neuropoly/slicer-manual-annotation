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


    # def set_debug(self, enable):
    #     """
    #     Allows to set activate or deactivate debugging mode.
    #     """
    #     print('set_debug: ENABLE_DEBUG =', enable)
    #     global ENABLE_DEBUG
    #     ENABLE_DEBUG = enable

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


# def enter_function(func):
#     """
#     Decorator that enables to print the function name in the python console
#     and the name of the class that the function is associated with.
#     """
#
#     @functools.wraps(func)
#     def wrapper(self, *args, **kwargs):
#         def print_enter_function(self_of_cls, *args, **kwargs):
#             # This function should not return the func, but rather print the
#             # message
#             if ENABLE_DEBUG:
#                 print('\n *** enter_function ***:', func.__name__,
#                       '*** from class ***:', self_of_cls.__class__.__name__,
#                       '\n')
#
#         print_enter_function(self, *args, **kwargs)
#
#         # Call the original function with the provided arguments and return
#         # its result
#         result = func(self)
#         return result
#
#     return wrapper


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

        # Call the original function with the provided arguments and return
        # its result
        print('args', args)
        print('len args', len(args))
        print('kwargs', kwargs)
        print('len kwargs', len(kwargs))
        print('type arg', type(args))

        # if not (len(args) == 1 and args[0] is False):
        #     print('arg not none')
        #     result = func(self, *args, **kwargs)
        #     print('function worked')
        # else:
        #     result = func(self)

        # Use inspect to get argument names
        sig = inspect.signature(func)
        print('sig', sig)
        print('sig paragm', list(sig.parameters))
        args_list = list(sig.parameters)
        print('len args list', len(args_list))

        if len(args_list) == 1:
            print('args list has opnly self')
            result = func(self)
        else:
            print('***** has not only self')
            result = func(self, *args, **kwargs)

        # # Handle the case where the first and only argument is explicitly False
        # if len(args) == 1 and args[0] is False:
        #     print('mean that the function has no argument or 1 argument that '
        #           'is false')
        #     print("Single argument is explicitly False")
        #     print('self', self)
        #     print('args 0 type', type(args[0]))
        #     result = func(self)  # Pass the argument explicitly, including False
        # else:
        #     # Call the original function with the provided arguments
        #     print('else dd')
        #     result = func(self, *args, **kwargs)


        # if (len(args) == 1 and args[0] is False):
        #     print('self, ', self)
        #     print('testing', args[0] == self)
        #     if ((args[0] == self) == False):
        #         print('args 0 = self == false')
        #         result = func(self)
        #         # result = func(self, args[0])
        #     else:
        #         #ToDo: Find how to distinguish False as an argument from False
        #         # from default args Tuple. This is currently a LIMITATION only
        #         # if the first argument is False
        #         print('len 1')
        #         result = func(self)
        #         # result = func(self)
        #         print('len 1 worked')
        # else:
        #     if len(args) == 2 and args[1] == False:
        #         print('case scenario set to false object')
        #         result = func(self, args[1])
        #         print('terrer')
        #     else:
        #         print('arg not none')
        #         result = func(self, *args, **kwargs)
        #         print('function worked')

        return result

    return wrapper