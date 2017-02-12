import FileEntryCollector
import FileReader
import os
import os.path
from functools import partial
import stat


class OSAttributes:
    pass


class WinAttributes:
    pass


class OSDirectoryReader:
    def __init__(self, cluster_size):
        self.cluster_size = cluster_size

    def all_files_stream(self, path):
        for name in os.listdir(path):
            file_path = os.path.join(path, name)
            if not (os.path.islink(file_path) or os.path.ismount(file_path)):
                yield file_path

    def files_stream(self, path):
        files = self.all_files_stream(path)
        for file_path in files:
            if os.path.isfile(file_path):
                yield file_path

    def dirs_stream(self, path):
        files = self.all_files_stream(path)
        for file_path in files:
            if os.path.isdir(file_path):
                yield file_path

    def file_descriptor_stream(self, path):
        file_paths = self.files_stream(path)
        for file_path in file_paths:
            f = open(file_path, "rb")
            yield f
            f.close()

    def read_file(self, file_path):
        f = open(file_path, "rb")
        return f

    def file_data_stream(self, file_descriptor):
        f = file_descriptor
        data_stream = iter(partial(f.read, self.cluster_size), b'')
        for data_chunk in data_stream:
            yield data_chunk


class OSDirectoryWriter:
    def __init__(self, cluster_size):
        self.cluster_size = cluster_size

    def create_dir(self, path, mode=0o777):
        os.makedirs(path, mode)

    def crete_file(self, path):
        head, tail = os.path.split(path)
        os.chdir(head)
        f = open(tail, "xb")
        f.close()
        f = open(tail, "r+b")
        return f

    def write_data_to_file(self, file_descriptor, data_stream):
        for num, data_chunk in enumerate(data_stream):
            file_descriptor.seek(self.cluster_size * num)
            file_descriptor.write(data_chunk)
        file_descriptor.close()

    def create_dirs(self, path, names_stream):
        for name in names_stream:
            dir_path = os.path.join(path, name)
            self.create_dir(dir_path)
