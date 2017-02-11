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
import FileSystemUtilsLowLevel




class FileSystemUtil:
    def __init__(self, core):
        self.core = core
        self.file_reader = FR.DataParser(core)
        self.directory_reader = FR.DirectoryParser(core)
        self.file_writer = FW.FileWriter(core)
        self.root_directory_offset = core.fat_bot_sector.root_directory_offset
        self.working_directory = self.directory_reader.nio_parse_directory(self.root_directory_offset)
        self.current_path = '/'

    def ls_recursive(self, path, long=False, all=False):

        pass

    def ls(self, path, long=False, all=False, recursive=False):
        if recursive:
            self.ls_recursive(path, long)

    def cp(self, path_from, path_to):
        pass

    def rmdir(self, path, clear=False):
        pass
    def path_validation(self, exist):
        pass
    def get_working_directory_information(self, path=""):
        destination_dir = self.working_directory
        if path:
            destination_dir, operation_status = self._change_directory(path)
            if not operation_status:
                raise FatReaderExceptions.InvalidPathException()
        info = ""
        for files in destination_dir.entries_list:
            info += files.to_string() + "\n"
        return info
    def cat(self, path, byte = False, text= True , encoding="cp866"):
        pass
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

    def calc_cluster_offset(self, cluster_number):
        return self.core.fat_bot_sector.calc_cluster_offset(cluster_number)

    def parse_directory(self, cluster_number):
        return self.directory_reader.nio_parse_directory(self.calc_cluster_offset(cluster_number))






    def change_directory(self, path):
        directory, status = self._change_directory(path)
        if status:
            self.working_directory = directory
        else:
            raise FatReaderExceptions.DirectoryDoesNotExistException()





    def rename(self, path, new_name):
        destination_dir, file_source, file_name = self._pre_operation_processing(path)
        self.file_writer.rename(new_name, destination_dir, file_source)
        self.refresh()



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




