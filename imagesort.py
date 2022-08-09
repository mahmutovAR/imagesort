from argparse import ArgumentParser, RawDescriptionHelpFormatter
from chameleon import PageTemplateLoader
from hashlib import sha256
from os import chmod, mkdir, remove, rename
from os import walk as os_walk
from os.path import abspath, basename, dirname, isdir, isfile, splitext
from os.path import join as os_path_join
from pathlib import Path
from PIL import Image
from shutil import copy as shutil_copy
from shutil import rmtree
from stat import S_IWRITE
from sys import exit as sys_exit

# global variables:
SCRIPT_PATH = abspath(dirname(__file__))  # SCRIPT_PATH = Path(__file__).resolve().parent
SHA256_BLOCK_SIZE = 65536


class FileAttributes:
    __slots__ = ['__initial_file_full_path', '__folder_name_for_sorted_file', '__sorted_file_path']

    def __init__(self, initial_file_full_path):
        self.__initial_file_full_path = initial_file_full_path
        self.__folder_name_for_sorted_file = 'not sorted'
        self.__sorted_file_path = 'no path'

    def set_initial_full_path(self, initial_file_full_path) -> None:
        self.__initial_file_full_path = initial_file_full_path

    def return_initial_file_path(self) -> str:
        return self.__initial_file_full_path

    def get_folder_name_for_sorted_file(self) -> None:
        try:
            with Image.open(self.__initial_file_full_path) as image_to_size:
                w, h = image_to_size.size
        except:
            self.__folder_name_for_sorted_file = 'Not images'
        else:
            self.__folder_name_for_sorted_file = f'{w}x{h}'

    def return_folder_name_for_sorted_file(self) -> str:
        return self.__folder_name_for_sorted_file

    def get_path_for_sorted_file(self) -> None:
        initial_file_name = basename(self.__initial_file_full_path)
        sorted_file_path = os_path_join(TARGET_FOLDER,
                                        self.return_folder_name_for_sorted_file(), initial_file_name)
        if isfile(sorted_file_path):
            num = 1
            file_path_without_type, file_type = splitext(sorted_file_path)
            while isfile(os_path_join(f'{file_path_without_type}({num}){file_type}')):
                num += 1
            new_sorted_file_path = f'{file_path_without_type}({num}){file_type}'
            self.__sorted_file_path = new_sorted_file_path
        else:
            self.__sorted_file_path = sorted_file_path

    def return_sorted_file_path(self) -> str:
        return self.__sorted_file_path


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


class ChecksumVerificationError(Exception):
    def __init__(self):
        self.__description = 'Error! Checksum verification completed with an error. ' \
                             'Deleting of the initial files canceled.'

    def __str__(self):
        return f'{self.__description}'


class ArgParsingError(Exception):
    def __init__(self):
        self.__description = f'Error! The required argument(s) was(re) not entered'

    def __str__(self):
        return f'{self.__description}'


def parse_main_args() -> 'argparse.Namespace':
    """The argparse module returns ArgumentParser object with main data from CLI."""
    parser = ArgumentParser(prog='ImageSort',
                            usage='imagesort.py [-h] [script_mode, initial_folder, target_folder]',
                            formatter_class=RawDescriptionHelpFormatter,
                            description='''
        %(prog)s sorts images by their resolutions.
        Reference information about application:
          dryrun "initial_dir" "report_dir" = app sorts files from "ini_dir" and generates html report in "report_dir"
          copy "initial_dir" "target_dir" = app sorts and copies files from "initial_dir" into "target_dir"
          move "initial_dir" "target_dir" = app sorts and moves files from "initial_dir" into "target_dir"
          sort "initial_dir" = app sorts files into "initial_dir" and deletes the initial files''')
    parser.add_argument('script_mode', type=str, help='Choose the mode',
                        choices=['dryrun', 'copy', 'move', 'sort'])
    parser.add_argument('initial_folder', type=Path, help='Input the initial folder', nargs='?', default=None)
    parser.add_argument('target_folder', type=Path, help='Input the auxiliary folder', nargs='?', default=None)
    return parser.parse_args()


def get_global_variables(CLI_data: 'argparse.Namespace') -> None:
    """Returns global variables (MODE, INITIAL FOLDER, TARGET FOLDER) from ArgumentParser object."""
    global MODE, INITIAL_FOLDER, TARGET_FOLDER
    MODE = CLI_data.script_mode
    INITIAL_FOLDER = convert_path_to_str(CLI_data.initial_folder)

    if MODE == 'sort':
        TARGET_FOLDER = create_temporary_folder()
    else:
        TARGET_FOLDER = convert_path_to_str(CLI_data.target_folder)


