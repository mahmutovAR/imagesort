from PIL import Image
#import chameleon # will be used later
import hashlib
import os
import shutil
import sys


def main():
    image_types = ['.bmp', '.gif', '.png', '.jpg', '.jpeg', '.tiff', '.raw']
    initial_folder, target_folder, remove_status, dry_run, all_files, images, not_images_status, not_images = input_parameters (image_types)
    images_by_resolutions = structure_of_target_folder(initial_folder, images)
    if dry_run:
        dry_run_report(target_folder, images_by_resolutions, not_images_status, not_images)
    else:
        ini_files_sha256 = checksums_in_the_initial_folder(initial_folder, all_files)
        create_folders_and_copy_images(initial_folder, target_folder, images_by_resolutions, ini_files_sha256)
        if not_images_status:
            create_folder_for_other_files(initial_folder, target_folder, not_images, ini_files_sha256)
        if remove_status:
            remove_initial_files(initial_folder)
        checksum_verification(ini_files_sha256, target_folder, images_by_resolutions, not_images_status, not_images)


def input_parameters(image_types: list) -> 'main args':
    """Gets parameters from CMD, checks them and returns main arguments."""
    script, initial_folder, target_folder, add_option = sys.argv

    if not os.path.isdir(target_folder):
        print(f"Error! Entered target folder doesn't exist! \n{target_folder}")
        sys.exit(0) # or use break

    if not os.path.isdir(initial_folder):
        print(f"Error! Entered initial folder doesn't exist! \n{initial_folder}")
        sys.exit(0) # or use break

    all_files = os.listdir(initial_folder)
    if not all_files:
        print(f'Error! There are no files in the initial folder! \n{initial_folder}')
        sys.exit(0) # or use break

    images = [file
              for file in all_files
              for image_format in image_types
              if file.endswith(image_format)]
    if not images:
        print(f'Error! There are no images to sort in the initial folder! \n{initial_folder}')
        sys.exit(0) # or use break

    remove_status = False
    dry_run = False
    if add_option.lower() == 'default':
        program_mode = 'Default mode: sort image, move from initial folder'
        remove_status = True
    elif add_option.lower() == 'dryrun':
        program_mode = 'Dry Run mode'
        dry_run = True
    elif add_option.lower() == "copy":
        program_mode = 'User mode: sort image, copy to target folder'
    else:
        print('Error! Check mode parameter!', add_option, 'is not correct')
        sys.exit(0) # or use break

    print(f'Input parameters are:\nInitial folder:\t{initial_folder}\nTarget folder:'
          f'\t{target_folder}\nAdditional option:\t{program_mode}')

    not_images = [file
                  for file in all_files
                  if file not in images]

    not_images_status = False
    if not_images:
        not_images_status = True
        print(f'\nInformation! There is(are) "not images" file(s) in the initial folder '
              f'so directory "Other files" will be created.\n{"-" * 50}')

    return initial_folder, target_folder, remove_status, dry_run, all_files, images, not_images_status, not_images


def structure_of_target_folder(initial_folder: str, images: list) -> dict:
    """Forms the structure of directories with sorted images."""
    os.chdir(initial_folder)
    # add checking for not images with "image" format and for folder
    images_and_its_resolutions = {}
    for name in images:
        w, h = Image.open(name).size
        images_and_its_resolutions[name] = f'{w}x{h}'

    images_by_resolutions = {resolution: [k
                                          for k, v in images_and_its_resolutions.items()
                                          if v == resolution]
                             for resolution in set(images_and_its_resolutions.values())}

    return images_by_resolutions


def dry_run_report(target_folder: str, images_by_resolutions: dict,
                   not_images_status: bool, not_images: list) -> 'not html report':
    """Displays the new structure of the target folder without any action."""
    print(f'After sorting the directory "{target_folder}" will contain the next folder(s) and file(s):\n'
          '* if the directory already exists, the files will be added there\n'
          '** if there are files with the same names, but they are different'
          'then old file will be renamed "!renamed-old_name"\n')
    for dir_name in sorted(images_by_resolutions.keys()):
        print(f'{dir_name}')
        for file_name in images_by_resolutions[dir_name]:
            print(f'\t{file_name}')
    if not_images_status:
        print('Other files')
        for file_name in not_images:
            print(f'\t{file_name}')


