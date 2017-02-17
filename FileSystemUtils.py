import posixpath

import CopyUtils
import DirectoriesStructures
import FileReader
import FileSystemUtilsLowLevel
import FileWriter
from FatReaderExceptions import *


class RemoveUtils:
    def __init__(self, core, fat_reader_utils):
        self.core = core
        self.low_level_utils = fat_reader_utils.low_level_utils
        self.fat_reader_utils = fat_reader_utils
        self.file_writer = FileWriter.FileWriter(core)

    @property
    def working_directory(self):
        return self.fat_reader_utils.working_directory

    @working_directory.setter
    def working_directory(self, value):
        self.fat_reader_utils.working_directory = value

    def move(self, from_path_obj: FileSystemUtilsLowLevel.PathObject, to_path_obj: FileSystemUtilsLowLevel.PathObject):
        self.file_writer.transfer_file(to_path_obj.path_descriptor, from_path_obj.file_fs_descriptor)
        self.refresh()

    def remove_file(self, path_obj: FileSystemUtilsLowLevel.PathObject, recoverable=True, clean=False):
        self.file_writer.delete_directory_or_file(path_obj.file_fs_descriptor, recoverable, clean)
        self.refresh()

    def remove_directory(self, path_obj: FileSystemUtilsLowLevel.PathObject, force=False, clear=True):
        self._remove_current_directory(path_obj.path_descriptor)
        self.file_writer.delete_directory_or_file(path_obj.file_fs_descriptor, recoverable=False, clean=clear)

    def _remove_current_directory(self, directory_descriptor: DirectoriesStructures.Directory, force=False, clear=True):
        for file_descriptor in directory_descriptor.entries():
            if file_descriptor.attributes.directory:
                next_directory_descriptor = self.low_level_utils.parse_directory_descriptor(
                    file_descriptor.data_cluster)
                self._remove_current_directory(next_directory_descriptor, force, clear)
                self.file_writer.delete_directory_or_file(file_descriptor, recoverable=False, clean=clear)
            else:
                self.file_writer.delete_directory_or_file(file_descriptor, recoverable=False, clean=clear)

    def rename(self, path_obj: FileSystemUtilsLowLevel.PathObject, new_name):
        self.file_writer.rename(new_name, path_obj.parent_descriptor, path_obj.file_fs_descriptor)
        self.refresh()

    def refresh(self):
        pass


class FileSystemUtils:
    def __init__(self, core, fat_reader_utils):
        self.core = core
        self.low_level_utils = fat_reader_utils.low_level_utils
        self.fat_reader_utils = fat_reader_utils
        self.file_writer = FileWriter.FileWriter(core)
        self.file_reader = FileReader.DataParser(core)

    @property
    def working_directory(self):
        return self.fat_reader_utils.working_directory

    @working_directory.setter
    def working_directory(self, value):
        self.fat_reader_utils.working_directory = value

    def change_directory(self, path_obj: FileSystemUtilsLowLevel.PathObject):
        self.working_directory = path_obj.path_descriptor

    def new_directories(self, path_obj: FileSystemUtilsLowLevel.PathObject):
        next_path = path_obj.raw_path
        last_existing_dir = path_obj.raw_path_start_directory
        status = False
        start_clusters = []
        while not status:
            output = self.low_level_utils.get_directory_descriptor(next_path, last_existing_dir)
            last_existing_dir, status, stop_number = output
            path_parts = next_path.split('/')
            start_cluster = self.file_writer.new_file(path_parts[stop_number], "d", last_existing_dir)
            start_clusters.append((start_cluster, path_parts[stop_number]))
            last_existing_dir = self.low_level_utils.parse_directory_descriptor(start_cluster)
            next_path = posixpath.normpath(posixpath.join('', *path_parts[stop_number+1:]))
            if next_path is '':
                status = True
        return start_clusters

    def calculate_directory_path(self):
        return self.low_level_utils.get_canonical_path(self.working_directory)

    def ls(self, path_obj: FileSystemUtilsLowLevel.PathObject, long=False, all=False, recursive=False):
        if recursive and path_obj.is_directory:
            yield self.get_directory_information(path_obj, long, all)
            for dir_ in path_obj.path_descriptor.get_directories_sources():
                if dir_.name not in [".", ".."]:
                    yield from self.ls(self.low_level_utils.path_parser(dir_.name, path_obj.path_descriptor), long, all,
                                       recursive)
        else:
            yield self.get_directory_information(path_obj, long, all)

    def get_directory_information(self, path_obj: FileSystemUtilsLowLevel.PathObject, long=False, all=False):
        info = ''
        if path_obj.is_file:
            info = path_obj.path_descriptor.to_string(long, all=True)
        else:
            info = "\n".join(
                x for x in [files.to_string(long, all) for files in path_obj.path_descriptor.entries_list] if x != '')
        return self.low_level_utils.get_canonical_path(
            path_obj.path_descriptor if path_obj.is_directory else path_obj.parent_descriptor) + '\n' + info

    def cat_data(self, path_obj: FileSystemUtilsLowLevel.PathObject, byte=False, text=True, encoding="cp866"):
        addr = path_obj.path_descriptor.data_cluster
        if byte:
            for data_part in self.file_reader.parse_non_buffer(addr):
                yield data_part
        else:
            for data_part in self.file_reader.parse_non_buffer(addr):
                try:
                    yield data_part.decode(encoding)
                except UnicodeEncodeError:
                    raise BadEncodingSelected()


