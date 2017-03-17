class FatReaderException(Exception):
    def __init__(self, msg=None):
        self._message = None
        if msg:
            self._message = msg
        else:
            self._message = "Fat Reader unexpected error"
        print(self._message)

    pass

    @property
    def error_message(self):
        return self._message

class CoreNotInitedError(FatReaderException):
    def __init__(self, msg=None):
        self._message = None
        if msg:
            self._message = msg
        else:
            self._message = "This class needs to Init app core"
        print(self._message)
    pass

    @property
    def error_message(self):
        return self._message

class BadEncodingSelected(FatReaderException):
    def __init__(self, msg=None):
        self._message = None
        if msg:
            self._message = msg
        else:
            self._message = "BadEncodingSelected"
        print(self._message)

    pass

    @property
    def error_message(self):
        return self._message


class InvalidCommandException(FatReaderException):
    def __init__(self, msg=None):
        self._message = None
        if msg:
            self._message = msg
        else:
            self._message = "Invalid Command"
        print(self._message)

    pass

    @property
    def error_message(self):
        return self._message

class UnExpectedParsingError(FatReaderException):
    def __init__(self, msg=None):
        self._message = None
        if msg:
            self._message = msg
        else:
            self._message = "Unexpected Error"
        print(self._message)
    pass

    @property
    def error_message(self):
        return self._message
class UnExpectedCriticalError(FatReaderException):
    def __init__(self, msg=None):
        self._message = None
        if msg:
            self._message = msg
        else:
            self._message = "Unexpected Error"
        print(self._message)
    pass

    @property
    def error_message(self):
        return self._message

class InvalidPathException(FatReaderException):
    def __init__(self, msg=None):
        self._message = None
        if msg:
            self._message = msg
        else:
            self._message = "Invalid path"
        print(self._message)

    pass

    @property
    def error_message(self):
        return self._message


class AllocationMemoryOutException(FatReaderException):
    def __init__(self, msg=None):
        self._message = None
        if msg:
            self._message = msg
        else:
            self._message = "No free memory"
        print(self._message)

    pass

    @property
    def error_message(self):
        return self._message


class DirectoryDoesNotExistException(FatReaderException):
    def __init__(self, msg=None):
        self._message = None
        if msg:
            self._message = msg
        else:
            self._message = "Directory doesn't exist"
        print(self._message)

    pass

    @property
    def error_message(self):
        return self._message


class FileAlreadyExistException(FatReaderException):
    def __init__(self, msg=None):
        self._message = None
        if msg:
            self._message = msg
        else:
            self._message = "File already exist"
        print(self._message)

    pass

    @property
    def error_message(self):
        return self._message


class NotADirectoryException(FatReaderException):
    def __init__(self, msg=None):
        self._message = None
        if msg:
            self._message = msg
        else:
            self._message = "Not a Directory"
        print(self._message)

    pass

    @property
    def error_message(self):
        return self._message


class NotAFileException(FatReaderException):
    def __init__(self, msg=None):
        self._message = None
        if msg:
            self._message = msg
        else:
            self._message = "Not a File"
        print(self._message)

    pass

    @property
    def error_message(self):
        return self._message


class ZeroSizeAllocationException(FatReaderException):
    def __init__(self, msg=None):
        self._message = None
        if msg:
            self._message = msg
        else:
            self._message = "Zero size allocation expected"
        print(self._message)

    pass

    @property
    def error_message(self):
        return self._message
