from chameleon import PageTemplateLoader
from PIL import Image
import argparse
import copy
import hashlib
import os
import pathlib
import shutil
import stat
import sys


def create_directories_structure(initial_folder: str) -> dict and list:
    """
    Checks the initial folder for existing. Gets structure of the initial folder as dictionary and list:
    ini_structure = {'full_path_to_folder_1': ['file_name_1', 'file_name_2', __], __}
    all_files = ['full_path_to_file_1', 'full_path_to_the_file_2', __]

    Gets the structure of target folder, resolutions are defined for images
    and status 'Not images' is given for other files.
    Output dictionaries are:
    files_attributes = {'full_path_to_file_1': ['folder_name'*, 'file_name_1'], __}
    dir_structure = {'folder_name'*: ['file_name_1', 'file_name_2', __], __}
    * were 'folder_name' is resolution (for example, '1920x1080') or 'Not images'
    """
    if not os.path.isdir(initial_folder):
        sys.exit(f"Error! Entered initial folder doesn't exist: {initial_folder}")

    os.chdir(initial_folder)
    all_files, ini_structure = get_dirs_and_files(initial_folder)

    files_attributes = dict()

    for single_file in all_files:
        try:
            w, h = Image.open(single_file).size
        except:
            files_attributes[single_file] = ['Not images', os.path.basename(single_file)]
        else:
            files_attributes[single_file] = [f'{w}x{h}', os.path.basename(single_file)]

    dir_structure = dict()
    dirs_set = set([folder_name[0]
                    for folder_name in files_attributes.values()])

    for folder_name in dirs_set:
        temp_list = list()
        for attributes in files_attributes.values():
            if attributes[0] == folder_name:
                temp_list.append(attributes[1])
            dir_structure[folder_name] = temp_list

    if len(dir_structure.keys()) == 1 and 'Not images' in dir_structure.keys():
        sys.exit('Error! There are no images to sort in the initial folder: {initial_folder}')

    if 'Not images' in dir_structure.keys():
        print(f"Information! There is(are) file(s) in the initial folder for which resolution couldn't "
              f'be determined so directory "Not images" will be created.\n')

    return ini_structure, files_attributes, dir_structure


def process_mode_dry_run(script_path: str, initial_folder: str,
                         ini_structure: dict, dir_structure: dict) -> 'html report':
    """Generates the html report which will show previous structure and suggested reorganization.
    initial_structure = {'path_to_folder_1': ['file_name_1', 'file_name_2', __], __}
    sorted_output_files = {'folder_name'*: ['file_name_1', 'file_name_2', __], __}
    * were 'folder_name' is resolution (for example, '1920x1080') or 'Not images'
    """
    report_name = check_dryrun_report_name(initial_folder)

    initial_structure = dict()
    for path in ini_structure.keys():
        initial_structure[f"""{path.replace(initial_folder, '"root dir"')}"""] = ini_structure[path]

    sorted_output_files = dict()
    for folder in sorted(dir_structure):
        sorted_output_files[folder] = sorted(dir_structure[folder])

    try:
        templates = PageTemplateLoader(os.path.join(script_path, "templates"))
        tmpl = templates['report_temp.pt']
        result_html = tmpl(title=report_name, input_folder=initial_folder,
                           initial_dir=initial_structure, structure=sorted_output_files)
    except Exception as err:
        print(f'The HTML report generation caused the exception:\n\t{err}')
    else:
        report = open(os.path.join(initial_folder, report_name), 'w')
        report.write(result_html)
        report.close()
        print(f'The file "{report_name}" was created in the directory "{initial_folder}"')


def sort_images(target_folder: str, files_attributes: dict) -> None:
    """Creates new folders (Width x Height) or 'Not images' and copies images from initial folder to the new,
    if folder already exists files will be added there, if there is file with the same name,
    then the new file will be renamed, "({num})" will be added to its name (for example, "wallpaper(3)").
    """
    os.chdir(target_folder)
    temp_dict = copy.deepcopy(files_attributes)
    for full_path, attributes in temp_dict.items():
        check_dir_before_making(attributes[0])
        checked_file_name = check_file_before_coping(full_path, target_folder, files_attributes)
        shutil.copy(full_path, os.path.join(target_folder, attributes[0], checked_file_name))


