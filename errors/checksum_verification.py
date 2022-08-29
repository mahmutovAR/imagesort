class ChecksumVerificationError(Exception):
    def __init__(self):
        self.__description = 'Error! Checksum verification completed with an error. ' \
                             'Deleting of the initial files canceled.'

    def __str__(self):
        return f'{self.__description}'
