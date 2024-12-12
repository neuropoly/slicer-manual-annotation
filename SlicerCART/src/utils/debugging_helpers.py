import functools
ENABLE_DEBUG = True
class Debug:
    def __init__(self):
        pass


    # def set_debug(self, enable):
    #     print('set_debug: enable=', enable)
    #     ENABLE_DEBUG = enable #ToDo: enventually, ENABLE_DEBUG variable might
    #     # be moved to another python file. Ensure that the variable is still
    #     # accessible for calling.
    #
    #
    # def print_dictionary(self, dictionary, name=None):
    #     if ENABLE_DEBUG:
    #         if name is None:
    #             name = "dictionary"
    #         for element in dictionary:
    #             print(f"{name} {element}: ", dictionary[element])
    #
    # def print(self, statement='', ):
    #     if ENABLE_DEBUG:
    #         print(statement)





# Decorator to automatically pass the function name
# def log_function_call(func):
#     @functools.wraps(func)
#     def wrapper(self, *args, **kwargs):
#         debug = Debug()
#         # Automatically pass the function name to the enter_function method
#         debug.enter_function(func.__name__)  # func.__name__ gets the name of the current function
#         return func(self, *args, **kwargs)
#     return wrapper


# Decorator to automatically pass the function name
def enter_function(func):
    def wrapper(self, *args, **kwargs):
        @functools.wraps(func)
        def enter_function(self_of_cls, *args, **kwargs):
            if ENABLE_DEBUG:
                print('\n *** enter_function ***:', func.__name__,
                      '*** from class ***:', self.__class__.__name__, '\n')
                # print('class name to which belongs the function:', self.__class__.__name__)
            return None
        return enter_function(self, *args, **kwargs)
    return wrapper