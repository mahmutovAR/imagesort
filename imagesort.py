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


def parse_arguments(image_types: list, initial_folder: str) -> dict or list or None:
    """Checks the initial folder for existing and the presence of images there, gets dictionaries with structure of
    the initial folder, images and other files from initial folder.
    all_files = {'full_path_to_folder_1': ['file_name_1', 'file_name_2', __], __}
    images = ['full_path_to_image_1', 'full_path_to_the_image_2', __]
    not_images = {'full_path_to_not_image_1': ['not_image_name_1'], __}
    """

    if not os.path.isdir(initial_folder):
        sys.exit(f"Error! Entered initial folder doesn't exist: {initial_folder}")

    all_files = get_dirs_and_files(initial_folder)

    if not all_files:
        sys.exit(f'Error! There are no files in the initial folder: {initial_folder}')

    images = list()
    not_images = dict()
    for dir_path in all_files.keys():
        for file_name in all_files[dir_path]:
            if os.path.splitext(file_name.lower())[1] in image_types:
                images.append(os.path.join(dir_path, file_name))
            else:
                not_images[os.path.join(dir_path, file_name)] = [file_name]

    if not images:
        sys.exit(f'Error! There are no images to sort in the initial folder: {initial_folder}')

    if not_images:
        print(f'Information! There is(are) "not images" file(s) in the initial folder '
              f'so directory "Other files" will be created.')
    return all_files, images, not_images


def create_directories_structure(initial_folder: str, images: list) -> dict or None:
    """Gets two dictionaries, one with resolutions of each image,
    and second with images for which resolution couldn't be determined.
    images_attributes = {'full_path_to_image_1': ['image_name_1', 'resolution'], __}
    images_by_resolutions = {'resolution_1': ['full_path_to_image_1', 'full_path_to_image_2', __], __}
    not_sized_files = {'full_path_to_not_sized_file_name_1': ['not_sized_file_name_1'], __}
    """
    os.chdir(initial_folder)
    images_attributes = dict()
    not_sized_files = dict()
    for single_image in images:
        try:
            w, h = Image.open(single_image).size
        except:
            not_sized_files[single_image] = [os.path.basename(single_image)]
        else:
            images_attributes[single_image] = [os.path.basename(single_image),
                                               f'{w}x{h}']

    images_by_resolutions = {resolution: [k
                                          for k, v in images_attributes.items()
                                          if v[1] == resolution]
                             for resolution in set([attributes[1]
                                                    for attributes in images_attributes.values()])}

    if not_sized_files:
        print(f"Information! There is(are) file(s) in the initial folder for which resolution couldn't "
              f'be determined so directory "Error files" will be created.\n')
    return images_attributes, images_by_resolutions, not_sized_files


def generate_html_report(script_path: str, initial_folder: str, all_files: dict, images_attributes: dict,
                         images_by_resolutions: dict, not_images: dict, not_sized_files: dict) -> 'html report':
    """Generates the html report which will show previous structure and suggested reorganization.
    initial_structure = {'path_to_folder_1': ['file_name_1', 'file_name_2', __], __}
    output_files = {'resolution_1': ['image_name_1', 'image_name_2', __], __}
    sorted_output_files = output_files sorted by 'resolutions'
    """
    report_name = 'DryRun report'

    initial_structure = {f'{path.replace(initial_folder,"<ROOT>")}': all_files[path]
                         for path in all_files.keys()}

    output_files = {f'{resolution}': [images_attributes[image][0]
                                      for image in images_by_resolutions[resolution]]
                    for resolution in images_by_resolutions.keys()}

    if not_images:
        output_files['Other files'] = not_images
    if not_sized_files:
        output_files['Error files'] = not_sized_files

    sorted_output_files = {k: sorted(output_files[k])
                           for k in sorted(output_files)}

    try:
        templates = PageTemplateLoader(os.path.join(script_path, "templates"))
        tmpl = templates['report_temp.pt']
        result_html = tmpl(title=report_name, input_folder=initial_folder,
                           initial_dir=initial_structure, structure=sorted_output_files)
    except Exception as err:
        print(f'The HTML report generation caused the exception:\n\t{err}')
    else:
        report = open(os.path.join(initial_folder, report_name) + '.html', 'w')
        report.write(result_html)
        report.close()
        print(f'The file "{report_name}.html" was created in the directory "{initial_folder}"')


def sort_images(target_folder: str, images_by_resolutions: dict, images_attributes: dict) -> None:
    """Creates new folders (Width x Height) and copies images from initial folder to the new,
    if folder already exists files will be added there, if there is file with the same name,
    then the new file will be renamed, "({num})" will be added to its name.
    """
    os.chdir(target_folder)
    for resolution in images_by_resolutions.keys():
        if not os.path.isdir(resolution):
            os.mkdir(resolution)
        for image_path in images_by_resolutions[resolution]:
            checked_file_name = check_file_before_coping(target_folder, resolution, image_path,
                                                         images_attributes)
            shutil.copy(f'{image_path}', os.path.join(target_folder, resolution, checked_file_name))


def create_named_folder_and_copy_files(target_folder: str, dir_name: str,
                                       input_dict: dict) -> None:
    """Creates folder for other or error files and copy them there, if folder already exists files will be added there,
    if there is file with the same name, then the new file will be renamed, "({num})" will be added to its name."""
    os.chdir(target_folder)
    dict_copy = copy.deepcopy(input_dict)
    for path_to_file in dict_copy.keys():
        if not os.path.isdir(f'{dir_name}'):
            os.mkdir(f'{dir_name}')
        checked_file_name = check_file_before_coping(target_folder, dir_name, path_to_file, input_dict)
        shutil.copy(path_to_file, os.path.join(target_folder, dir_name, checked_file_name))


