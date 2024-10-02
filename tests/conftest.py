import pytest
from pytest import fixture

from imagesort import delete_folder


pytest_plugins = 'tests.fixtures'


@pytest.fixture
def set_up(ini_folder: fixture, temp_folder: fixture, create_initial_folder: fixture):
    create_initial_folder(temp_folder, ini_folder)
    yield
    delete_folder(ini_folder)
