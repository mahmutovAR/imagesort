from chameleon import PageTemplateLoader
from PIL import Image
import argparse
import copy
import hashlib
import os
import pathlib
import stat
import shutil
import sys


def parse_arguments(image_types: list, initial_folder: str) -> 'main arguments':
    """Checks the initial folder for existing and the presence of images there, gets dictionaries with structure of
    the initial folder, images and other files from initial folder.
    all_files = {'full_path_to_the_folder_1': ['file_name_1', 'file_name_2', ..], ..}
    images = {'full_path_to_the_folder_1': ['image_name_1', 'image_name_2', ..], ..}
    not_images = {'full_path_to_the_folder_1': ['not_image_name_1', 'not_image_name_2', ..], ..}
    """

    if not os.path.isdir(initial_folder):
        sys.exit(f"Error! Entered initial folder doesn't exist: {initial_folder}")

    all_files = get_dirs_and_files(initial_folder)
    images = {}
    not_images = {}

    if not all_files:
        sys.exit(f'Error! There are no files in the initial folder: {initial_folder}')

    for dir_path in all_files.keys():
        images[dir_path] = [file
                            for file in all_files[dir_path]
                            for image_format in image_types
                            if os.path.splitext(file.lower())[1] == image_format]

    for dir_path in all_files.keys():
        not_images[dir_path] = [file
                                for file in all_files[dir_path]
                                if file not in images[dir_path]]

    images = delete_empty_folders(images)
    not_images = delete_empty_folders(not_images)

    if not images:
        sys.exit(f'Error! There are no images to sort in the initial folder: {initial_folder}')

    if not_images is not None:
        print(f'Information! There is(are) "not images" file(s) in the initial folder '
              f'so directory "Other files" will be created.')
    return all_files, images, not_images


def create_directories_structure(initial_folder: str, images: dict) -> 'dict and bool':
    """Gets two dictionaries, one with resolutions of each image,
    and second with images for which resolution couldn't be determined.
    images_attributes = {'full_path_to_the_image_1': ['image_name', 'resolution', 'checksum'], ..}
    images_by_resolutions = {'resolution_1': ['full_path_to_the_image_1', 'full_path_to_the_image_2', ..], ..}
    not_sized_files = {'full_path_to_the_folder_1': ['not_sized_image_name_1', 'not_sized_image_name_2', ..], ..}
    """
    os.chdir(initial_folder)
    not_sized_files = {}
    images_attributes = {}
    for folder_name in images.keys():
        for image_name in images[folder_name]:
            try:
                w, h = Image.open(f'{folder_name}/{image_name}').size
            except:
                if folder_name in not_sized_files:
                    not_sized_files_list = not_sized_files[folder_name]
                    not_sized_files_list.append(image_name)
                    not_sized_files[folder_name] = not_sized_files_list
                else:
                    not_sized_files[f'{folder_name}'] = [image_name]
            else:
                images_attributes[f'{folder_name}/{image_name}'] = [image_name,
                                                                    f'{w}x{h}',
                                                                    calculate_checksums(f'{folder_name}/{image_name}')]

    images_by_resolutions = {resolution: [k
                                          for k, v in images_attributes.items()
                                          if v[1] == resolution]
                             for resolution in set([attributes[1]
                                                    for attributes in images_attributes.values()])}

    if not_sized_files is not None:
        print(f"Information! There is(are) file(s) in the initial folder for which resolution couldn't "
              f'be determined so directory "Error files" will be created.\n')
    return images_attributes, images_by_resolutions, not_sized_files