class FatReaderUtils:
    def __init__(self, core):
        self.core = core
        self.low_level_utils = FileSystemUtilsLowLevel.FileSystemUtilsLowLevel(core)
        self._working_directory = self.low_level_utils.parse_directory_descriptor(2)
        self.file_system_utils = FileSystemUtils(core, self)
        self.remove_utils = RemoveUtils(core, self)
        self.copy_utils = CopyUtils.CopyUtils(core, self)

    @property
    def working_directory(self):
        return self._working_directory

    @working_directory.setter
    def working_directory(self, value):
        self._working_directory = value

    def ls(self, path, long=False, all=False, recursive=False):
        if path == '':
            path = "./"
        self.refresh()
        path_obj = self.low_level_utils.path_parser(path, self.working_directory)
        if not path_obj.is_exist and not (not path_obj.is_file and path_obj.parent_exist):
            raise InvalidPathException()
        for data in self.file_system_utils.ls(path_obj, long, all, recursive):
            print(data)
        pass

    def cp(self, path_from, path_to):
        path_obj_from = self.low_level_utils.path_parser(path_from, self.working_directory)
        path_obj_to = self.low_level_utils.path_parser(path_to, self.working_directory)
        if not path_obj_from.is_exist or path_obj_to.is_file:
            raise InvalidPathException()
        self.copy_utils.copy_in_image(path_obj_from, path_obj_to)
        pass

    def cpf(self, path_from_os, path_to):
        path_obj_to = self.low_level_utils.path_parser(path_to, self.working_directory)
        if path_obj_to.is_file:
            raise InvalidPathException()
        self.copy_utils.copy_from_os(path_from_os, path_obj_to)

    def cpt(self, path_from, path_to_os):
        path_obj_from = self.low_level_utils.path_parser(path_from, self.working_directory)
        if not path_obj_from.is_exist:
            raise InvalidPathException()
        self.copy_utils.copy_to_os(path_obj_from, path_to_os)
        pass

    def rm(self, path, clear=False):
        path_obj = self.low_level_utils.path_parser(path, self.working_directory)
        if not path_obj.is_exist:
            raise FileNotFoundError()
        if path_obj.is_directory:
            raise IsADirectoryError()
        self.remove_utils.remove_file(path_obj, recoverable=True, clean=clear)
        pass

    def rmdir(self, path, force=False, clear=False):
        path_obj = self.low_level_utils.path_parser(path, self.working_directory)
        if not path_obj.is_exist:
            raise FileNotFoundError()
        if path_obj.is_file:
            raise FileExistsError()
        self.remove_utils.remove_directory(path_obj, force=force, clear=clear)
        pass

    def cat(self, path, byte=False, text=True, encoding="cp866"):
        path_obj = self.low_level_utils.path_parser(path, self.working_directory)
        if not path_obj.is_exist:
            raise NotAFileException()
        if path_obj.is_directory:
            raise NotAFileException()
        for data in self.file_system_utils.cat_data(path_obj, byte, ):
            print(data)
        pass

    def cd(self, path):
        path_obj = self.low_level_utils.path_parser(path, self.working_directory)
        if not path_obj.is_exist:
            raise NotAFileException()
        if path_obj.is_file:
            raise NotAFileException()
        self.file_system_utils.change_directory(path_obj)

    def md(self, path):
        path_obj = self.low_level_utils.path_parser(path, self.working_directory)
        if path_obj.is_exist:
            raise FileAlreadyExistException()
        self.file_system_utils.new_directories(path_obj)

    def pwd(self):
        print(self.file_system_utils.calculate_directory_path())

    def move(self, path_from, path_to):
        path_obj_from = self.low_level_utils.path_parser(path_from, self.working_directory)
        path_obj_to = self.low_level_utils.path_parser(path_to, self.working_directory)
        if not path_obj_from.is_exist or path_obj_to.is_file:
            raise InvalidPathException()
        self.remove_utils.move(path_obj_from, path_obj_to)

    def refresh(self):
        self.working_directory = self.low_level_utils.parse_directory_descriptor(self.working_directory.data_cluster)
