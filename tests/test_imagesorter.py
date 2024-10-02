from os import mkdir
from os.path import isdir
from os.path import join as os_path_join
from tempfile import TemporaryDirectory

from pytest import fixture, raises

import imagesort


def test_argparse_no_mode(set_up: fixture, ini_folder: fixture, simulate_argparse: fixture):
    """Test of argparse module, no mode in arguments."""
    no_mode_data = [ini_folder, os_path_join(ini_folder, 'folder_name')]
    with raises(SystemExit):
        simulate_argparse(no_mode_data)


def test_argparse_incorrect_mode(set_up: fixture, ini_folder: fixture, simulate_argparse: fixture):
    """Test of argparse module, incorrect mode."""
    incorrect_mode_data = ['incorrect_mode', ini_folder, os_path_join(ini_folder, 'folder_name')]
    with raises(SystemExit):
        simulate_argparse(incorrect_mode_data)


def test_argparse_no_path(set_up: fixture, simulate_argparse: fixture):
    """Test of argparse module, no required path."""
    no_path_data = ['dryrun']
    no_path_args = simulate_argparse(no_path_data)
    with raises(imagesort.ArgParsingError):
        imagesort.main(no_path_args)


def test_argparse_no_all_paths(set_up: fixture, simulate_argparse: fixture):
    """Test of argparse module, no all required paths."""
    no_all_paths_data = ['move']
    no_all_paths_args = simulate_argparse(no_all_paths_data)
    with raises(imagesort.ArgParsingError):
        imagesort.main(no_all_paths_args)


def test_argparse_incorrect_ini_path(set_up: fixture, ini_folder: fixture, simulate_argparse: fixture):
    """Test of argparse module, initial folder doesn't exist."""
    incorrect_ini_path_data = ['copy', os_path_join(ini_folder, 'error dir'), os_path_join(ini_folder, 'folder_name')]
    incorrect_initial_path_args = simulate_argparse(incorrect_ini_path_data)
    with raises(imagesort.InitialFolderNotFoundError):
        imagesort.main(incorrect_initial_path_args)


def test_argparse_incorrect_target_path(set_up: fixture, ini_folder: fixture, simulate_argparse: fixture):
    """Test of argparse module, target folder is relative to initial folder."""
    incorrect_target_path_data = ['copy', ini_folder, os_path_join(ini_folder, 'new dir', 'folder_1')]
    incorrect_target_path_args = simulate_argparse(incorrect_target_path_data)
    with raises(imagesort.TargetFolderIsRelativeToInitialFolderError):
        imagesort.main(incorrect_target_path_args)


def test_target_folder_was_created(set_up: fixture):
    """Test of creating of the target folder."""
    with TemporaryDirectory() as temp_dir:
        test_target_folder = os_path_join(temp_dir, 'folder_1', 'nested_folder', 'test_folder')
        imagesort.create_target_folder(test_target_folder)
        assert isdir(test_target_folder)


def test_dryrun_mode(set_up: fixture, ini_folder: fixture, reference_report: fixture,
                     simulate_argparse: fixture, parse_and_edit_html: fixture):
    """Test of dryrun mode."""
    with TemporaryDirectory() as temp_dir:
        test_data = simulate_argparse(['dryrun', ini_folder, temp_dir])
        imagesort.main(test_data)
        assert reference_report == parse_and_edit_html(os_path_join(temp_dir, 'DryRun report.html'))


def test_dryrun_mode_with_creating_target_folder(set_up: fixture, ini_folder: fixture,
                                                 reference_report: fixture, simulate_argparse: fixture,
                                                 parse_and_edit_html: fixture):
    """Test of dryrun mode with creating of the target folder."""
    with TemporaryDirectory() as temp_dir:
        test_target_folder = os_path_join(temp_dir, 'new folder', 'target folder')
        test_data = simulate_argparse(['dryrun', ini_folder, test_target_folder])
        imagesort.main(test_data)
        assert reference_report == parse_and_edit_html(os_path_join(test_target_folder, 'DryRun report.html'))


def test_copy_mode(set_up: fixture, ini_folder: fixture, folder_structure: fixture,
                   simulate_argparse: fixture, reference_data: fixture):
    """Test of copy mode."""
    with TemporaryDirectory() as temp_dir:
        test_data = simulate_argparse(['copy', ini_folder, temp_dir])
        imagesort.main(test_data)
        assert reference_data == folder_structure(temp_dir)


def test_copy_mode_with_creating_target_folder(set_up: fixture, ini_folder: fixture,
                                               folder_structure: fixture,
                                               simulate_argparse: fixture, reference_data: fixture):
    """Test of copy mode with creating of the target folder."""
    with TemporaryDirectory() as temp_dir:
        test_target_folder = os_path_join(temp_dir, 'new folder', 'target folder')
        test_data = simulate_argparse(['copy', ini_folder, test_target_folder])
        imagesort.main(test_data)
        assert reference_data == folder_structure(test_target_folder)


def test_move_mode(set_up: fixture, create_initial_folder: fixture, ini_folder: fixture,
                   folder_structure: fixture, simulate_argparse: fixture, reference_data: fixture):
    """Test of move mode."""
    with TemporaryDirectory() as temp_dir:
        first_temp_dir = os_path_join(temp_dir, '1')
        second_temp_dir = os_path_join(temp_dir, '2')
        mkdir(second_temp_dir)
        create_initial_folder(ini_folder, first_temp_dir)
        test_data = simulate_argparse(['move', first_temp_dir, second_temp_dir])
        imagesort.main(test_data)
        assert reference_data == folder_structure(second_temp_dir)


def test_move_mode_with_creating_target_folder(set_up: fixture, create_initial_folder: fixture,
                                               ini_folder: fixture, folder_structure: fixture,
                                               simulate_argparse: fixture, reference_data: fixture):
    """Test of move mode with creating of the target folder."""
    with TemporaryDirectory() as temp_dir:
        first_temp_dir = os_path_join(temp_dir, '1')
        second_temp_dir = os_path_join(temp_dir, 'new folder', 'target folder')
        create_initial_folder(ini_folder, first_temp_dir)
        test_data = simulate_argparse(['move', first_temp_dir, second_temp_dir])
        imagesort.main(test_data)
        assert reference_data == folder_structure(second_temp_dir)


def test_sort_mode(set_up: fixture, create_initial_folder: fixture, ini_folder: fixture,
                   folder_structure: fixture, simulate_argparse: fixture, reference_data: fixture):
    """Test of sort mode."""
    test_data = simulate_argparse(['sort', ini_folder])
    imagesort.main(test_data)
    assert reference_data == folder_structure(ini_folder)
