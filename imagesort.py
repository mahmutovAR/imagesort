from PIL import Image
import datetime
import hashlib
import os
import shutil
import sys
import time


def main():
    image_types = ['.bmp', '.gif', '.png', '.jpg', '.jpeg', '.tiff', '.raw']
    initial_folder, target_folder, remove_status, dry_run, all_files, images, not_images_status, not_images = input_parameters(image_types)
    images_by_resolutions = structure_of_target_folder(initial_folder, images)
    if dry_run:
        dry_run_report(target_folder, images_by_resolutions, not_images_status, not_images)
    else:
        ini_files_sha256 = checksums_in_the_initial_folder(initial_folder, all_files)
        create_folders_and_copy_images(initial_folder, target_folder, images_by_resolutions, ini_files_sha256)
        if not_images_status:
            create_folder_for_another_files(initial_folder, target_folder, not_images, ini_files_sha256)
        if remove_status:
            remove_initial_files (initial_folder)
        checksum_verification(ini_files_sha256, target_folder, images_by_resolutions, not_images_status, not_images)


def input_parameters(image_types: list) -> 'main args':
    """Gets parameters from CMD, checks them and returns main arguments."""
    script, initial_folder, target_folder, add_option = sys.argv
    if not os.path.isdir(initial_folder):
        print('Error! Entered initial folder doesnot exist!', initial_folder, sep='\n')
        sys.exit(0)

    if not os.path.isdir(target_folder):
        print('Error! Entered target folder doesnot exist!', target_folder, sep='\n')
        sys.exit(0)
        
    all_files = os.listdir(initial_folder)
    if len(all_files) == 0:
        print('Error! There are no files in the initial folder!', initial_folder, sep='\n')
        sys.exit(0)
        
    images = [file
              for file in all_files
              for image_format in image_types
              if file.endswith(image_format)]
    if len(images) == 0:
        print('Error! There are no images to sort in the initial folder!', initial_folder, sep='\n')
        sys.exit(0)

    remove_status = False
    dry_run = False
    if add_option.lower() == 'default' or add_option == ' ' or add_option == '-':
        program_mode= 'Default mode: sort image, move from initial folder'
        remove_status = True
        dry_run = False
    elif add_option.lower() =='dryrun':
        program_mode= 'Dry Run mode'
        dry_run = True
    elif add_option.lower() == 'copy':
        program_mode= 'User mode: sort image, copy to target folder'
        remove_status = False
        dry_run = False
    else:
        print('Error! Check mode parameter!', add_option, 'is not correct')
        sys.exit(0)
        
    print('Input parameters are:', '\n',
          'Initial folder:', '\n', initial_folder, '\n'
          'Target folder:', '\n', target_folder, '\n'
          'Additional option:', '\n', program_mode, '\n', sep='')
    
    not_images = [file
                  for file in all_files
                  if file not in images]
    
    not_images_status= False
    if len(not_images) !=0:
        not_images_status = True
        print('Information! There are another files (not images) in the initial folder,'
              'so directory "Another files" will be created.', '\n', '-'*50, sep='')
    
    
    return initial_folder, target_folder, remove_status, dry_run, all_files, images, not_images_status, not_images


def structure_of_target_folder(initial_folder: str, images: list) -> dict:
    """Forms the structure of directories with sorted images."""
    os.chdir(initial_folder)
    images_and_its_resolutions = {name : str(Image.open(name).size)
                                  for name in images}
    
    images_by_resolutions = {resolution:[k
                                         for k,v in images_and_its_resolutions.items()
                                         if v==resolution]
                             for resolution in set(images_and_its_resolutions.values())}

    return images_by_resolutions


def dry_run_report(target_folder: str, images_by_resolutions: dict,
                   not_images_status: bool, not_images: list) -> 'not html report':
    """Displays the new stucture of the target folder without any action."""
    print('After sorting the directory "', target_folder, '" will contain the next folder(s) and file(s):', '\n',
          '* if the directory already exists, the files will be added there', '\n',
          '** if there are files with the same names, but they are different,'
          'then old file will be renamed "!renamed-old_name"', '\n', sep='')
    for dir_name in sorted(images_by_resolutions.keys()):
            print(dir_name, end='\n')
            for file_name in images_by_resolutions[dir_name]:
                print('\t', file_name, sep='')        
    if not_images_status:
        print('Another files')
        for file_name in not_images:
                print('\t', file_name, sep='')