def validate_checksums(target_folder: str, files_attributes: dict) -> 'terminal report':
    """Compares checksums of the files from initial folder and copied files after reorganization.
    ini_files_checksums = ['checksum_of_file_1', 'checksum_of_file_2', __]  # for all files from initial_folder
    res_files_checksums = ['checksum_of_file_1', 'checksum_of_file_2', __]  # for copied files from target_folder
    """
    ini_files_checksums = list()
    res_files_checksums = list()
    for file_path, attributes in files_attributes.items():
        ini_files_checksums.append(calculate_checksums(file_path))
        res_files_checksums.append(calculate_checksums(os.path.join(target_folder, attributes[0], attributes[1])))

    ini_files_checksums.sort()
    res_files_checksums.sort()

    if ini_files_checksums == res_files_checksums:
        print('Checksum verification completed successfully')
    else:
        sys.exit('Attention! Checksum verification completed with an error. Deleting of the initial files canceled.')

    total_ini_files = len(files_attributes.keys())
    total_images = 0
    total_not_images = 0
    for attributes in files_attributes.values():
        if attributes[0] == 'Not images':
            total_not_images += 1
        else:
            total_images += 1

    print(f'\nImageSort report:\nFrom initial folder was(re) sorted successfully {total_ini_files} files:\n'
          f'Images{total_images:>20}\n'
          f'Not images{total_not_images:>16}')


def remove_initial_files(script_path: str, initial_folder: str) -> None:
    """Removes all files from given folder even with attribute "readonly"."""
    os.chdir(script_path)
    try:
        shutil.rmtree(initial_folder, onerror=delete_readonly)
    except PermissionError as err:
        sys.exit(f'Attention! Deleting of the initial folder completed with an error: {err}'
                 f'\nPlease close the folder in explorer or another application and try again')
    except Exception as err:
        sys.exit(f'Attention! Deleting of the initial folder completed with an error: {err}')


def create_temp_folder(initial_folder: str) -> str:
    """Creates temporary folder for coping sorted files."""
    only_path = os.path.dirname(initial_folder)
    num = 1
    while os.path.isdir(f'{only_path}-temp{num}'):
        num += 1
    temp_folder = f'{initial_folder}-temp{num}'
    os.mkdir(temp_folder)
    return temp_folder


def check_dryrun_report_name(initial_folder: str) -> str:
    """Checks initial folder for existing file 'DryRun report.html', if file already exists then
    the report will be renamed before generating, "({num})" will be added to its name."""
    if os.path.isfile(os.path.join(initial_folder, 'DryRun report.html')):
        num = 1
        while os.path.isfile(os.path.join(initial_folder, f'DryRun report({num}).html')):
            num += 1
        return f'DryRun report({num}).html'
    else:
        return 'DryRun report.html'


def rename_target_folder(script_path: str, initial_folder: str, target_folder: str) -> None:
    """Renames temporary target folder into initial folder."""
    os.chdir(script_path)
    os.rename(target_folder, initial_folder)


def delete_readonly(action, name, exc) -> None:
    """Deletes files with attribute "readonly"."""
    os.chmod(name, stat.S_IWRITE)
    os.remove(name)


def calculate_checksums(file_path: str) -> str:
    """Returns checksum of the given file."""
    block_size = 65536
    sha = hashlib.sha256()
    with open(file_path, 'rb') as CF:
        file_buffer = CF.read(block_size)
        while len(file_buffer) > 0:
            sha.update(file_buffer)
            file_buffer = CF.read(block_size)
    return sha.hexdigest()


def check_file_before_coping(file_to_copy: str, target_folder: str, input_dict: dict) -> str:
    """Checks folder for existing file with given name,
    if file already exists then the new file will be renamed before coping:
    "({num})" will be added to its name (for example, "wallpaper(3)").
    """
    dir_name = input_dict[file_to_copy][0]
    file_name = input_dict[file_to_copy][1]
    existing_file = os.path.join(target_folder, dir_name, file_name)
    only_name, only_type = os.path.splitext(file_name)
    if os.path.isfile(existing_file):
        num = 1
        while os.path.isfile(os.path.join(target_folder, dir_name, f'{only_name}({num}){only_type}')):
            num += 1
        input_dict[file_to_copy][1] = f'{only_name}({num}){only_type}'
        return f'{only_name}({num}){only_type}'
    else:
        return file_name


