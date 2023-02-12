class InitialFolderNotFoundError(Exception):
    __slots__ = ['__folder_name']

    def __init__(self, folder_name):
        self.__folder_name = folder_name
        self.__description = f'Error! The initial folder not found: {self.__folder_name}'

    def __str__(self):
        return f'{self.__description}'