def checksums_in_the_initial_folder(initial_folder: str, all_files: list) -> dict:
    """"Returns dict, keys are names and values are checksums of the files from initial folder."""
    os.chdir(initial_folder)
    ini_files_sha256 = {}
    for file_name in all_files:
        with open(file_name, 'rb') as FN:
            checksum = FN.read()
            ini_files_sha256[file_name] = hashlib.sha256(checksum).hexdigest()

    # use it if necessary:
    # for file_name in all_files:
    #     if not os.path.isdir(f'{initial_folder}/{file_name}'):
    #         with open(file_name, 'rb') as FN:
    #             checksum = FN.read()
    #             ini_files_sha256[file_name] = hashlib.sha256(checksum).hexdigest()
    #     else:
    #         print(f'There is(are) folder in {initial_folder}:\t{file_name}')
    return ini_files_sha256


def create_folders_and_copy_images(initial_folder: str, target_folder: str,
                                   images_by_resolutions: dict, ini_files_sha256: dict) -> None:
    """Creates new folders (Width x Height) and copies images from initial folder to the new,
    if folder already exists files will be added there, if there are files with the same names,
    but they are different, then old file will be renamed "!renamed-old_name"."""
    # rename new file: edit dictionary with resolutions and dictionary with checksums
    os.chdir(target_folder)
    for folder_name in images_by_resolutions.keys():
        if not os.path.isdir(folder_name):
            os.mkdir(folder_name)
        for image in images_by_resolutions[folder_name]:
            current_folder = f'{target_folder}/{folder_name}/'
            existing_file = f'{current_folder}{image}'
            if os.path.isfile(existing_file):
                with open(existing_file, 'rb') as FN:
                    checksum = FN.read()
                    existing_file_sha = hashlib.sha256(checksum).hexdigest()
                if ini_files_sha256[image] != existing_file_sha:
                    os.rename(existing_file, f'{current_folder}!renamed-{file_name}')
                    shutil.copy(f'{initial_folder}/{image}', f'{target_folder}/{folder_name}/{image}')
            else:
                shutil.copy(f'{initial_folder}/{image}', f'{target_folder}/{folder_name}/{image}')


def create_folder_for_other_files(initial_folder: str, target_folder: str,
                                    not_images: list, ini_files_sha256: dict) -> None:
    """Creates folder for other files and copy them there, if folder already exists files will be added there,
    if there are files with the same names, but they are different,
    then old file will be renamed "!renamed-old_name"."""
    os.chdir(target_folder)
    if not os.path.isdir(target_folder + '/Other files/'):
        os.mkdir('Other files')
    for file_name in not_images:
        current_folder = target_folder + '/Other files/'
        existing_file = current_folder + str(file_name)
        if os.path.isfile(existing_file):
            with open(existing_file, 'rb') as FN:
                checksum = FN.read()
                existing_file_sha = hashlib.sha256(checksum).hexdigest()
            if ini_files_sha256[file_name] != existing_file_sha:
                os.rename(existing_file, f'{current_folder}!renamed-{file_name}')
                shutil.copy(f'{initial_folder}/{file_name}', f'{target_folder}/Other files/{file_name}')
        else:
            shutil.copy(f'{initial_folder}/{file_name}', f'{target_folder}/Other files/{file_name}')


def remove_initial_files(initial_folder: str) -> 'None':
    """Remove all files from initial folder."""
    files_list = os.listdir(initial_folder)
    for file_name in files_list:
        os.remove(f'{initial_folder}/{file_name}')


def checksum_verification(ini_files_sha256: dict, target_folder: str, images_by_resolutions: dict,
                          not_images_status: bool, not_images: list) -> None:
    """"Gets dict, keys are names of the files and values are checksums.
    Compares checksums before and after reorganization."""
    res_files_sha256 = {}
    for dir_name in images_by_resolutions.keys():
        os.chdir(f'{target_folder}/{dir_name}/')
        for file_name in images_by_resolutions[dir_name]:
            with open(file_name, 'rb') as FN:
                checksum = FN.read()
                res_files_sha256[file_name] = hashlib.sha256(checksum).hexdigest()

    if not_images_status:
        os.chdir(f'{target_folder}/Other files/')
        for file_name in not_images:
            with open(file_name, 'rb') as FN:
                checksum = FN.read()
                res_files_sha256[file_name] = hashlib.sha256(checksum).hexdigest()

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
        print(files_total, 'files was(re) verified successfully')


main()