def get_dirs_and_files(input_folder: str) -> dict and list:
    """Gets full structure of the given path.
    dir_structure = {'full_path_to_the_folder_1': ['file_name_1', 'file_name_2', ], }
    """
    paths_structure = list()
    dir_structure = dict()
    for dirpath, dirs, files in os.walk(f'{input_folder}'):
        temp_list = list()
        for file_name in os.listdir(dirpath):
            if not os.path.isdir(os.path.join(dirpath, file_name)):
                paths_structure.append(os.path.join(dirpath, file_name))
                temp_list.append(file_name)
            dir_structure[dirpath] = temp_list

    if not paths_structure:
        sys.exit(f'Error! There are no files in the initial folder: {input_folder}')
    else:
        return paths_structure, delete_empty_folders(dir_structure)


def delete_empty_folders(input_dict: dict) -> dict:
    """Deletes in inputted dictionary paths for empty folders."""
    dict_copy = copy.deepcopy(input_dict)
    for folder_name in dict_copy.keys():
        if not input_dict[folder_name]:
            del input_dict[folder_name]
    return input_dict


def check_dir_before_making(input_path: str) -> None:
    """Checks if the given directory exists, otherwise creates a new one."""
    if not os.path.isdir(input_path):
        os.mkdir(input_path)


def main():
    """This is the main function of the script.
    Firstly, full path to the "imagesort.py" is given.
    Secondly, main arguments are defined from the command line by using argparse module:
        mode ('dryrun', 'copy', 'move', 'sort')
        initial folder (full path)
        target folder (full path)
    After thees blocks function 'create_directories_structure' is executed for all types of the mode

    For 'dryrun' is executed:
        process_mode_dry_run
    For 'copy' are executed next functions:
        sort_images
        validate_checksums
    For 'move' are executed next functions:
        sort_images
        validate_checksums
        remove_initial_files
    For 'sort' are executed next functions:
        create_temp_folder
        sort_images
        validate_checksums
        remove_initial_files
        rename_target_folder

    Extra functions are also used:
        calculate_checksums
        check_dryrun_report_name
        check_file_before_coping
        check_dir_before_making
        delete_empty_folders
        delete_readonly
        get_dirs_and_files
    """
    script_path = os.path.abspath(os.path.dirname(__file__))  # path to the imagesort.py

    parser = argparse.ArgumentParser(prog='ImageSort',
                                     usage='imagesort.py [-h] [mode, initial_folder, target_folder (optional)]',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description='''
    %(prog)s sorts images by their resolutions.
    Reference information about application:
      dryrun "path" = app generates html-report with sorted files structure from inputted folder
      copy "path_1" "path_2" = app sorts files from "directory_1" into "directory_2"
      move "path_1" "path_2" = app sorts and moves files from "directory_1" into "directory_2"
      sort "path" = app sorts files into the inputted folder and deletes the initial files''')
    parser.add_argument('mode', type=str, help='Choose the mode',
                        choices=['dryrun', 'copy', 'move', 'sort'])
    parser.add_argument('initial_folder', type=pathlib.Path, help='Input the initial folder', nargs='?', default=None)
    parser.add_argument('target_folder', type=pathlib.Path, help='Input the target folder', nargs='?', default=None)

    input_args = parser.parse_args()
    initial_folder = str(input_args.initial_folder)
    target_folder = str(input_args.target_folder)
    mode = input_args.mode

    ini_structure, files_attributes, dir_structure = create_directories_structure(initial_folder)

    if mode == 'dryrun':
        process_mode_dry_run(script_path, initial_folder, ini_structure, dir_structure)
    elif mode == 'copy':
        process_mode_copy(target_folder, files_attributes)
    elif mode == 'move':
        process_mode_move(script_path, initial_folder, target_folder, files_attributes)
    else:  # elif mode == 'sort':
        process_mode_sort(script_path, initial_folder, files_attributes)


# mode function definitions:
def process_mode_copy(target_folder, files_attributes):
    check_dir_before_making(target_folder)
    sort_images(target_folder, files_attributes)
    validate_checksums(target_folder, files_attributes)


def process_mode_move(script_path, initial_folder, target_folder, files_attributes):
    check_dir_before_making(target_folder)
    sort_images(target_folder, files_attributes)
    validate_checksums(target_folder, files_attributes)
    remove_initial_files(script_path, initial_folder)


def process_mode_sort(script_path, initial_folder, files_attributes):
    target_folder = create_temp_folder(initial_folder)
    sort_images(target_folder, files_attributes)
    validate_checksums(target_folder, files_attributes)
    remove_initial_files(script_path, initial_folder)
    rename_target_folder(script_path, initial_folder, target_folder)


if __name__ == '__main__':
    main()
