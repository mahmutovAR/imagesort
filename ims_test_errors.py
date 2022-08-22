class TestFailedError(Exception):
    __slots__ = ['__test_name']

    def __init__(self, test_name):
        self.__test_name = test_name
        self.__description = f'Error! Test {test_name} failed.'

    def __str__(self):
        return f'{self.__description}'
