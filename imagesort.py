from PIL import Image
# import chameleon
import hashlib
import os
import shutil
import sys


def main():
    image_types = ['.bmp', '.gif', '.png', '.jpg', '.jpeg', '.tiff', '.raw']
    initial_folder, target_folder, remove_status, dry_run, all_files, images, not_images_status, not_images = input_parameters(image_types)
    images_by_resolutions, not_sized_status, not_sized_files = structure_of_target_folder(initial_folder, images)
    if dry_run:
        dry_run_report(target_folder, images_by_resolutions, not_images_status, not_images,
                       not_sized_status, not_sized_files)
    else:
        ini_files_sha256 = checksums_in_the_initial_folder(initial_folder, all_files)
        exception_list = create_folders_and_copy_images(initial_folder, target_folder,
                                                        images_by_resolutions, ini_files_sha256)
        if not_images_status:
            create_folder_for_other_files(initial_folder, target_folder,
                                          not_images, ini_files_sha256, exception_list)
        if not_sized_status:
            create_folder_for_error_files(initial_folder, target_folder,
                                          not_sized_files, ini_files_sha256, exception_list)
        if remove_status:
            remove_initial_files(initial_folder, all_files)
        checksum_verification(ini_files_sha256, target_folder, images_by_resolutions, not_images_status,
                              not_images, not_sized_status, not_sized_files, exception_list)


def input_parameters(image_types: list) -> 'main args':
    """Gets parameters from CMD, checks them and returns main arguments."""
    script, initial_folder, target_folder, add_option = sys.argv

    if not os.path.isdir(target_folder):
        print(f"Error! Entered target folder doesn't exist! \n{target_folder}")
        sys.exit(0)

    if not os.path.isdir(initial_folder):
        print(f"Error! Entered initial folder doesn't exist! \n{initial_folder}")
        sys.exit(0)

    all_files = [file_name
                 for file_name in os.listdir(initial_folder)
                 if not os.path.isdir(f'{initial_folder}/{file_name}')]

    if not all_files:
        print(f'Error! There are no files in the initial folder! \n{initial_folder}')
        sys.exit(0)

    images = [file
              for file in all_files
              for image_format in image_types
              if file.endswith(image_format)]

    if not images:
        print(f'Error! There are no images to sort in the initial folder! \n{initial_folder}')
        sys.exit(0)

    remove_status = False
    dry_run = False
    if add_option.lower() == 'default':
        program_mode = 'sort image and move from the initial folder to the target folder'
        remove_status = True
    elif add_option.lower() == 'dryrun':
        program_mode = 'Dry Run mode'
        dry_run = True
    elif add_option.lower() == "copy":
        program_mode = 'sort image and copy to the target folder'
    else:
        print('Error! Check mode parameter!', add_option, 'is not correct')
        sys.exit(0)

    print(f'Input parameters are:\nInitial folder:\t{initial_folder}\nTarget folder:'
          f'\t{target_folder}\nAdditional option:\t{program_mode}\n')

    not_images = [file
                  for file in all_files
                  if file not in images]

    for folder in os.listdir(initial_folder):
        if os.path.isdir(f'{initial_folder}/{folder}'):
            print(f"""Information! There is the directory "{folder}" in the initial folder, it won't be modified.""")

    not_images_status = False
    if not_images:
        not_images_status = True
        print(f'Information! There is(are) "not images" file(s) in the initial folder '
              f'so directory "Other files" will be created.')

    return initial_folder, target_folder, remove_status, dry_run, all_files, images, not_images_status, not_images


