import IOmodule
import FatReaderExceptions
import posixpath
import os
import os.path
import DirectoriesStructures

class CopyUtils:
    def __init__(self):
        pass

    def copy_directory(self, from_path, to_path):
        file_dir, file_source, file_name = self._pre_operation_processing(from_path)
        if not file_source.attributes.directory:
            raise FatReaderExceptions.NotADirectoryException()
        destination_dir, error = self._change_directory(to_path)
        if error:
            raise FatReaderExceptions.InvalidPathException()
        file_source = self._file_exist_name_file_source_path(destination_dir, file_source)
        start_cluster = self.new_directory(None, "", CopyNewDirIMetaData(destination_dir, file_source))
        to_dir = self.parse_directory(start_cluster)
        from_dir = self.parse_directory(file_source.data_cluster)
        self._write_copy_data(from_dir, to_dir)
        self.refresh()

    def _write_copy_data(self, from_dir: DirectoriesStructures.Directory, to_dir: DirectoriesStructures.Directory):
        for files in from_dir.get_files_sources():
            self.file_writer.copy_file(to_dir, files)
        for dirs in from_dir.get_files_sources():
            start_cluster = self.new_directory(None, "", CopyNewDirIMetaData(to_dir, dirs))
            new_to_dir = self.parse_directory(start_cluster)
            new_from_dir = self.parse_directory(dirs.data_cluster)
            self._write_copy_data(new_from_dir, new_to_dir)

    def _check_os_path(self, os_path):
        os_path = os.path.normpath(os_path)
        if os.path.isfile(os_path) or os.path.ismount(os_path):
            raise FatReaderExceptions.InvalidPathException()
        return os_path

    def make_dirs(self, path):
        posixpath.normpath(path)
        directory, head_exist = self._change_directory(path)
        if head_exist:
            raise FatReaderExceptions.FileAlreadyExistException()

    def _check_image_path_for_os_copy(self, image_path):
        head, tail, is_dir = self.__path_parser(image_path)
        if not is_dir:
            raise FatReaderExceptions.InvalidPathException()
        return posixpath.join(head, tail)

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
            nex_dir_to_write = self.parse_directory(data_cluster)
            self._from_os_write_copy_data(dirs, nex_dir_to_write)

    def copy_from_os(self, os_path, image_path):
        os_path = self._check_os_path(os_path)
        image_path = self._check_image_path_for_os_copy(image_path)
        # os_files = IOmodule.OSDirectoryReader(self.core.fat_bot_sector.cluster_size)
        destination_dir, sst = self._change_directory(image_path)
        self._from_os_write_copy_data(os_path, destination_dir)

    def copy_to_os(self, image_path, os_path):
        head, tail, is_dir = self.__path_parser(image_path)
        os_files = IOmodule.OSDirectoryWriter(self.core.fat_bot_sector.cluster_size)
        os_files.create_dir(os_path)
        if not is_dir:
            src_dir, sst = self._change_directory(head)
            src_dsc_file = src_dir.find(tail, "by_name")
            f = os_files.crete_file(os.path.join(os_path, tail))
            os_files.write_data_to_file(f, self.file_reader.parse_non_buffer(src_dsc_file.data_cluster))
            f.close()
        else:
            src_dir, sst = self._change_directory(posixpath.join(head, tail))
            self._write_copy_data_to_os(src_dir, os_path)

    def _write_copy_data_to_os(self, from_dir: DirectoriesStructures.Directory, os_path):
        os_files = IOmodule.OSDirectoryWriter(self.core.fat_bot_sector.cluster_size)
        for file in from_dir.get_files_sources():
            # self.file_writer.copy_file(to_dir, files)
            f = os_files.crete_file(os.path.join(os_path, file.name))
            os_files.write_data_to_file(f, self.file_reader.parse_non_buffer(file.data_cluster))
            f.close()
        for dir in from_dir.get_files_sources():
            dir_path = os.path.join(os_path, dir.name)
            os_files.create_dir(dir_path)
            from_dir = self.parse_directory(dir.data_cluster)
            self._write_copy_data_to_os(from_dir, dir_path)

class CopyNewDirIMetaData:
    def __init__(self, destination_dir, file_source):
        self._file_source = file_source
        self._destination_dir = destination_dir

    @property
    def destination_dir(self):
        return self._destination_dir

    @property
    def file_source(self):
        return self._file_source