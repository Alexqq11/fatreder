import posixpath
import OSDescriptors
import FileReader
import FileSystemUtilsLowLevel
import os
import ctypes

from FatReaderExceptions import *


class RemoveUtils:
    def __init__(self, core, fat_reader_utils):
        self.core = core
        self.low_level_utils = fat_reader_utils.low_level_utils
        self.fat_reader_utils = fat_reader_utils

    @property
    def working_directory(self):
        return self.fat_reader_utils.working_directory

    @working_directory.setter
    def working_directory(self, value):
        self.fat_reader_utils.working_directory = value

    def free_space_avalible(self, path, is_image=True):
        if is_image:
            return self.core.fat_table.calculate_free_space()
        else:
            if os.name == 'nt':
                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(path), None, None,
                                                           ctypes.pointer(free_bytes))
                return free_bytes.value
            else:
                st = os.statvfs(path)
                return st.f_bavail * st.f_frsize

    def remove_file(self, path_obj: FileSystemUtilsLowLevel.PathObject, recoverable=True, clean=False):
        path_obj.path_descriptor.delete()
        self.refresh()

    @staticmethod
    def remove_directory(path_obj: FileSystemUtilsLowLevel.PathObject, force=False, clear=True):
        path_obj.path_descriptor.delete()

    @staticmethod
    def delete(path_obj: FileSystemUtilsLowLevel.PathObject):
        path_obj.file_fs_descriptor.delete()

    def rename(self, path_obj: FileSystemUtilsLowLevel.PathObject, new_name):
        path_obj.parent_descriptor.rename_file(path_obj.file_name, new_name)
        self.refresh()

    def copy(self, path_obj_to: FileSystemUtilsLowLevel.PathObject, path_obj_from: FileSystemUtilsLowLevel.PathObject,
             is_image_descriptor=None):
        if is_image_descriptor is None:
            raise UnExpectedCriticalError("Working option not validated")

        size_to_copy = path_obj_from.file_fs_descriptor.calculate_size_on_disk()
        if is_image_descriptor:
            free_space = self.free_space_avalible(path_obj_to.file_directory_path, is_image=False)
        else:
            free_space = self.free_space_avalible(path_obj_to.file_directory_path)
        if free_space < size_to_copy:
            raise AllocationMemoryOutException("No enough free space avalible in the cp destination place")

        path_obj_to.path_descriptor.copy(path_obj_from.file_fs_descriptor, is_image_descriptor)

    @staticmethod
    def move(path_obj_to: FileSystemUtilsLowLevel.PathObject, path_obj_from: FileSystemUtilsLowLevel.PathObject):
        path_obj_to.path_descriptor.move(path_obj_from.file_fs_descriptor)

    def refresh(self):
        pass


class FileSystemUtils:
    def __init__(self, core, fat_reader_utils):
        self.core = core
        self.low_level_utils = fat_reader_utils.low_level_utils
        self.fat_reader_utils = fat_reader_utils
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
            start_cluster = last_existing_dir.make_directory(path_parts[stop_number])
            start_clusters.append((start_cluster, path_parts[stop_number]))
            last_existing_dir = self.low_level_utils.parse_directory_descriptor(start_cluster)
            next_path = posixpath.normpath(posixpath.join('', *path_parts[stop_number + 1:]))
            if next_path is '.' or next_path is '':
                status = True
        return start_clusters

    def calculate_directory_path(self):
        return self.low_level_utils.get_canonical_path(self.working_directory)

    def ls(self, path_obj: FileSystemUtilsLowLevel.PathObject, long=False, all_files=False, recursive=False):
        if recursive and path_obj.is_directory:
            yield self.get_directory_information(path_obj, long, all_files)
            for dir_ in path_obj.path_descriptor.directories_sources():
                if dir_.name not in [".", ".."]:
                    yield from self.ls(self.low_level_utils.path_parser(dir_.name, path_obj.path_descriptor),
                                       long, all_files, recursive)
        else:
            yield self.get_directory_information(path_obj, long, all_files)

    def get_directory_information(self, path_obj: FileSystemUtilsLowLevel.PathObject, long=False, all_files=False):
        if path_obj.is_file:
            info = path_obj.path_descriptor.to_string(long, all_files=True)
        else:
            info = "\n".join(
                x for x in [files.to_string(long, all) for files in path_obj.path_descriptor.entries_list] if x != '')
        return self.low_level_utils.get_canonical_path(
            path_obj.path_descriptor if path_obj.is_directory else path_obj.parent_descriptor) + '\n' + info

    def cat_data(self, path_obj: FileSystemUtilsLowLevel.PathObject, byte=False, text=True, encoding="cp866"):
        data_cluster = path_obj.path_descriptor.data_cluster
        if byte:
            for data_part in self.file_reader.parse_non_buffer(data_cluster):
                yield data_part
        else:
            for data_part in self.file_reader.parse_non_buffer(data_cluster):
                try:
                    yield data_part.decode(encoding)
                except UnicodeEncodeError:
                    raise BadEncodingSelected()

    @staticmethod
    def size(path_obj: FileSystemUtilsLowLevel.PathObject):
        print(path_obj.file_fs_descriptor.calculate_size_on_disk())


