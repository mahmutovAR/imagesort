class ArgParsingError(Exception):
    def __init__(self):
        self.__description = f'Error! The required argument(s) was(re) not entered'

    def __str__(self):
        return f'{self.__description}'


class ChecksumVerificationError(Exception):
    def __init__(self):
        self.__description = 'Error! Checksum verification completed with an error. ' \
                             'Deleting of the initial files canceled.'

    def __str__(self):
        return f'{self.__description}'


class FolderNotFoundError(Exception):
    __slots__ = ['__folder_name']

    def __init__(self, folder_name):
        self.__folder_name = folder_name
        self.__description = f"""Error! This folder doesn't exist: {self.__folder_name}"""

    def __str__(self):
        return f'{self.__description}'


class NoFilesToSortError(Exception):
    __slots__ = ['__folder_name']

    def __init__(self, folder_name):
        self.__folder_name = folder_name
        self.__description = f'Error! There are no files to sort in the folder: {self.__folder_name}'

    def __str__(self):
        return f'{self.__description} {self.__folder_name}'
