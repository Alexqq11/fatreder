
import os
import os.path

import DirectoryDescriptor
import FatReaderExceptions
import FileReader
import FileSystemUtilsLowLevel
import IOmodule

"""
class CopyUtils:
    def __init__(self, core, fat_reader_utils):
        self.core = core
        self.low_level_utils = fat_reader_utils.low_level_utils
        self.fat_reader_utils = fat_reader_utils
        self.file_writer = FileWriter.FileWriter(core)
        self.file_reader = FileReader.DirectoryParser()
        self.file_reader.init_core(core)

    @property
    def working_directory(self):
        return self.fat_reader_utils.working_directory

    @working_directory.setter
    def working_directory(self, value):
        self.fat_reader_utils.working_directory = value

    def refresh(self):
        pass

    def make_dirs_obj(self, path_obj):
        start_clusters = self.core.file_system_utils.new_directories(path_obj)
        return start_clusters

    def make_dir(self, file_name, attr, destination_dir):
        start_cluster = self.file_writer.new_file(file_name, attr, destination_dir)
        return start_cluster

    def copy_in_image(self, from_path_obj: FileSystemUtilsLowLevel.PathObject,
                      to_path_obj: FileSystemUtilsLowLevel.PathObject):
        # todo resolve name conflicts
        if from_path_obj.is_file:
            self.file_writer.copy_file(to_path_obj.path_descriptor, from_path_obj.file_fs_descriptor)
        else:
            self.make_dirs_obj(to_path_obj)  # todo be shure if we have dirs it doesn't make it again
            to_path_obj = self.low_level_utils.path_parser(to_path_obj.raw_path, to_path_obj.raw_path_start_directory)
            self._write_copy_data(*self._calc_new_dirs(from_path_obj.file_fs_descriptor, to_path_obj.path_descriptor))
        self.refresh()

    def _calc_new_dirs(self, file_descriptor, directory_descriptor: DirectoriesStructures.Directory):
        start_cluster = self.make_dir(file_descriptor.name, file_descriptor.attr_string, directory_descriptor)
        new_to_dir = self.low_level_utils.parse_directory_descriptor(start_cluster)
        new_from_dir = self.low_level_utils.parse_directory_descriptor(file_descriptor.data_cluster)
        return new_from_dir, new_to_dir

    def _write_copy_data(self, from_dir: DirectoriesStructures.Directory, to_dir: DirectoriesStructures.Directory):
        for files in from_dir.get_files_sources():
            self.file_writer.copy_file(to_dir, files)
        for dir_file_descriptor in from_dir.get_files_sources():
            self._write_copy_data(*self._calc_new_dirs(dir_file_descriptor, to_dir))

    @staticmethod
    def _check_os_path(os_path):
        os_path = os.path.normpath(os_path)
        if os.path.isfile(os_path) or os.path.ismount(os_path):
            raise FatReaderExceptions.InvalidPathException()
        return os_path

    def _from_os_write_copy_data(self, os_path, destination_dir):
        os_files = IOmodule.OSDirectoryReader(self.core.fat_bot_sector.cluster_size)
        for file in os_files.files_stream(os_path):
            head, tail = os.path.split(file)
            data_cluster = self.file_writer.new_file(tail, "", destination_dir)
            self.file_writer.extend_file(data_cluster, os.path.getsize(file))
            clusters_offsets = self.file_writer.get_file_allocation_offsets(data_cluster)
            fd = os_files.read_file(file)
            for offset, data in zip(clusters_offsets, os_files.file_data_stream(fd)):
                self.core.image_reader.set_data_global(offset, data)
            fd.close()
        for dirs in os_files.dirs_stream(os_path):
            head, tail = os.path.split(dirs)
            data_cluster = self.file_writer.new_file(tail, "d", destination_dir)
            nex_dir_to_write = self.low_level_utils.parse_directory_descriptor(data_cluster)
            self._from_os_write_copy_data(dirs, nex_dir_to_write)

    def copy_from_os(self, os_path, image_path_obj: FileSystemUtilsLowLevel.PathObject):
        os_path = self._check_os_path(os_path)
        self.make_dirs_obj(image_path_obj)  # todo be shure if we have dirs it doesn't make it again
        image_path_obj = self.low_level_utils.path_parser(image_path_obj.raw_path,
                                                          image_path_obj.raw_path_start_directory)
        self._from_os_write_copy_data(os_path, image_path_obj.path_descriptor)

    def copy_to_os(self, image_path_obj: FileSystemUtilsLowLevel.PathObject, os_path):
        os_files = IOmodule.OSDirectoryWriter(self.core.fat_bot_sector.cluster_size)
        os_files.create_dir(os_path)
        if image_path_obj.is_file:
            f = os_files.crete_file(os.path.join(os_path, image_path_obj.file_name))
            os_files.write_data_to_file(f, self.file_reader.parse_non_buffer(
                image_path_obj.file_fs_descriptor.data_cluster))
            f.close()
        else:
            self._write_copy_data_to_os(image_path_obj.path_descriptor, os_path)

    def move(self, from_path_obj: FileSystemUtilsLowLevel.PathObject, to_path_obj: FileSystemUtilsLowLevel.PathObject):
        # self.file_writer.transfer_file(to_path_obj.path_descriptor, from_path_obj.file_fs_descriptor)
        self.refresh()
    def _write_copy_data_to_os(self, from_dir: DirectoriesStructures.Directory, os_path):
        os_files = IOmodule.OSDirectoryWriter(self.core.fat_bot_sector.cluster_size)
        for file in from_dir.get_files_sources():
            f = os_files.crete_file(os.path.join(os_path, file.name))
            os_files.write_data_to_file(f, self.file_reader.parse_non_buffer(file.data_cluster))
            f.close()
        for dir_ in from_dir.get_files_sources():
            dir_path = os.path.join(os_path, dir_.name)
            os_files.create_dir(dir_path)
            from_dir = self.low_level_utils.parse_directory_descriptor(dir_.data_cluster)
            self._write_copy_data_to_os(from_dir, dir_path)
"""