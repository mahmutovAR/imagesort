from chameleon import PageTemplateLoader
from PIL import Image
import copy
import hashlib
import os
import stat
import shutil
import sys


def main():
    dir_path = os.path.abspath(os.path.dirname(__file__))
    image_types = ['.bmp', '.gif', '.png', '.jpg', '.jpeg', '.tiff', '.raw']

    script, *args = sys.argv
    if len(args) == 2 and args[0].lower() == '-dryrun':
        initial_folder = args[1]
        print(f'Input parameters are:\nInitial folder:\t{initial_folder}/\nAdditional option:  "Dry Run mode"\n')
        all_files, images, not_images_status, not_images = parse_arguments(image_types, initial_folder)
        images_attributes, images_by_resolutions, not_sized_status, not_sized_files = create_directories_structure(initial_folder, images)
        generate_html_report(dir_path, initial_folder, all_files, images_attributes, images_by_resolutions,
                             not_images_status, not_images, not_sized_status, not_sized_files)
    elif len(args) == 3 and args[0].lower() == '-copy':
        initial_folder = args[1]
        target_folder = args[2]
        print(f'Input parameters are:\nInitial folder:\t{initial_folder}/\nTarget folder:\t{target_folder}/'
              f'\nAdditional option:  "Copy sorted files from initial folder to the target folder"\n')
        if not os.path.isdir(f'{target_folder}'):
            os.mkdir(f'{target_folder}')
            print(f'Information! Target folder "{target_folder}" was created')
        all_files, images, not_images_status, not_images = parse_arguments(image_types, initial_folder)
        images_attributes, images_by_resolutions, not_sized_status, not_sized_files = create_directories_structure(initial_folder, images)
        exception_dict = sort_images(target_folder, images_attributes, images_by_resolutions)
        if not_images_status:
            create_named_folder_and_copy_files(target_folder, 'Other files', not_images, exception_dict)
        if not_sized_status:
            create_named_folder_and_copy_files(target_folder, 'Error files', not_sized_files, exception_dict)
        validate_checksums(target_folder, all_files, images_attributes, images_by_resolutions,
                           not_images_status, not_images, not_sized_status, not_sized_files, exception_dict)
    elif len(args) == 3 and args[0].lower() == '-remove':
        initial_folder = args[1]
        target_folder = args[2]
        print(f'Input parameters are:\nInitial folder:\t{initial_folder}/\nTarget folder:\t{target_folder}/'
              f'\nAdditional option:  "Remove sorted files from the initial folder into the target folder"\n')
        if not os.path.isdir(f'{target_folder}'):
            os.mkdir(f'{target_folder}')
            print(f'Information! Target folder "{target_folder}" was created')
        all_files, images, not_images_status, not_images = parse_arguments(image_types, initial_folder)
        images_attributes, images_by_resolutions, not_sized_status, not_sized_files = create_directories_structure(
            initial_folder, images)
        exception_dict = sort_images(target_folder, images_attributes, images_by_resolutions)
        if not_images_status:
            create_named_folder_and_copy_files(target_folder, 'Other files', not_images, exception_dict)
        if not_sized_status:
            create_named_folder_and_copy_files(target_folder, 'Error files', not_sized_files, exception_dict)
        validate_checksums(target_folder, all_files, images_attributes, images_by_resolutions, not_images_status,
                           not_images, not_sized_status, not_sized_files, exception_dict)
        remove_initial_files(dir_path, initial_folder)
    elif len(args) == 1 and args[0].lower() != '-help':
        initial_folder = args[0]
        print(f'Input parameters are:\nInitial folder:\t{initial_folder}/\nAdditional option:  "Sort files '
              f'into the inputted folder and delete initial files"\n')
        target_folder = create_temp_folder(initial_folder)
        all_files, images, not_images_status, not_images = parse_arguments(image_types, initial_folder)
        images_attributes, images_by_resolutions, not_sized_status, not_sized_files = create_directories_structure(
            initial_folder, images)
        exception_dict = sort_images(target_folder, images_attributes, images_by_resolutions)
        if not_images_status:
            create_named_folder_and_copy_files(target_folder, 'Other files', not_images, exception_dict)
        if not_sized_status:
            create_named_folder_and_copy_files(target_folder, 'Error files', not_sized_files, exception_dict)
        validate_checksums(target_folder, all_files, images_attributes, images_by_resolutions, not_images_status,
                           not_images, not_sized_status, not_sized_files, exception_dict)
        remove_initial_files(dir_path, initial_folder)
        rename_target_folder(dir_path, initial_folder, target_folder)
    else:
        sys.exit(f'Reference information about application "ImageSort":'
                 f'\nimagesort.py -help = get this reference Information'
                 f'\nimagesort.py -dryrun "directory path" = generate html-report '
                 f'with sorted files structure from inputted folder'
                 f'\nimagesort.py -copy "first directory path" "second directory path" = sort files '
                 f'from "directory 1" into "directory 2"'
                 f'\nimagesort.py -remove "first directory path" "second directory path" = sort files '
                 f'from "directory 1" into "directory 2" and delete initial files from "directory 1"'
                 f'\nimagesort.py "folder name" = sort files into the inputted folder '
                 f'and delete initial files')


