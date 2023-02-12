class TargetFolderIsRelativeToInitialFolderError(Exception):
    __slots__ = ['__initial_folder', '__target_folder']

    def __init__(self, initial_folder, target_folder):
        self.__initial_folder = initial_folder
        self.__target_folder = target_folder
        self.__description = f'Error! The target folder {self.__target_folder} ' \
                             f'is relative to initial folder: {self.__target_folder}'

    def __str__(self):
        return f'{self.__description}'