def convert_path_to_str(input_data: 'pathlib.PosixPath') -> str:
    """Converts 'pathlib.PosixPath' object to the string and returns path if directory exists.
    If 'pathlib.PosixPath' object is None then the ArgParsingError is raised.
    If directory doesn't exist then the FolderNotFoundError is raised."""
    if not input_data:
        raise ArgParsingError
    output_path = str(input_data)
    if not isdir(output_path):
        raise FolderNotFoundError(output_path)
    else:
        return output_path


def get_files_and_attributes_from_initial_dir() -> list and dict:
    """Returns list of objects FileAttributes class."""
    files_from_initial_folder, ini_dir_structure = get_all_files_from_folder(INITIAL_FOLDER)

    ini_files_attributes = [FileAttributes(file_to_sort)
                            for file_to_sort in files_from_initial_folder]

    return ini_files_attributes, ini_dir_structure


def get_all_files_from_folder(given_folder: str) -> list and dict:
    """Returns list of paths of all files from given directory and full structure of the given directory.
    full_paths_from_dir = ['full_path_to_the_file_1', 'full_path_to_the_file_2', etc.]
    dir_structure = {'full_path_to_the_folder_1': ['file_name_1', 'file_name_2', etc.], etc.}
    """
    full_paths_from_dir = list()
    dir_structure = dict()
    for dir_path, dir_name, files_in_dir in os_walk(given_folder):
        for file in files_in_dir:
            full_paths_from_dir.append(os_path_join(dir_path, file))
        if files_in_dir:
            dir_structure[f"""{dir_path.replace(given_folder, '"root dir" ')}"""] = files_in_dir

    if not full_paths_from_dir:
        raise NoFilesToSortError(given_folder)
    else:
        return full_paths_from_dir, dir_structure


def get_folder_names_for_sorted_files(ini_files_attributes: list) -> None:
    """Runs function "get_folder_name_for_sorted_file" for each file from initial folder."""
    for file_to_sort in ini_files_attributes:
        file_to_sort.get_folder_name_for_sorted_file()


def generate_html_report(ini_files_attributes: list, files_before_sorting: dict) -> 'html report':
    """Generates the html report which shows current structure and suggested reorganization.
    The html report will be created in the given directory.
    """
    html_report_name = choose_name_for_html_report(TARGET_FOLDER)

    files_after_sorting = dict()
    for file_to_sort in ini_files_attributes:
        full_path = file_to_sort.return_initial_file_path()
        file_name = basename(full_path)
        folder_name = file_to_sort.return_folder_name_for_sorted_file()
        if folder_name not in files_after_sorting.keys():
            files_after_sorting[folder_name] = list()
        files_after_sorting[folder_name].append(file_name)

    sorted_output_files = dict()
    for folder_name in sorted(files_after_sorting):
        sorted_output_files[folder_name] = sorted(files_after_sorting[folder_name])

    try:
        templates = PageTemplateLoader(os_path_join(SCRIPT_PATH, "templates"))
        tmpl = templates['report_temp.pt']

        data_for_html = tmpl(title=html_report_name, input_folder=INITIAL_FOLDER,
                             initial_dir=files_before_sorting, structure=sorted_output_files)
    except Exception as err:
        print(f'The HTML report generation caused the exception:\n{err}')
    else:
        report = open(os_path_join(TARGET_FOLDER, html_report_name), 'w')
        report.write(data_for_html)
        report.close()
        print(f'The file "{html_report_name}" was created in the directory "{TARGET_FOLDER}"')


def choose_name_for_html_report(given_folder: str) -> str:
    """Checks given folder for existing file 'DryRun report.html', if file already exists then
    the report will be renamed before generating, "({num})" will be added to its name."""
    if isfile(os_path_join(given_folder, 'DryRun report.html')):
        num = 1
        while isfile(os_path_join(given_folder, f'DryRun report({num}).html')):
            num += 1
        return f'DryRun report({num}).html'
    else:
        return 'DryRun report.html'


def copy_sorted_files(ini_files_attributes: list) -> None:
    """Creates new folders (Width x Height) or 'Not images' and copies files from initial folder to the new one,
    if folder already exists files will be added there, if there is file with the same name,
    then the new file will be renamed, "({num})" will be added to its name (for example, "wallpaper(3)").
    """
    for file_to_sort in ini_files_attributes:
        initial_file_path = file_to_sort.return_initial_file_path()
        folder_to_copy_file = os_path_join(TARGET_FOLDER, file_to_sort.return_folder_name_for_sorted_file())
        create_dir_if_not_exists(folder_to_copy_file)
        file_to_sort.get_path_for_sorted_file()
        path_for_sorted_file = file_to_sort.return_sorted_file_path()
        shutil_copy(initial_file_path, path_for_sorted_file)


def create_dir_if_not_exists(given_path: str) -> None:
    """Makes directory if it doesn't exist."""
    if not isdir(given_path):
        mkdir(given_path)


