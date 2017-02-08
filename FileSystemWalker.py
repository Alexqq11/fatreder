import FileReader as FR
import FileWriter as FW
import DirectoriesStructures
import FileEntryCollector as FeC
import FileEntryCreator as FeCr
import FatReaderExceptions
import re
import os.path as pw
# import Core
import posixpath

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
        parent_cluster = self.working_directory.parent_directory_cluster
        own_cluster = self.working_directory.data_cluster
        temp_dir = self.working_directory
        path = '/'
        while not temp_dir.is_root:
            temp_dir = self.parse_directory(parent_cluster)
            path = '/' + temp_dir.find(own_cluster, 'by_address').name + path
            own_cluster = parent_cluster
            parent_cluster = temp_dir.parent_directory_cluster
        return path

    def _change_directory(self, path):
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

    def get_working_directory_information(self, path = "", names=True, datetime=False, attributes=False, hidden=False, size = False):
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
        path, file  = posixpath.split(path)

        pass
    def _path_parser(self, path):
        dir = False
        slash_position = 0
        error = False
        file_name = None
        new_path = ""
        path_list = path.split('/')
        if len(path_list) >= 2:
            if path_list[len(path_list) - 1] == '':
                dir = True
                if path_list[len(path_list) - 2] == '':
                    error = True
                else:
                    file_name = path_list[len(path_list) - 2]
                    new_path = "".join(['/' + path_list[word] for word in range(0, len(path_list) - 2)])
                    if path_list[0] != '':
                        new_path = '.' + new_path
            else:
                file_name = path_list[len(path_list) - 1]
                new_path = "".join(['/' + path_list[word] for word in range(0, len(path_list) - 1)])
                if path_list[0] != '':
                    new_path = '.' + new_path
        else:
            if len(path_list) == 0:
                error = True
            else:
                if path_list[0] == '':
                    error = True
                else:
                    file_name = path_list[0]
                    new_path = './'
        return new_path, file_name, dir, error

    def _pre_operation_processing(self, path):
        new_path, file_name, is_dir, error = self._path_parser(path)
        file_source = None
        destination_dir = None
        if error:
            raise FatReaderExceptions.InvalidPathException()
        if file_name == '.':
            new_path1 = new_path + './'
            new_path2 = new_path + '../'
            new_dir, operation_status = self._change_directory(new_path1)
            if not operation_status:
                raise FatReaderExceptions.InvalidPathException()
            new_dir_data_cluster = new_dir.data_cluster
            new_dir, error = self._change_directory(new_path2)
            file_source = new_dir.find(new_dir_data_cluster, "by_address")
            destination_dir = new_dir
        elif file_name == '..':
            new_path1 = new_path + '../'
            new_path2 = new_path + '../'
            new_dir, operation_status = self._change_directory(new_path1)
            if not operation_status:
                raise FatReaderExceptions.InvalidPathException()
            new_dir_data_cluster = new_dir.data_cluster
            new_dir, error = self._change_directory(new_path2)
            file_source = new_dir.find(new_dir_data_cluster, "by_address")
            destination_dir = new_dir
        else:
            new_dir, operation_status = self._change_directory(new_path)
            if not operation_status:
                raise FatReaderExceptions.InvalidPathException()
            file_source = new_dir.find(file_name, "by_name")
            destination_dir = new_dir
        return destination_dir, file_source, file_name

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

    def new_directory(self, path , attr = "d",program_data = None):
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
        return  start_cluster

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

    def _file_exist_name_file_source_path(self,destination_dir : DirectoriesStructures.Directory,file_source : FeC.FileEntry):
        pattern= re.compile("[^.]\((?P<folder>\d+)\)$|\((?P<file>\d+)\)\.[^\.]*$")
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
            #temp_creator = FeCr.ShortEntryCreator()
            #temp_creator.dir_listing = []
            #temp_creator._set_name(new_name)
            #file_source._long_name = new_name
            #file_source._short_name = temp_creator.dir_name.decode('cp866') # бага найдена мы ищем одно и тоже но проблема с нонами
            temp_file_source = destination_dir.find(new_name, "by_name")
            file_source._long_name = new_name
            #file_source._short_name = temp_creator.dir_name.decode('cp866')
        return  file_source


    def copy_directory(self, from_path , to_path):
        file_dir, file_source, file_name = self._pre_operation_processing(from_path)
        if not file_source.attributes.directory:
            raise FatReaderExceptions.NotADirectoryException()
        destination_dir, error = self._change_directory(to_path)
        if error:
            raise  FatReaderExceptions.InvalidPathException()
        file_source = self._file_exist_name_file_source_path(destination_dir, file_source)
        start_cluster =self.new_directory(None, "", CopyNewDirIMetaData(destination_dir, file_source))
        to_dir = self.parse_directory(start_cluster)
        from_dir = self.parse_directory(file_source.data_cluster)
        self._write_copy_data(from_dir, to_dir)
        self.refresh()

    def _write_copy_data(self,from_dir : DirectoriesStructures.Directory , to_dir : DirectoriesStructures.Directory):
        for files in from_dir.get_files_sources():
            self.file_writer.copy_file(to_dir, files)
        for dirs in from_dir.get_files_sources():
            start_cluster = self.new_directory(None, "", CopyNewDirIMetaData(to_dir, dirs))
            new_to_dir = self.parse_directory(start_cluster)
            new_from_dir = self.parse_directory(dirs.data_cluster)
            self._write_copy_data(new_from_dir, new_to_dir)


class CopyNewDirIMetaData:
    def __init__(self, destination_dir, file_source):
        self._file_source = file_source
        self._destination_dir = destination_dir

    @property
    def destination_dir(self):
        return  self._destination_dir
    @property
    def file_source(self):
        return self._file_source
