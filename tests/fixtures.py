import json
from argparse import ArgumentParser
from os import walk as os_walk
from os.path import join as os_path_join
from pathlib import Path
from shutil import copytree

import pytest
from bs4 import BeautifulSoup


TEST_DIR = Path(__file__).resolve().parent
# TEST_DIR = os_path_join(BASE_DIR, 'tests')
CONTROL_REPORT = os_path_join(TEST_DIR, 'reference report and structure', 'control report.html')
CONTROL_STRUCTURE = os_path_join(TEST_DIR, 'reference report and structure', 'control structure.json')


@pytest.fixture
def create_initial_folder():
    def copy_tree(copy_from: str, copy_to: str):
        try:
            copytree(copy_from, copy_to)
        except Exception as err:
            err.add_note('Error! Testing aborted')
            raise
    return copy_tree


@pytest.fixture
def reference_data():
    with open(CONTROL_STRUCTURE, 'r') as data_file:
        reference_structure = json.load(data_file)
    return reference_structure


@pytest.fixture
def simulate_argparse():
    def parse_args(input_args: list):
        test_parser = ArgumentParser()
        test_parser.add_argument('script_mode', type=str, choices=['dryrun', 'copy', 'move', 'sort'])
        test_parser.add_argument('initial_folder', type=Path, nargs='?')
        test_parser.add_argument('target_folder', type=Path, nargs='?')

        return test_parser.parse_args(input_args)
    return parse_args


@pytest.fixture
def ini_folder():
    return os_path_join(TEST_DIR, 'test INI DIR')


@pytest.fixture
def temp_folder():
    return os_path_join(TEST_DIR, 'unsorted')


@pytest.fixture
def parse_and_edit_html():
    def get_html(input_path: str):
        with open(input_path, 'r') as data_file:
            html_report = data_file.read()
        output_data = BeautifulSoup(html_report, 'lxml')
        output_data.h2.extract()
        output_data.h2.extract()
        return output_data
    return get_html


@pytest.fixture
def reference_report(parse_and_edit_html):
    return parse_and_edit_html(CONTROL_REPORT)


@pytest.fixture
def folder_structure():
    def get_folder_structure(given_folder: str):
        dir_structure = dict()
        for dir_path, dir_name, files_in_dir in os_walk(given_folder):
            if files_in_dir:
                dir_structure[f"""{dir_path.replace(given_folder, '"root dir" ')}"""] = files_in_dir
        output_dict = dict()
        for k in sorted(dir_structure):
            output_dict[k] = sorted(dir_structure[k])
        return output_dict
    return get_folder_structure
