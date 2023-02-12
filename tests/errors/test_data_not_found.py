class TestDataNotFoundError(Exception):
    __slots__ = ['__test_data_name']

    def __init__(self, test_data_name):
        self.__test_data_name = test_data_name
        self.__description = f"""Error! The testing couldn't be started:\n {self.__test_data_name} not found"""

    def __str__(self):
        return f'{self.__description}'