def structure_of_target_folder(initial_folder: str, images: list) -> dict:
    """Forms the structure of directories with sorted images."""
    os.chdir(initial_folder)
    not_sized_status = False
    not_sized_files = []
    images_and_its_resolutions = {}
    for name in images:
        try:
            w, h = Image.open(name).size
        except Exception:
            not_sized_status = True
            not_sized_files.append(name)
        else:
            images_and_its_resolutions[name] = f'{w}x{h}'

    images_by_resolutions = {resolution: [k
                                          for k, v in images_and_its_resolutions.items()
                                          if v == resolution]
                             for resolution in set(images_and_its_resolutions.values())}

    if not_sized_status:
        print(f"Information! There is(are) file(s) in the initial folder for which resolution couldn't "
              f'be determined so directory "Error files" will be created.\n')

    return images_by_resolutions, not_sized_status, not_sized_files


def dry_run_report(target_folder: str, images_by_resolutions: dict,
                   not_images_status: bool, not_images: list,
                   not_sized_status: bool, not_sized_files: list) -> 'not html report':
    """Displays the new structure of the target folder without any action."""
    txt_report = open(f'{target_folder}/DryRun report.txt', 'w')
    txt_report.write(f'After sorting the directory "{target_folder}" will contain the next folder(s) and file(s):\n'
                     '* if the directory already exists, the files will be added there\n'
                     '** if there are files with the same names, but they are different\n'
                     'then the new file will be renamed "!{num}-" will be added to its name.\n\n')
    for dir_name in sorted(images_by_resolutions.keys()):
        txt_report.write(f'{dir_name}\n')
        for file_name in images_by_resolutions[dir_name]:
            txt_report.write(f'\t{file_name}\n')
    if not_images_status:
        txt_report.write('Other files\n')
        for file_name in not_images:
            txt_report.write(f'\t{file_name}\n')
    if not_sized_status:
        txt_report.write('Error files\n')
        for file_name in not_sized_files:
            txt_report.write(f'\t{file_name}\n')
    txt_report.close()
    print(f'The file "DryRun report.txt" was created in the directory "{target_folder}"')


def checksums_in_the_initial_folder(initial_folder: str, all_files: list) -> dict:
    """"Returns dict, keys are names and values are checksums of the files from initial folder."""
    os.chdir(initial_folder)
    ini_files_sha256 = {}
    for file_name in all_files:
        ini_files_sha256[file_name] = getting_checksum(file_name)

    return ini_files_sha256


def create_folders_and_copy_images(initial_folder: str, target_folder: str,
                                   images_by_resolutions: dict, ini_files_sha256: dict) -> dict:
    """Creates new folders (Width x Height) and copies images from initial folder to the new,
    if folder already exists files will be added there, if there are files with the same names,
    but they are different, then the new file will be renamed, "!new-" will be added to its name."""
    exception_dict = {}
    os.chdir(target_folder)
    for folder_name in images_by_resolutions.keys():
        if not os.path.isdir(folder_name):
            os.mkdir(folder_name)
        for image in images_by_resolutions[folder_name]:
            shutil.copy(f'{initial_folder}/{image}',
                        f'{target_folder}/{check_file(folder_name, image, ini_files_sha256, exception_dict)}')
    return exception_dict


def create_folder_for_other_files(initial_folder: str, target_folder: str,
                                  not_images: list, ini_files_sha256: dict, exception_dict: list) -> None:
    """Creates folder for other files and copy them there, if folder already exists files will be added there,
    if there are files with the same names, but they are different,
    then the new file will be renamed, "!new-" will be added to its name."""
    os.chdir(target_folder)
    if not os.path.isdir(f'{target_folder}/Other files/'):
        os.mkdir('Other files')
    for file_name in not_images:
        shutil.copy(f'{initial_folder}/{file_name}',
                    f'{target_folder}/{check_file("Other files", file_name, ini_files_sha256, exception_dict)}')


def create_folder_for_error_files(initial_folder: str, target_folder: str,
                                  not_sized_files: list, ini_files_sha256: dict, exception_dict: list) -> None:
    """Creates folder for error files and copy them there, if folder already exists files will be added there,
    if there are files with the same names, but they are different,
    then the new file will be renamed, "!new-" will be added to its name."""
    os.chdir(target_folder)
    if not os.path.isdir(f'{target_folder}/Error files/'):
        os.mkdir('Error files')
    for file_name in not_sized_files:
        shutil.copy(f'{initial_folder}/{file_name}',
                    f'{target_folder}/{check_file("Error files", file_name, ini_files_sha256, exception_dict)}')


