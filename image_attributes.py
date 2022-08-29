from os.path import basename, isfile, splitext
from os.path import join as os_path_join
from PIL import Image


class ImageAttributes:
    """Class receives full path if the image and gets its resolution, if it couldn't be got then
    the image will be sorted to the folder 'Not images'."""

    __slots__ = ['__initial_file_path', '__image_resolution', '__sorted_file_path']

    def __init__(self, initial_file_path):
        self.__initial_file_path = initial_file_path
        self.__image_resolution = 'not sorted'
        self.__sorted_file_path = 'no path'

    def get_initial_file_path(self) -> str:
        return self.__initial_file_path

    def get_file_name(self) -> str:
        return basename(self.__initial_file_path)

    def define_image_resolution(self) -> None:
        try:
            with Image.open(self.__initial_file_path) as image_to_size:
                width, height = image_to_size.size
        except:
            self.__image_resolution = 'Not images'
        else:
            self.__image_resolution = f'{width}x{height}'

    def get_image_resolution(self) -> str:
        return self.__image_resolution

    def set_sorted_file_path(self, sorted_file_path) -> None:
        self.__sorted_file_path = sorted_file_path

    def get_sorted_file_path(self) -> str:
        return self.__sorted_file_path