def generate_html_report(script_path: str, initial_folder: str, all_files: dict, images_attributes: dict,
                         images_by_resolutions: dict, not_images: dict, not_sized_files: dict) -> 'html report':
    """Generates the html report which will show previous structure and suggested reorganization.
    initial_structure = {'path_to_the_folder_1': ['file_name_1', 'file_name_2', ..], ..}
    output_files = {'resolution_1': ['image_name_1', 'image_name_2', ..], ..}
    sorted_output_files = output_files with sorted 'resolutions'
    """
    report_name = 'DryRun report'

    initial_structure = {f'{path.replace(initial_folder,"..")}': all_files[path]
                         for path in all_files.keys()}

    output_files = {f'{resolution}': [images_attributes[image][0]
                                       for image in images_by_resolutions[resolution]]
                    for resolution in images_by_resolutions.keys()}

    if not_images is not None:
        not_images_list = []
        for key in not_images:
            not_images_list += not_images[key]
        output_files['Other files/'] = not_images_list

    if not_sized_files is not None:
        not_sized_files_list = []
        for key in not_sized_files:
            not_sized_files_list += not_sized_files[key]
        output_files['Error files/'] = not_sized_files_list

    sorted_output_files = {k: sorted(output_files[k])
                           for k in sorted(output_files)}

    try:
        templates = PageTemplateLoader(os.path.join(script_path, "templates"))
        tmpl = templates['report_temp.pt']
        result_html = tmpl(title=report_name, input_folder=initial_folder,
                           initial_dir=initial_structure, structure=sorted_output_files)
    except Exception as err:
        print(f'The building of the HTML report caused the exception: {err}'
              f'\nPlease check the integrity of the source files')
    else:
        report = open(f'{initial_folder}/{report_name}.html', 'w')
        report.write(result_html)
        report.close()
        print(f'The file "{report_name}.html" was created in the directory "{initial_folder}"')


def sort_images(target_folder: str, images_attributes: dict, images_by_resolutions: dict) -> dict:
    """Creates new folders (Width x Height) and copies images from initial folder to the new,
    if folder already exists files will be added there, if there is file with the same name,
    then the new file will be renamed, "!{num}-" will be added to its name.
    exception_dict = {'full_path_to_the_image_1' : 'changed_name_of_the_image_1', ..}
    """
    exception_dict = {}
    os.chdir(target_folder)
    for resolution in images_by_resolutions.keys():
        if not os.path.isdir(resolution):
            os.mkdir(resolution)
        for image_path in images_by_resolutions[resolution]:
            checked_file_name = check_file_before_coping(target_folder, resolution, image_path,
                                                         images_attributes[image_path][0], exception_dict)
            shutil.copy(f'{image_path}', f'{target_folder}/{resolution}/{checked_file_name}')
    return exception_dict


def create_named_folder_and_copy_files(target_folder: str, dir_name: str,
                                       input_dict: dict, exception_dict: dict) -> None:
    """Creates folder for other/error files and copy them there, if folder already exists files will be added there,
    if there is file with the same name, then the new file will be renamed, "!{num}-" will be added to its name."""
    os.chdir(target_folder)
    for path_to_file in input_dict.keys():
        if not os.path.isdir(f'{dir_name}'):
            os.mkdir(f'{dir_name}')
        for file_name in input_dict[path_to_file]:
            checked_file_name = check_file_before_coping(target_folder, dir_name, f'{path_to_file}/{file_name}',
                                                         file_name, exception_dict)
            shutil.copy(f'{path_to_file}/{file_name}', f"{target_folder}/{dir_name}/{checked_file_name}")


