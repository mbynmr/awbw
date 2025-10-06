class CustomError(Exception):
    def __init__(self, message):
        super().__init__(message)
        # if I want extra arguments, go to https://stackoverflow.com/a/1319675
        # todo just stick in other files? idk
