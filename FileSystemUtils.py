import posixpath
import re
import os
import os.path
import DirectoriesStructures
import FatReaderExceptions
import FileEntryCollector as FeC
import FileReader as FR
import FileWriter as FW
import IOmodule


class FileSystemUtil:
    def __init__(self, core):  #: Core.Core):
        ''' by default working directory is a root directory'''
        self.core = core
        self.file_reader = FR.DataParser(core)
        self.directory_reader = FR.DirectoryParser(core)
        self.file_writer = FW.FileWriter(core)
        self.root_directory_offset = core.fat_bot_sector.root_directory_offset
        self.working_directory = self.directory_reader.nio_parse_directory(self.root_directory_offset)
        self.current_path = '/'

    def calc_cluster_offset(self, cluster_number):
        return self.core.fat_bot_sector.calc_cluster_offset(cluster_number)

    def parse_directory(self, cluster_number):
        return self.directory_reader.nio_parse_directory(self.calc_cluster_offset(cluster_number))

    def cat_data(self, file_name):
        file_dir, file_source, file_name = self._pre_operation_processing(file_name)
        if not file_source.attributes.directory:
            addr = file_source.data_cluster
            for data_part in self.file_reader.parse_non_buffer(addr):
                yield data_part
        else:
            raise FatReaderExceptions.NotAFileException()

    def calculate_directory_path(self):
        return self._calculate_canonical_path(self.working_directory)

    def _calculate_canonical_path(self, directory_descriptor: DirectoriesStructures):
        parent_cluster = directory_descriptor.parent_directory_cluster
        own_cluster = directory_descriptor.data_cluster
        temp_dir = directory_descriptor
        path = '/'
        while not temp_dir.is_root:
            temp_dir = self.parse_directory(parent_cluster)
            # path = '/' + temp_dir.find(own_cluster, 'by_address').name + path
            path = posixpath.join(temp_dir.find(own_cluster, 'by_address').name, path)
            own_cluster = parent_cluster
            parent_cluster = temp_dir.parent_directory_cluster
        return posixpath.normpath(path)

    def _change_directory(self, path):
        path = posixpath.normpath(path)  # todo think maybe we can simplified this function
        path_list = path.split('/')
        temp_dir = None
        operation_status = True
        for way_elem in path_list:
            if way_elem == '' and not temp_dir:
                temp_dir = self.parse_directory(2)
            elif way_elem == '' and temp_dir and way_elem == path_list[len(path_list) - 1]:
                break
            else:
                if not temp_dir:
                    temp_dir = self.working_directory
                dir_entry = temp_dir.find(way_elem, 'by_name_dir')
                if dir_entry:
                    temp_dir = self.parse_directory(dir_entry.data_cluster)
                else:
                    operation_status = False
                    break

        return temp_dir, operation_status

    def change_directory(self, path):
        directory, status = self._change_directory(path)
        if status:
            self.working_directory = directory
        else:
            raise FatReaderExceptions.DirectoryDoesNotExistException()

    def get_working_directory_information(self, path="", names=True, datetime=False, attributes=False, hidden=False,
                                          size=False):
        destination_dir = self.working_directory
        if path:
            destination_dir, operation_status = self._change_directory(path)
            if not operation_status:
                raise FatReaderExceptions.InvalidPathException()
        info = ""
        for files in destination_dir.entries_list:
            info += files.to_string() + "\n"
        return info

    def __path_parser(self, path):
        """
        :param path:
        :return: path to object directory and object name and what the fuck is this shit
        """
        canonical_path = None
        head = None
        tail = None
        path = posixpath.normpath(path)
        directory, head_exist = self._change_directory(path)
        if head_exist:
            canonical_path = self._calculate_canonical_path(directory)
        else:
            head, tail = posixpath.split(path)
            directory, head_exist = self._change_directory(head)
            if head_exist:
                canonical_path = posixpath.normpath(posixpath.join(self._calculate_canonical_path(directory), tail))
            else:
                raise FatReaderExceptions.InvalidPathException()

        head, tail = posixpath.split(canonical_path)
        head_exist, tail_exist, tail_is_directory = self._path_is_correct(head, tail)
        if not head_exist or not (tail_exist or tail == ''):
            raise FatReaderExceptions.InvalidPathException()
        return head, tail, tail_is_directory

    def _path_is_correct(self, head, tail):
        """
        Check and returns path parameters
        :params *posix.split(path)
        :param head: path to directory with file or directory
        :param tail: file or directory name
        :return: head_exist , tail_exist , tail_is_directory
        """
        directory, correct_operation = self._change_directory(head)
        head_exist = correct_operation
        tail_exist = correct_operation and not tail == ''
        tail_is_directory = None
        if tail_exist:
            tail_source = directory.find(tail, "by_name")
            if tail_source:
                tail_is_directory = tail_source.atttributes.directory
            else:
                tail_exist = False
        return head_exist, tail_exist, tail_is_directory

    def __get_descriptors(self, path, file_or_dir_expected=True):
        parent_dir_path, file, file_is_dir = self.__path_parser(path)
        if file_or_dir_expected and file == '':
            raise FatReaderExceptions.InvalidPathException()
        destination_dir, operation_status = self._change_directory(parent_dir_path)
        file_source = destination_dir.find(file, "by_name")
        return destination_dir, file_source, file

    def _pre_operation_processing(self, path):
        return self.__get_descriptors(path)

    def rename(self, path, new_name):
        destination_dir, file_source, file_name = self._pre_operation_processing(path)
        self.file_writer.rename(new_name, destination_dir, file_source)
        self.refresh()

    def transfer(self, from_path, to_path):
        destination_dir, error = self._change_directory(to_path)
        if error:
            raise FatReaderExceptions.InvalidPathException()
        file_dir, file_source, file_name = self._pre_operation_processing(from_path)
        self.file_writer.transfer_file(destination_dir, file_source)
        self.refresh()

    def new_directory(self, path, attr="d", program_data=None):
        destination_dir = None
        file_source = None
        file_name = None
        if not program_data:
            destination_dir, file_source, file_name = self._pre_operation_processing(path)
            if not file_source:
                FatReaderExceptions.FileAlreadyExistException()
        else:
            destination_dir = program_data.destination_dir
            file_name = program_data.file_source.name
            attr = program_data.file_source.attr_string
        start_cluster = self.file_writer.new_file(file_name, attr, destination_dir)
        if not program_data:
            self.refresh()
        return start_cluster

    def copy_on_image(self, from_path, to_path):
        destination_dir, error = self._change_directory(to_path)
        if error:
            raise FatReaderExceptions.InvalidPathException()
        file_dir, file_source, file_name = self._pre_operation_processing(from_path)
        self.file_writer.copy_file(destination_dir, file_source)
        self.refresh()

    def remove_file(self, file_name, recoverable=True, clean=False):
        file_dir, file_source, file_name = self._pre_operation_processing(file_name)
        if not file_source.attributes.directory:
            self.file_writer.delete_directory_or_file(file_source, recoverable, clean)
        else:
            raise FatReaderExceptions.NotAFileException()
        self.refresh()

    def get_file_information(self, file_name):
        file_dir, file_source, file_name = self._pre_operation_processing(file_name)
        return file_source.to_string()

    def refresh(self):
        self.working_directory = self.parse_directory(self.working_directory.data_cluster)

    def _file_exist_name_file_source_path(self, destination_dir: DirectoriesStructures.Directory,
                                          file_source: FeC.FileEntry):
        pattern = re.compile("[^.]\((?P<folder>\d+)\)$|\((?P<file>\d+)\)\.[^\.]*$")
        pattern_end = re.compile("(\.)[^\.]*$")
        temp_file_source = destination_dir.find(file_source.name, "by_name")
        while temp_file_source:
            m = pattern.search(file_source.name)
            number = ""
            new_name = ""
            n = m
            if m:
                result = m.groupdict()
                accessor = "file"
                if result["folder"]:
                    accessor = "folder"
                number = str(int(result[accessor]) + 1)
            else:
                number = '(1)'
                n = pattern_end.search(file_source.name)
            if not n:
                new_name = file_source.name + number
            else:
                m = n
                new_name = file_source.name[0:m.start(2)] + number + file_source.name[m.end(2):]

            temp_file_source = destination_dir.find(new_name, "by_name")
            file_source._long_name = new_name
        return file_source

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


    def _check_os_path(self, os_path ):
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
        head , tail , is_dir = self.__path_parser(image_path)
        if not is_dir:
            raise  FatReaderExceptions.InvalidPathException()
        return posixpath.join(head, tail)

    def _from_os_write_copy_data(self, os_path , destination_dir):
        os_files = IOmodule.OSDirectoryReader(self.core.fat_bot_sector.cluster_size)
        for file in os_files.files_stream(os_path):
            head , tail = os.path.split(file)
            data_cluster = self.file_writer.new_file(tail,"", destination_dir)
            self.file_writer.extend_file(data_cluster, os.path.getsize(file))
            clusters_offsets = self.file_writer.get_file_allocation_offsets(data_cluster)
            fd = os_files.read_file(file)
            for  offset , data in zip(clusters_offsets, os_files.file_data_stream(fd)):
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
        #os_files = IOmodule.OSDirectoryReader(self.core.fat_bot_sector.cluster_size)
        destination_dir, sst = self._change_directory(image_path)
        self._from_os_write_copy_data(os_path, destination_dir)

    def copy_to_os(self, image_path , os_path):
        head, tail, is_dir = self.__path_parser(image_path)
        os_files = IOmodule.OSDirectoryWriter(self.core.fat_bot_sector.cluster_size)
        os_files.create_dir(os_path)
        if not is_dir:
            src_dir, sst = self._change_directory(head)
            src_dsc_file  = src_dir.find(tail, "by_name")
            f = os_files.crete_file(os.path.join(os_path, tail))
            os_files.write_data_to_file(f, self.file_reader.parse_non_buffer(src_dsc_file.data_cluster))
            f.close()
        else:
            src_dir, sst = self._change_directory(posixpath.join(head, tail))
            self._write_copy_data_to_os(src_dir, os_path)


    def _write_copy_data_to_os(self, from_dir: DirectoriesStructures.Directory, os_path):
        os_files = IOmodule.OSDirectoryWriter(self.core.fat_bot_sector.cluster_size)
        for file in from_dir.get_files_sources():
            #self.file_writer.copy_file(to_dir, files)
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