def remove_initial_files(initial_folder: str, all_files: list) -> None:
    """Remove all files from initial folder."""
    for file_name in all_files:
        os.remove(f'{initial_folder}/{file_name}')


def checksum_verification(ini_files_sha256: dict, target_folder: str, images_by_resolutions: dict,
                          not_images_status: bool, not_images: list,
                          not_sized_status: bool, not_sized_files: list, exception_dict: list) -> None:
    """"Gets dict, keys are names of the files and values are checksums.
    Compares checksums before and after reorganization."""
    res_files_sha256 = {}
    for dir_name in images_by_resolutions.keys():
        os.chdir(f'{target_folder}/{dir_name}/')
        for file_name in images_by_resolutions[dir_name]:
            if file_name in exception_dict.keys():
                res_files_sha256[exception_dict[file_name]] = getting_checksum(f'{target_folder}/{dir_name}/{exception_dict[file_name]}')
            else:
                res_files_sha256[file_name] = getting_checksum(f'{target_folder}/{dir_name}/{file_name}')

    if not_images_status:
        os.chdir(f'{target_folder}/Other files/')
        for file_name in not_images:
            if file_name in exception_dict.keys():
                res_files_sha256[exception_dict[file_name]] = getting_checksum(f'{target_folder}/Other files/{exception_dict[file_name]}')
            else:
                res_files_sha256[file_name] = getting_checksum(f'{target_folder}/Other files/{file_name}')

    if not_sized_status:
        os.chdir(f'{target_folder}/Error files/')
        for file_name in not_sized_files:
            if file_name in exception_dict.keys():
                res_files_sha256[exception_dict[file_name]] = getting_checksum(f'{target_folder}/Error files/{exception_dict[file_name]}')
            else:
                res_files_sha256[file_name] = getting_checksum(f'{target_folder}/Error files/{file_name}')

    files_total = 0
    not_verified = False
    for file_name in ini_files_sha256.keys():
        if ini_files_sha256[file_name] == res_files_sha256[file_name]:
            files_total += 1
        else:
            not_verified = True
    if not_verified:
        print('Verification completed with error!')
    else:
        print(f'{files_total} files was(re) verified successfully')


def getting_checksum(arg_file: str) -> str:
    """Returns checksum of the input file."""
    block_size = 65536
    sha = hashlib.sha256()
    with open(arg_file, 'rb') as CF:
        file_buffer = CF.read(block_size)
        while len(file_buffer) > 0:
            sha.update(file_buffer)
            file_buffer = CF.read(block_size)
    return sha.hexdigest()


def check_file(folder: str, checking_file: str, ini_files_sha256: dict, exception_dict: dict) -> str:
    """Checks existing file to be the same to the new file, if files are different,
    the new file will be renamed, "!{num}-" will be added to its name."""
    existing_file = f'{folder}/{checking_file}'
    if os.path.isfile(existing_file):
        if ini_files_sha256[checking_file] != getting_checksum(existing_file):
            num = 1
            while os.path.isfile(f'{folder}/!{num}-{checking_file}')\
                    and ini_files_sha256[checking_file] != getting_checksum(f'{folder}/!{num}-{checking_file}'):
                num += 1
            ini_files_sha256[f'!{num}-{checking_file}'] = ini_files_sha256[checking_file]
            exception_dict[checking_file] = f'!{num}-{checking_file}'
            del ini_files_sha256[checking_file]
            output_file_name = f'{folder}/!{num}-{checking_file}'
        else:
            output_file_name = f'{folder}/{checking_file}'
    return output_file_name


main()