def integrity_validation(ini_files_attributes: list) -> None:
    """Compares checksums of each file from initial folder and copied files after reorganization.
    Displays information about amount of sorted files."""
    total_ini_files = len(ini_files_attributes)
    total_images = 0
    total_not_images = 0
    for file_to_sort in ini_files_attributes:
        initial_file = file_to_sort.return_initial_file_path()
        sorted_file = file_to_sort.return_sorted_file_path()
        if get_checksum(initial_file) != get_checksum(sorted_file):
            raise ChecksumVerificationError
        if file_to_sort.return_folder_name_for_sorted_file() == 'Not images':
            total_not_images += 1
        else:
            total_images += 1
    print(f'Checksum verification completed successfully\n'
          f'From initial folder was(re) sorted successfully {total_ini_files} files:\n'
          f'Images{total_images:>20}\n'
          f'Not images{total_not_images:>16}')


def get_checksum(file_path: str) -> str:
    """Returns checksum of the given file."""
    sha_hashing = sha256()
    with open(file_path, 'rb') as CF:
        file_buffer = CF.read(SHA256_BLOCK_SIZE)
        while len(file_buffer) > 0:
            sha_hashing.update(file_buffer)
            file_buffer = CF.read(SHA256_BLOCK_SIZE)
    return sha_hashing.hexdigest()


def delete_folder(folder_for_deleting: str) -> None:
    """Deletes given folder with all nested folder(s) and file(s)."""
    try:
        rmtree(folder_for_deleting, onerror=delete_readonly_file)
    except PermissionError as err:
        sys_exit(f'Attention! Deleting of the "{folder_for_deleting}" raised the exception: {err}'
                 f'\nPlease close the folder in explorer or another application and try again')
    except Exception as err:
        sys_exit(f'Attention! Deleting of the "{folder_for_deleting}" raised the exception: {err}')


def delete_readonly_file(action, name, exc) -> None:
    """Deletes files with attribute "readonly"."""
    chmod(name, S_IWRITE)
    remove(name)


def create_temporary_folder() -> str:
    """Creates temporary folder for coping sorted files."""
    temp_target_folder = os_path_join(dirname(INITIAL_FOLDER), 'ImageSort temp folder')
    if isdir(temp_target_folder):
        num = 1
        while isdir(os_path_join(INITIAL_FOLDER, f'ImageSort temp folder({num})')):
            num += 1
        temp_target_folder = os_path_join(INITIAL_FOLDER, f'ImageSort temp folder({num})')
    mkdir(temp_target_folder)
    return temp_target_folder


def rename_temp_folder_to_initial() -> None:
    """Renames temporary target folder into initial folder."""
    rename(TARGET_FOLDER, INITIAL_FOLDER)


def main(CLI_data: 'argparse.Namespace'):
    """This is the main function of the script.
    Firstly, global variables are defined:
    - full path to the "imagesort.py"
    - block size for getting checksum (SHA256)
    Secondly, main arguments are defined from the command line by using argparse module:
        parse_main_args() returns argparse.Namespace object
        get_global_variables(CLI_data) returns:
            mode ('dryrun', 'copy', 'move', 'sort')
            initial folder (full path)
            target folder (full path)

    After thees blocks are executed next functions:
    - get_files_and_attributes_from_initial_dir()
    - get_folder_names_for_sorted_files(initial_files_attributes)

    For 'dryrun' mode is executed:
        generate_html_report()
    For 'copy' mode are executed next functions:
        copy_sorted_files()
        integrity_validation()
    For 'move' mode are executed next functions:
        copy_sorted_files()
        integrity_validation()
        delete_folder()
    For 'sort' mode are executed next functions:
        create_temporary_folder()
        copy_sorted_files()
        integrity_validation()
        delete_folder()
        rename_temp_folder_to_initial()
    """

    get_global_variables(CLI_data)
    initial_files_attributes, initial_dir_structure = get_files_and_attributes_from_initial_dir()
    get_folder_names_for_sorted_files(initial_files_attributes)

    if MODE == 'dryrun':
        generate_html_report(initial_files_attributes, initial_dir_structure)
    elif MODE == 'copy':
        process_mode_copy(initial_files_attributes)
    elif MODE == 'move':
        process_mode_move(initial_files_attributes)
    else:  # MODE == 'sort':
        process_mode_sort(initial_files_attributes)


# mode function definitions:
def process_mode_copy(ini_files_attributes):
    copy_sorted_files(ini_files_attributes)
    integrity_validation(ini_files_attributes)


def process_mode_move(ini_files_attributes):
    copy_sorted_files(ini_files_attributes)
    integrity_validation(ini_files_attributes)
    delete_folder(INITIAL_FOLDER)


def process_mode_sort(ini_files_attributes):
    copy_sorted_files(ini_files_attributes)
    integrity_validation(ini_files_attributes)
    delete_folder(INITIAL_FOLDER)
    rename_temp_folder_to_initial()


if __name__ == '__main__':
    CLI_data = parse_main_args()
    main(CLI_data)