def checksums_in_the_initial_folder(initial_folder: str, all_files: list) -> dict:
    """"Returns dict, keys are names and values are checksums of the files from initial folder."""
    os.chdir(initial_folder)
    ini_files_sha256={}
    for file_name in all_files:
        with open(file_name, 'rb') as FN:
            bytes = FN.read()
            ini_files_sha256[file_name] = hashlib.sha256(bytes).hexdigest()
    return ini_files_sha256

        
def create_folders_and_copy_images(initial_folder: str, target_folder: str,
                                   images_by_resolutions: dict, ini_files_sha256: dict) ->  None:
    """Creates new folders (Width, Heigth) and copies images from initial folder to the new,
    if folder already exists files will be added there, if there are files with the same names,
    but they are different, then old file will be renamed "!renamed-old_name"."""
    os.chdir(target_folder)
    for folder_name in images_by_resolutions.keys():
        if not os.path.isdir(folder_name):
            os.mkdir(folder_name)           
        for image in images_by_resolutions[folder_name]:
            current_folder = target_folder + '/' + str(folder_name)+'/'
            existing_file = current_folder + str(image)
            if os.path.isfile(existing_file):
                with open(existing_file, 'rb') as FN:
                    bytes = FN.read()
                    existing_file_sha = hashlib.sha256(bytes).hexdigest()
                if ini_files_sha256[image] != existing_file_sha:
                    os.rename(existing_file, str(current_folder + '!renamed-' + str(file_name)))
                    shutil.copy(initial_folder+'/'+str(image), target_folder+'/'+str(folder_name)+'/'+str(image))
            else:
                shutil.copy(initial_folder+'/'+str(image), target_folder+'/'+str(folder_name)+'/'+str(image))


def create_folder_for_another_files(initial_folder: str, target_folder: str,
                                    not_images: list, ini_files_sha256: dict) -> None:
    """Creates folder for another files and copy them there, if folder already exists files will be added there,
    if there are files with the same names, but they are different,
    then old file will be renamed "!renamed-old_name"."""
    os.chdir(target_folder)
    if not os.path.isdir(target_folder + '/Another files/'):
        os.mkdir('Another files')
    for file_name in not_images:
        current_folder = target_folder + '/Another files/'
        existing_file = current_folder + str(file_name)
        if os.path.isfile(existing_file):
            with open(existing_file, 'rb') as FN:
                bytes = FN.read()
                existing_file_sha = hashlib.sha256(bytes).hexdigest()
            if ini_files_sha256[file_name] != existing_file_sha:
                os.rename(existing_file, str(current_folder + '!renamed-' + str(file_name)))
                shutil.copy(initial_folder+'/'+str(file_name), target_folder + '/Another files/'+str(file_name))
        else:
            shutil.copy(initial_folder+'/'+str(file_name), target_folder + '/Another files/'+str(file_name))

                   
def remove_initial_files (initial_folder: str) -> 'None':
    """Remove all files from initial folder."""
    files_list = os.listdir(initial_folder)
    for file_name in files_list:
        os.remove(initial_folder+'/'+str(file_name))


def checksum_verification(ini_files_sha256: dict, target_folder: str, images_by_resolutions: dict,
                          not_images_status: bool, not_images: list) -> None:
    """"Gets dict, keys are names of the files and values are checksums.
    Compares checksums before and after reorganization."""
    res_files_sha256={}
    for dir_name in images_by_resolutions.keys():
        os.chdir(target_folder+'/'+str(dir_name)+'/')
        for file_name in images_by_resolutions[dir_name]:
            with open(file_name, 'rb') as FN:
                bytes = FN.read()
                res_files_sha256[file_name] = hashlib.sha256(bytes).hexdigest()
                
    if not_images_status:           
        os.chdir(target_folder+'/Another files/')
        for file_name in not_images:
                with open(file_name, 'rb') as FN:
                    bytes = FN.read()
                    res_files_sha256[file_name] = hashlib.sha256(bytes).hexdigest()

    files_total=0
    not_verified = False
    for file_name in ini_files_sha256.keys():
        if ini_files_sha256[file_name] == res_files_sha256[file_name]:
            files_total+=1
        else:
            not_verified = True
    if not_verified:
        print('Verification compeled with error!')
    else:
        print(files_total, 'files was(re) verified successfully')

        
main()
