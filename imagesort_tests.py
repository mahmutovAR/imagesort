from argparse import ArgumentParser, RawDescriptionHelpFormatter
from bs4 import BeautifulSoup
from os import walk as os_walk
from os import mkdir
from os.path import abspath, dirname
from os.path import join as os_path_join
from pathlib import Path
from shutil import copytree
from sys import exit as sys_exit
from tempfile import TemporaryDirectory
from ims_test_errors import TestFailedError
import imagesort
import json
import unittest
import argparse


SCRIPT_PATH = abspath(dirname(__file__))
BASE_DIR = Path(__file__).resolve().parent
CONTROL_REPORT = os_path_join(BASE_DIR, 'reference report and structure', 'control report.html')
CONTROL_STRUCTURE = os_path_join(BASE_DIR, 'reference report and structure', 'control structure.json')

TEMP_FOLDER = os_path_join(BASE_DIR, 'unsorted')
INITIAL_FOLDER = os_path_join(BASE_DIR, 'test INI DIR')


def simulate_argparse(input_args: list) -> 'argparse.Namespace':
    test_parser = ArgumentParser(prog='ImageSort',
                                 usage='imagesort.py [-h] [script_mode, initial_folder, target_folder]',
                                 formatter_class=RawDescriptionHelpFormatter,
                                 description='''
        %(prog)s sorts images by their resolutions.
        Reference information about application:
          dryrun "initial_dir" "report_dir" = app sorts files from "ini_dir" and generates html report in "report_dir"
          copy "initial_dir" "target_dir" = app sorts and copies files from "initial_dir" into "target_dir"
          move "initial_dir" "target_dir" = app sorts and moves files from "initial_dir" into "target_dir"
          sort "initial_dir" = app sorts files into "initial_dir" and deletes the initial files''')
    test_parser.add_argument('script_mode', type=str, help='Choose the mode',
                             choices=['dryrun', 'copy', 'move', 'sort'])
    test_parser.add_argument('initial_folder', type=Path, help='Input the initial folder', nargs='?', default=SCRIPT_PATH)
    test_parser.add_argument('target_folder', type=Path, help='Input the auxiliary folder', nargs='?', default=None)

    return test_parser.parse_args(input_args)


def create_initial_folder(copy_from: str, copy_to: str) -> None:
    """Creates temporary folders for testing."""
    try:
        copytree(copy_from, copy_to)
    except Exception as err:
        sys_exit(f"Error! Testing aborted, the exception was raised: {err}")


def get_reference_data() -> dict:
    """Returns dictionary with reference directory structure."""
    with open(CONTROL_STRUCTURE, 'r') as data_file:
        reference_structure = json.load(data_file)

    return reference_structure


def parse_and_edit_html(input_path: str) -> 'BeautifulSoup':
    """Parses html document and deletes tags 'h2' with path of initial folder.
    The edited document is returned."""
    with open(input_path, 'r') as data_file:
        html_report = data_file.read()
    output_data = BeautifulSoup(html_report, 'lxml')
    output_data.h2.extract()
    output_data.h2.extract()
    return output_data


def get_folder_structure(given_folder: str) -> dict:
    """Returns dictionary with full structure of the given directory.
    dir_structure = {'full_path_to_the_folder_1': ['file_name_1', 'file_name_2', etc.], etc.}
    """
    dir_structure = dict()
    for dir_path, dir_name, files_in_dir in os_walk(given_folder):
        if files_in_dir:
            dir_structure[f"""{dir_path.replace(given_folder, '"root dir" ')}"""] = files_in_dir

    return sort_dict(dir_structure)


def sort_dict(input_dict: dict) -> dict:
    """Return dictionary with sorted values."""
    output_dict = dict()
    for k in sorted(input_dict):
        output_dict[k] = sorted(input_dict[k])

    return output_dict


class ImagesortTest(unittest.TestCase):
    """Tests argparse module (for parsing different incorrect arguments) and each mode."""
    def setUp(self):
        create_initial_folder(TEMP_FOLDER, INITIAL_FOLDER)
        self.control_structure = get_reference_data()
        self.reference_report = parse_and_edit_html(CONTROL_REPORT)
        self.test_folder = os_path_join(INITIAL_FOLDER, 'folder_name')

    def test_argparse(self):
        """Tests argparse module in follow cases:
        - no mode in arguments
        - incorrect mode
        - no required path
        - no all required paths
        - incorrect path to initial folder
        - incorrect path to target folder
        ."""
        no_mode_data = [INITIAL_FOLDER, self.test_folder]
        with self.assertRaises(SystemExit):
            simulate_argparse(no_mode_data)

        incorrect_mode_data = ['incorrect_mode', INITIAL_FOLDER, self.test_folder]
        with self.assertRaises(SystemExit):
            simulate_argparse(incorrect_mode_data)

        no_path_data = ['dryrun']
        no_path_args = simulate_argparse(no_path_data)
        with self.assertRaises(imagesort.ArgParsingError):
            imagesort.main(no_path_args)

        no_all_paths_data = ['move']
        no_all_paths_args = simulate_argparse(no_all_paths_data)
        with self.assertRaises(imagesort.ArgParsingError):
            imagesort.main(no_all_paths_args)

        incorrect_ini_path_data = ['copy', os_path_join(INITIAL_FOLDER, 'error dir'), self.test_folder]
        incorrect_initial_path_args = simulate_argparse(incorrect_ini_path_data)
        with self.assertRaises(imagesort.FolderNotFoundError):
            imagesort.main(incorrect_initial_path_args)

        incorrect_targ_path_data = ['copy', INITIAL_FOLDER, os_path_join(self.test_folder, 'error dir')]
        incorrect_target_path_args = simulate_argparse(incorrect_targ_path_data)
        with self.assertRaises(imagesort.FolderNotFoundError):
            imagesort.main(incorrect_target_path_args)

    def test_dryrun_mode(self):
        with TemporaryDirectory() as temp_dir:
            test_data = simulate_argparse(['dryrun', INITIAL_FOLDER, temp_dir])
            imagesort.main(test_data)
            testing_report = parse_and_edit_html(os_path_join(temp_dir, 'DryRun report.html'))
            if self.reference_report != testing_report:
                raise TestFailedError('DRY RUN mode')

    def test_copy_mode(self):
        with TemporaryDirectory() as temp_dir:
            test_data = simulate_argparse(['copy', INITIAL_FOLDER, temp_dir])
            imagesort.main(test_data)
            testing_structure = get_folder_structure(temp_dir)
            if self.control_structure != testing_structure:
                raise TestFailedError('COPY mode')

    def test_move_mode(self):
        with TemporaryDirectory() as temp_dir:
            first_temp_dir = os_path_join(temp_dir, '1')
            second_temp_dir = os_path_join(temp_dir, '2')
            mkdir(second_temp_dir)
            create_initial_folder(INITIAL_FOLDER, first_temp_dir)
            test_data = simulate_argparse(['move', first_temp_dir, second_temp_dir])
            imagesort.main(test_data)
            testing_structure = get_folder_structure(second_temp_dir)
            if self.control_structure != testing_structure:
                raise TestFailedError('MOVE mode')

    def test_sort_mode(self):
        test_data = simulate_argparse(['sort', INITIAL_FOLDER])
        imagesort.main(test_data)
        testing_structure = get_folder_structure(INITIAL_FOLDER)
        if self.control_structure != testing_structure:
            raise TestFailedError('SORT mode')

    def tearDown(self):
        imagesort.delete_folder(INITIAL_FOLDER)


if __name__ == '__main__':
    unittest.main()