class FatReaderUtils:
    def __init__(self, core):
        self.core = core
        self.low_level_utils = FileSystemUtilsLowLevel.FileSystemUtilsLowLevel(core)
        self._working_directory = self.low_level_utils.parse_directory_descriptor(
            self.core.fat_boot_sector.root_directory_cluster)
        self.file_system_utils = FileSystemUtils(core, self)
        self.remove_utils = RemoveUtils(core, self)
        # self.copy_utils = CopyUtils.CopyUtils(core, self)

    @property
    def working_directory(self):
        return self._working_directory

    @working_directory.setter
    def working_directory(self, value):
        self._working_directory = value

    def ls(self, path, long=False, all_files=False, recursive=False):
        if path == '':
            path = "./"
        self.refresh()
        path_obj = self.low_level_utils.path_parser(path, self.working_directory)
        if not path_obj.is_exist and not (not path_obj.is_file and path_obj.parent_exist):
            raise InvalidPathException()
        for data in self.file_system_utils.ls(path_obj, long, all_files, recursive):
            print(data)
        pass

    def cp(self, path_from, path_to):  # todo check_sub_dir
        path_obj_from = self.low_level_utils.path_parser(path_from, self.working_directory)
        path_obj_to = self.low_level_utils.path_parser(path_to, self.working_directory)
        if not path_obj_from.is_exist or path_obj_to.is_file:
            raise InvalidPathException()
        self.remove_utils.copy(path_obj_to, path_obj_from, is_image_descriptor=True)
        pass

    def size(self, path):
        path_obj_to = self.low_level_utils.path_parser(path, self.working_directory)
        if not path_obj_to.is_exist:
            raise InvalidPathException()
        self.file_system_utils.size(path_obj_to)

    def cpf(self, path_from_os, path_to):
        path_obj_to = self.low_level_utils.path_parser(path_to, self.working_directory)
        path_obj_from = OSDescriptors.PathObject(path_from_os)
        if path_obj_to.is_file or not path_obj_from.is_exist:
            raise InvalidPathException()
        self.remove_utils.copy(path_obj_to, path_obj_from, is_image_descriptor=False)
        # self.copy_utils.copy_from_os(path_from_os, path_obj_to)

    def cpt(self, path_from, path_to_os):
        path_obj_from = self.low_level_utils.path_parser(path_from, self.working_directory)
        path_obj_to = OSDescriptors.PathObject(path_to_os)
        if not path_obj_from.is_exist or path_obj_to.is_file:
            raise InvalidPathException()
        if not path_obj_to.is_exist:
            path_obj_to.create()
        self.remove_utils.copy(path_obj_to, path_obj_from, is_image_descriptor=True)
        # self.copy_utils.copy_to_os(path_obj_from, path_to_os)
        pass

    def rm(self, path, clear=False):
        path_obj = self.low_level_utils.path_parser(path, self.working_directory)
        if not path_obj.is_exist:
            raise InvalidPathException("file not found")
        if path_obj.is_directory:
            raise InvalidPathException("Use rmdir to delete that directory")
        self.remove_utils.delete(path_obj)
        pass

    def rmdir(self, path, force=False, clear=False):
        path_obj = self.low_level_utils.path_parser(path, self.working_directory)
        if not path_obj.is_exist:
            raise InvalidPathException("file not found")
        if path_obj.is_file:
            raise InvalidPathException("Use rm to delete that file")
        self.remove_utils.delete(path_obj)
        pass

    def cat(self, path, byte=False, text=True, encoding="cp866"):
        path_obj = self.low_level_utils.path_parser(path, self.working_directory)
        if not path_obj.is_exist:
            raise InvalidPathException("file not found")
        if path_obj.is_directory:
            raise InvalidPathException("You can't read directory content by cat, use ls")
        for data in self.file_system_utils.cat_data(path_obj, byte, ):
            print(data)
        pass

    def cd(self, path):
        path_obj = self.low_level_utils.path_parser(path, self.working_directory)
        if not path_obj.is_exist:
            raise InvalidPathException("directory not found")
        if path_obj.is_file:
            raise InvalidPathException("you can't go into file, select directory")
        self.file_system_utils.change_directory(path_obj)

    def md(self, path):
        path_obj = self.low_level_utils.path_parser(path, self.working_directory)
        if path_obj.is_exist:
            raise FileAlreadyExistException()
        self.file_system_utils.new_directories(path_obj)

    def pwd(self):
        print(self.file_system_utils.calculate_directory_path())

    def move(self, path_to, path_from):  # todo check sub_dir
        path_obj_from = self.low_level_utils.path_parser(path_from, self.working_directory)
        path_obj_to = self.low_level_utils.path_parser(path_to, self.working_directory)
        if not path_obj_from.is_exist or path_obj_to.is_file:
            raise InvalidPathException("You trying move not exist directory or move file/directory into existing file")
        self.remove_utils.move(path_obj_to, path_obj_from)

    def rename(self, path, name):
        path_obj_from = self.low_level_utils.path_parser(path, self.working_directory)
        path_obj_to = self.low_level_utils.path_parser(name, self.working_directory)
        if not path_obj_from.is_exist or path_obj_to.is_exist or "/" in name or '\\' in name:
            raise InvalidPathException(
                "Yoy trying rename not existing object or trying to use uncorrect or existing filename ")
        self.remove_utils.rename(path_obj_from, name)

    def refresh(self):
        self.working_directory = self.low_level_utils.parse_directory_descriptor(self.working_directory.data_cluster)
