class ArgParsingError(Exception):
    def __init__(self):
        self.__description = f'Error! The required argument(s) was(re) not entered'

    def __str__(self):
        return f'{self.__description}'