def parse_arguments(image_types: list, initial_folder: str) -> 'main arguments':
    """Checks the initial folder for existing and the presence of images there, gets dictionaries with structure of
    the initial folder, images and other files from initial folder."""

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
                            if file.lower().endswith(image_format)]

    for dir_path in all_files.keys():
        not_images[dir_path] = [file
                                for file in all_files[dir_path]
                                if file not in images[dir_path]]

    images = delete_empty_folders(images)
    not_images = delete_empty_folders(not_images)
    
    if not images:
        sys.exit(f'Error! There are no images to sort in the initial folder: {initial_folder}')

    not_images_status = False
    if not_images:
        not_images_status = True
        print(f'Information! There is(are) "not images" file(s) in the initial folder '
              f'so directory "Other files" will be created.')
    
    return all_files, images, not_images_status, not_images


def create_directories_structure(initial_folder: str, images: dict) -> 'dict and bool':
    """Gets two dictionaries, one with resolutions of each image,
    and second with images for which resolution couldn't be determined."""
    os.chdir(initial_folder)
    not_sized_status = False
    not_sized_files = {}
    images_attributes = {}
    for folder_name in images.keys():
        for image_name in images[folder_name]:
            try:
                w, h = Image.open(f'{folder_name}/{image_name}').size
            except:
                not_sized_status = True
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

    if not_sized_status:
        print(f"Information! There is(are) file(s) in the initial folder for which resolution couldn't "
              f'be determined so directory "Error files" will be created.\n')
    
    return images_attributes, images_by_resolutions, not_sized_status, not_sized_files


def generate_html_report(dir_path: str, initial_folder: str, all_files: dict, images_attributes: dict,
                         images_by_resolutions: dict, not_images_status: bool, not_images: dict,
                         not_sized_status: bool, not_sized_files: dict) -> 'html report':
    """Generates the html report which will show previous structure and suggested reorganization."""
    initial_folder = f'{initial_folder}/'
    report_name = 'DryRun report'
    output_files = {resolution: [images_attributes[image][0]
                                 for image in images_by_resolutions[resolution]]
                    for resolution in images_by_resolutions.keys()}
    if not_images_status:
        not_images_list = []
        for key in not_images:
            not_images_list += not_images[key]
        output_files['Other files'] = not_images_list
    if not_sized_status:
        not_sized_files_list = []
        for key in not_sized_files:
            not_sized_files_list += not_sized_files[key]
        output_files['Error files'] = not_sized_files_list

    sorted_output_files = {k: sorted(output_files[k])
                           for k in sorted(output_files)}

    try:
        templates = PageTemplateLoader(os.path.join(dir_path, "templates"))
        tmpl = templates['report_temp.pt']
        result_html = tmpl(title=report_name, input_folder=initial_folder,
                           initial_dir=all_files, structure=sorted_output_files)
    except:
        print('The building of the HTML report caused the exception, please check the integrity of the source files')
    else:
        report = open(f'{initial_folder}/{report_name}.html', 'w')
        report.write(result_html)
        report.close()
        print(f'The file "{report_name}.html" was created in the directory "{initial_folder}"')


def sort_images(target_folder: str, images_attributes: dict, images_by_resolutions: dict) -> dict:
    """Creates new folders (Width x Height) and copies images from initial folder to the new,
    if folder already exists files will be added there, if there is file with the same name,
    then the new file will be renamed, "!{num}-" will be added to its name."""
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
                       not_images_status: bool, not_images: dict, not_sized_status: bool,
                       not_sized_files: dict, exception_dict: dict) -> None:
    """"Compares checksums of the files from initial folder and copied files after reorganization."""
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

    if not_images_status:
        res_files_checksums.extend(calculate_checksum_from_named_folder(target_folder, 'Other files',
                                                                        not_images, exception_dict))

    if not_sized_status:
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
    print(f'\n"ImageSort" report:\nFrom initial folder was(re) sorted successfully:\n'
          f'Images{len(images_attributes.keys()):>20}\n'
          f'Not images{total_not_images:>16}\n'
          f'Not sized images{total_not_sized_files:>10}\n'
          f'Total files{total_all_files:>15}')
         

def remove_initial_files(dir_path: str, initial_folder: str) -> None:
    """Removes all files from given folder even with attribute "readonly"."""
    os.chdir(dir_path)
    try:
        shutil.rmtree(initial_folder, onerror=delete_readonly)
    except PermissionError as err:
        sys.exit(f'Attention! Deleting of the initial folder completed with an error: {err}'
                 f'\nPlease close the folder in explorer or another application and try again')
    except Exception as err:
        sys.exit(f'Attention! Deleting of the initial folder completed with an error: {err}')


def delete_readonly(action, name, exc) -> None:
    """Deletes files with attribute "readonly"."""
    os.chmod(name, stat.S_IWRITE)
    os.remove(name)


def rename_target_folder(dir_path: str, initial_folder: str, target_folder: str) -> None:
    """Renames temp target folder into initial folder."""
    os.chdir(dir_path)
    os.rename(target_folder, initial_folder)


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
    the new file will be renamed before coping, "!{num}-" will be added to its name."""
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
    """Gets full structure of the given path."""
    dir_structure = {}
    for dirpath, dirs, files in os.walk(f'{folder}'):
        dir_structure[dirpath.replace('\\', '/')] = [file_name
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
    """Returns checksum of the files from given folder."""
    named_folder_checksums = []
    for folder_name in input_dict.keys():
        for file_name in input_dict[folder_name]:
            if f'{folder_name}/{file_name}' in exception_dict.keys():
                checked_file_name = exception_dict[f'{folder_name}/{file_name}']
            else:
                checked_file_name = file_name
            named_folder_checksums.append(calculate_checksums(f'{target_folder}/{dir_name}/{checked_file_name}'))

    return named_folder_checksums


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


main()
