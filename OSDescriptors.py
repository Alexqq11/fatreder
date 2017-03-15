import os
import os.path

from functools import partial


class FileDescriptor:  # todo think about use __slots__
    def __init__(self, path):
        path = os.path.normpath(path)
        path = os.path.abspath(path)
        self._file_path = path
        directory, name = os.path.split(path)
        self._parent_directory_path = directory
        self._name = name
        self._exist = os.path.exists(path)
        self._directory = None
        self._cluster_size = 512  # TODO THINK ABOUT CHANGES
        if self._exist:
            self._directory = os.path.isdir(path)

    @property
    def name(self):
        return self._name

    @property
    def directory(self):
        return self._directory

    @property
    def file_path(self):
        return self._file_path

    def data_stream(self):
        if not self._exist or self._directory:
            raise Exception("try to accesses not file object data")
        f = open(self._file_path, "rb")
        data_stream = iter(partial(f.read, self._cluster_size), b'')
        for data_chunk in data_stream:
            yield data_chunk

    def write_data_into_file(self, size, data_stream):
        size += 0
        if not self._exist or self._directory:
            raise Exception("try to accesses not file object data")
        file = open(self._file_path, "r+b")
        for num, data_chunk in enumerate(data_stream):
            file.seek(self._cluster_size * num)
            file.write(data_chunk)
        file.close()

    def create_in_os(self, is_dir=False):
        if is_dir:
            os.makedirs(self._file_path)
        else:
            os.makedirs(self._parent_directory_path)
            f = open(self._file_path, "xb")
            f.close()
        self._exist = True
        self._directory = is_dir

    def calculate_size_on_disk(self):
        size_in_bytes = 0  # todo think about data consistency in class when we call this method
        if self._directory:
            directory = DirectoryDescriptor(self._file_path)
            size_in_bytes += directory.calculate_size_on_disk()
        size_in_bytes += os.path.getsize(self._file_path)
        return size_in_bytes

    def update_size_in_descriptor(self):
        pass

    def flush(self):
        pass


class DirectoryDescriptor:
    def __init__(self, path):
        path = os.path.normpath(path)
        path = os.path.abspath(path)
        if not os.path.isdir(path):
            raise Exception("Trying to create directory descriptor from file or not exist object")
        self._file_path = path
        directory, name = os.path.split(path)
        self._parent_directory_path = directory
        self._name = name
        self._entries = [FileDescriptor(x) for x in self.files_paths_stream()]

    def calculate_size_on_disk(self):
        size = 0
        for x in self.entries():
            size += x.calculate_size_on_disk()
        return size

    def files_paths_stream(self):
        for name in os.listdir(self._file_path):
            file_path = os.path.join(self._file_path, name)
            if not (os.path.islink(file_path) or os.path.ismount(file_path)):
                yield file_path

    def make_directory(self, name):
        new_dir = FileDescriptor(os.path.join(self._file_path, name))
        new_dir.create_in_os(is_dir=True)
        self._entries.append(new_dir)
        return new_dir

    def make_file(self, name):
        new_file = FileDescriptor(os.path.join(self._file_path, name))
        new_file.create_in_os()
        self._entries.append(new_file)
        return new_file

    def entries(self):
        for x in self._entries:
            if x.name not in ['.', '..']:
                yield x

    def parse_descriptors(self, file_descriptor, is_image_descriptor=False):
        to_directory = self.make_directory(file_descriptor.name)
        to_directory = DirectoryDescriptor(to_directory.file_path)
        if is_image_descriptor:
            from_directory = file_descriptor.core.file_system_utils.low_level_utils.parse_directory_descriptor(
                file_descriptor.data_cluster)
        else:
            from_directory = DirectoryDescriptor(file_descriptor.file_path)
        return to_directory, from_directory

    def copy(self, file_descriptor, is_image_descriptor=False):
        if file_descriptor.directory:
            to_directory, from_directory = self.parse_descriptors(file_descriptor, is_image_descriptor)
            for descriptor in from_directory.entries():
                to_directory.copy(descriptor)
        else:
            descriptor = self.make_file(file_descriptor.name)
            size = file_descriptor.calculate_size_on_disk()
            descriptor.write_data_into_file(size, file_descriptor.data_stream())