def validate_checksums(target_folder: str, all_files: dict, images_attributes: dict,
                       images_by_resolutions: dict, not_images: dict, not_sized_files: dict) -> 'terminal report':
    """Compares checksums of the files from initial folder and copied files after reorganization.
    ini_files_checksums = ['checksum_of_file_1', 'checksum_of_file_2', __]  # for all files from initial_folder
    res_files_checksums = ['checksum_of_file_1', 'checksum_of_file_2', __]  # for copied files from target_folder
    """
    ini_files_checksums = [calculate_checksums(os.path.join(file_path, file_name))
                           for file_path in all_files.keys()
                           for file_name in all_files[file_path]]

    res_files_checksums = list()
    for resolution in images_by_resolutions.keys():
        for image_name in images_by_resolutions[resolution]:
            res_files_checksums.append(calculate_checksums(
                os.path.join(target_folder, resolution, images_attributes[image_name][0])))

    if not_images:
        for single_not_images in not_images:
            res_files_checksums.extend(calculate_checksums(
                os.path.join(target_folder, 'Other files', not_images[single_not_images][0])))

    if not_sized_files:
        for single_not_sized_files in not_sized_files:
            res_files_checksums.extend(calculate_checksums(
                os.path.join(target_folder, 'Error files', not_sized_files[single_not_sized_files][0])))

    if ini_files_checksums.sort() == res_files_checksums.sort():
        print('Checksum verification completed successfully')
    else:
        sys.exit('Attention! Checksum verification completed with an error. Deleting of the initial files canceled.')

    total_ini_files = 0
    for k in all_files.keys():
        total_ini_files += len(all_files[k])
    total_images = len(images_attributes.keys())
    total_not_images = len(not_images.keys())
    total_not_sized_files = len(not_sized_files.keys())

    print(f'\nImageSort report:\nFrom initial folder was(re) sorted successfully {total_ini_files} files:\n'
          f'Images{total_images:>20}\n'
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
    """Creates temporary folder for coping sorted files."""
    only_path = os.path.dirname(initial_folder)
    num = 1
    while os.path.isdir(f'{only_path}-temp{num}'):
        num += 1
    temp_folder = f'{initial_folder}-temp{num}'
    os.mkdir(temp_folder)
    return temp_folder


def rename_target_folder(script_path: str, initial_folder: str, target_folder: str) -> None:
    """Renames temporary target folder into initial folder."""
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
                             input_dict: dict) -> str:
    """Checks folder for existing file with given name, if file already exists then
    the new file will be renamed before coping, "({num})" will be added to its name.
    """
    file_name = os.path.basename(file_to_copy)
    existing_file = os.path.join(target_folder, dir_name, file_name)
    only_name, only_type = os.path.splitext(file_name)
    if os.path.isfile(existing_file):
        num = 1
        while os.path.isfile(os.path.join(target_folder, dir_name, f'{only_name}({num}){only_type}')):
            num += 1
        input_dict[file_to_copy].insert(0, f'{only_name}({num}){only_type}')
        return f'{only_name}({num}){only_type}'
    else:
        return file_name


def get_dirs_and_files(folder: str) -> dict:
    """Gets full structure of the given path.
    dir_structure = {'full_path_to_the_folder_1': ['file_name_1', 'file_name_2', ], }
    """
    dir_structure = dict()
    for dirpath, dirs, files in os.walk(f'{folder}'):
        dir_structure[dirpath] = [file_name
                                  for file_name in os.listdir(dirpath)
                                  if not os.path.isdir(os.path.join(dirpath, file_name))]
    dir_structure = delete_empty_folders(dir_structure)
    return dir_structure


def delete_empty_folders(input_dict: dict) -> dict:
    """Deletes in inputted dictionary paths for empty folders."""
    dict_copy = copy.deepcopy(input_dict)
    for folder_name in dict_copy.keys():
        if not input_dict[folder_name]:
            del input_dict[folder_name]
    return input_dict


def main():
    """This is the main function of the script.
    Firstly, are given two constant arguments:
        full path to the "imagesort.py"
        list of image types for sorting
    Secondly, main arguments are defined from the command line by using argparse module:
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

        if mode in ['copy', 'move', 'rename']:  # common for 'copy', 'move', 'sort' modes
            if not os.path.isdir(f'{target_folder}'):
                os.mkdir(f'{target_folder}')
                print(f'Information! Target folder "{target_folder}" was created')

            sort_images(target_folder, images_by_resolutions, images_attributes)

            if not_images:
                create_named_folder_and_copy_files(target_folder, 'Other files', not_images)
            if not_sized_files:
                create_named_folder_and_copy_files(target_folder, 'Error files', not_sized_files)
            validate_checksums(target_folder, all_files, images_attributes, images_by_resolutions,
                               not_images, not_sized_files)

            if mode in ['move', 'rename']:  # common for 'move' or 'sort' modes
                remove_initial_files(script_path, initial_folder)  # remove all files from the initial folder

                if mode == 'rename':  # only for 'sort' mode
                    rename_target_folder(script_path, initial_folder, target_folder)


if __name__ == '__main__':
    main()