def validate_checksums(target_folder: str, all_files: dict, images_attributes: dict, images_by_resolutions: dict,
                       not_images: dict, not_sized_files: dict, exception_dict: dict) -> None:
    """"Compares checksums of the files from initial folder and copied files after reorganization.
    ini_files_checksums = ['checksum_of_the_file_1', 'checksum_of_the_file_2', ..]  # for all files from initial_folder
    res_files_checksums = ['checksum_of_the_file_1', 'checksum_of_the_file_2', ..]  # for all files from target_folder
    """
    ini_files_checksums = [calculate_checksums(f'{file_path}/{file_name}')
                           for file_path in all_files.keys()
                           for file_name in all_files[file_path]]

    res_files_checksums = []
    for folder_name in images_by_resolutions.keys():
        for file_name in images_by_resolutions[folder_name]:
            if file_name in exception_dict.keys():
                checked_file_name = exception_dict[file_name]
            else:
                checked_file_name = images_attributes[file_name][0]
            res_files_checksums.append(calculate_checksums(f'{target_folder}/{folder_name}/{checked_file_name}'))

    if not_images is not None:
        res_files_checksums.extend(calculate_checksum_from_named_folder(target_folder, 'Other files',
                                                                        not_images, exception_dict))

    if not_sized_files is not None:
        res_files_checksums.extend(calculate_checksum_from_named_folder(target_folder, 'Error files',
                                                                        not_sized_files, exception_dict))

    if ini_files_checksums.sort() == res_files_checksums.sort():
        print('Checksum verification completed successfully')
    else:
        sys.exit('Attention! Checksum verification completed with an error. Deleting of the initial files canceled.')

    total_not_images = 0
    for k in not_images.keys():
        total_not_images += len(not_images[k])
    total_not_sized_files = 0
    for k in not_sized_files.keys():
        total_not_sized_files += len(not_sized_files[k])
    total_all_files = 0
    for k in all_files.keys():
        total_all_files += len(all_files[k])
    print(f'\nImageSort report:\nFrom initial folder was(re) sorted successfully {total_all_files} files:\n'
          f'Images{len(images_attributes.keys()):>20}\n'
          f'Not images{total_not_images:>16}\n'
          f'Not sized images{total_not_sized_files:>10}')


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
    """Creates temp folder for coping sorted files."""
    if initial_folder.endswith('/'):
        while initial_folder.endswith('/'):
            initial_folder = initial_folder[:-1]
    num = 1
    while os.path.isdir(f'{initial_folder}-temp{num}'):
        num += 1
    temp_folder = f'{initial_folder}-temp{num}'
    os.mkdir(temp_folder)
    return temp_folder


def rename_target_folder(script_path: str, initial_folder: str, target_folder: str) -> None:
    """Renames temp target folder into initial folder."""
    os.chdir(script_path)
    os.rename(target_folder, initial_folder)


def delete_readonly(action, name, exc) -> None:
    """Deletes files with attribute "readonly"."""
    os.chmod(name, stat.S_IWRITE)
    os.remove(name)


def calculate_checksums(arg_file: str) -> str:
    """Returns checksum of the given file."""
    block_size = 65536
    sha = hashlib.sha256()
    with open(arg_file, 'rb') as CF:
        file_buffer = CF.read(block_size)
        while len(file_buffer) > 0:
            sha.update(file_buffer)
            file_buffer = CF.read(block_size)
    return sha.hexdigest()


def check_file_before_coping(target_folder: str, dir_name: str, file_to_copy: str,
                             file_name: str, exception_dict: dict) -> str:
    """Checks folder for existing file with given name, if file already exists then
    the new file will be renamed before coping, "!{num}-" will be added to its name.
    exception_dict = {'full_path_to_the_image_1' : 'changed_name_of_the_image_1', ..}"""
    existing_file = f'{target_folder}/{dir_name}/{file_name}'
    if os.path.isfile(existing_file):
        num = 1
        while os.path.isfile(f'{target_folder}/{dir_name}/!{num}-{file_name}'):
            num += 1
        exception_dict[file_to_copy] = f'!{num}-{file_name}'
        return f'!{num}-{file_name}'
    else:
        return file_name


def get_dirs_and_files(folder: str) -> dict:
    """Gets full structure of the given path.
    dir_structure = {'full_path_to_the_folder_1': ['file_name_1', 'file_name_2', ..], ..}
    """
    dir_structure = {}
    for dirpath, dirs, files in os.walk(f'{folder}'):
        dir_structure[dirpath] = [file_name
                                  for file_name in os.listdir(dirpath)
                                  if not os.path.isdir(f'{dirpath}/{file_name}')]
    dir_structure = delete_empty_folders(dir_structure)
    return dir_structure


def delete_empty_folders(input_dict: dict) -> dict:
    """Deletes paths for empty folders from given dictionary."""
    dict_copy = copy.deepcopy(input_dict)
    for folder_name in dict_copy.keys():
        if not input_dict[folder_name]:
            del input_dict[folder_name]
    return input_dict


