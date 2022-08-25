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


class InitialFolderNotFoundError(Exception):
    __slots__ = ['__folder_name']

    def __init__(self, folder_name):
        self.__folder_name = folder_name
        self.__description = f"""Error! The initial folder doesn't exist: {self.__folder_name}"""

    def __str__(self):
        return f'{self.__description}'


class NoFilesToSortError(Exception):
    __slots__ = ['__folder_name']

    def __init__(self, folder_name):
        self.__folder_name = folder_name
        self.__description = f'Error! There are no files to sort in the folder: {self.__folder_name}'

    def __str__(self):
        return f'{self.__description} {self.__folder_name}'


class TargetFolderIsRelativeToInitialFolderError(Exception):
    __slots__ = ['__initial_folder', '__target_folder']

    def __init__(self, initial_folder, target_folder):
        self.__initial_folder = initial_folder
        self.__target_folder = target_folder
        self.__description = f'Error! The target folder {self.__target_folder} ' \
                             f'is relative to initial folder: {self.__target_folder}'

    def __str__(self):
        return f'{self.__description}'