def calculate_checksum_from_named_folder(target_folder: str, dir_name: str,
                                         input_dict: dict, exception_dict: dict) -> list:
    """Returns checksum of the files from given folder.
    named_folder_checksums = ['checksum_of_the_file_1', 'checksum_of_the_file_2', ..]
    """
    named_folder_checksums = []
    for folder_name in input_dict.keys():
        for file_name in input_dict[folder_name]:
            if f'{folder_name}/{file_name}' in exception_dict.keys():
                checked_file_name = exception_dict[f'{folder_name}/{file_name}']
            else:
                checked_file_name = file_name
            named_folder_checksums.append(calculate_checksums(f'{target_folder}/{dir_name}/{checked_file_name}'))
    return named_folder_checksums


def main():
    """This is the main function of the script.
    Firstly, are given two constant arguments:
        full path to the "imagesort.py"
        list of image types for sorting
    Secondly, main arguments obtained from the command line by using argparse module:
        mode ('dryrun', 'copy', 'move', 'sort')
        initial folder (full path)
        target folder (full path)
    After thees blocks two functions are executed for all types of the mode:
        parse_arguments
        create_directories_structure
    For 'dryrun' is executed:
        generate_html_report
    For 'copy' are executed next functions:
    *    sort_images
    *    create_named_folder_and_copy_files (if necessary)
    *    validate_checksums
    For 'move' are executed next functions:
    *    sort_images
    *    create_named_folder_and_copy_files (if necessary)
    *    validate_checksums
        remove_initial_files
    For 'sort' are executed next functions:
        create_temp_folder
    *    sort_images
    *    create_named_folder_and_copy_files (if necessary)
    *    validate_checksums
        remove_initial_files
        rename_target_folder

    * marked functions are same for all modes,so "if-else" structure was used to prevent code repetition
    after execution of the functions "parse_arguments" and "create_directories_structure":

    if 'dryrun':
        generate_html_report()
    else:
        if 'sort':
            create_temp_folder()
            additional argument 'rename' is given
        if 'copy' or 'move' or 'rename':
            sort_images()
            create_named_folder_and_copy_files()
            validate_checksums()
            if 'move' or 'rename':
                remove_initial_files()
                if 'rename':
                    rename_target_folder()

    Extra functions are also used:
        delete_readonly
        calculate_checksums
        check_file_before_coping
        get_dirs_and_files
        delete_empty_folders
        calculate_checksum_from_named_folder
    """
    script_path = os.path.abspath(os.path.dirname(__file__))  # path to the imagesort.py
    image_types = ['.bmp', '.gif', '.png', '.jpg', '.jpeg', '.tiff', '.raw']  # image types

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

    all_files, images, not_images = parse_arguments(image_types, initial_folder)
    images_attributes, images_by_resolutions, not_sized_files = create_directories_structure(
        initial_folder, images)

    if mode == 'dryrun':  # dry run mode for files in the initial folder
        generate_html_report(script_path, initial_folder, all_files, images_attributes, images_by_resolutions,
                             not_images, not_sized_files)
    else:
        if mode == 'sort':  # creating of the temporary folder
            target_folder = create_temp_folder(initial_folder)
            mode = 'rename'  # this additional argument is needed for using "if-else" structure

        if mode in ['copy', 'move', 'rename']:  # common for 'copy'/'move'/'sort' modes
            if not os.path.isdir(f'{target_folder}'):
                os.mkdir(f'{target_folder}')
                print(f'Information! Target folder "{target_folder}" was created')

            exception_dict = sort_images(target_folder, images_attributes, images_by_resolutions)
            if not_images is not None:
                create_named_folder_and_copy_files(target_folder, 'Other files', not_images, exception_dict)
            if not_sized_files is not None:
                create_named_folder_and_copy_files(target_folder, 'Error files', not_sized_files, exception_dict)
            validate_checksums(target_folder, all_files, images_attributes, images_by_resolutions,
                               not_images, not_sized_files, exception_dict)

            if mode in ['move', 'rename']:  # common for 'move' or 'sort' modes
                remove_initial_files(script_path, initial_folder)  # remove all files from the initial folder

                if mode == 'rename':  # only for 'sort' mode
                    rename_target_folder(script_path, initial_folder, target_folder)


if __name__ == '__main__':
    main()
