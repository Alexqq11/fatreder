import FileReader as FR
import FileWriter as FW


# import Core


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
        entry = self.working_directory.find(file_name, "by_name_file")
        if entry:
            addr = entry.data_cluster
            for data_part in self.file_reader.parse_non_buffer(addr):
                yield data_part

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
            # race directory not found error
            pass

    def get_working_directory_information(self, names=True, datetime=False, attributes=False, hidden=False):
        info = []
        for files in self.working_directory.entries_list:
            info.append(files.to_string())
        return info

    # todo rewrite rm
    def find_file_on_path(self):
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
                if path_list(len(path_list) - 2) == '':
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
            # race ilegal path expected exception
            pass
        if file_name == '.':
            new_path1 = new_path + './'
            new_path2 = new_path + '../'
            new_dir, error = self._change_directory(new_path1)
            if error:
                # race ilegal path expected exception
                pass
            new_dir_data_cluster = new_dir.data_cluster
            new_dir, error = self._change_directory(new_path2)
            file_source = new_dir.find(new_dir_data_cluster, "by_address")
            destination_dir = new_dir
        elif file_name == '..':
            new_path1 = new_path + '../'
            new_path2 = new_path + '../'
            new_dir, error = self._change_directory(new_path1)
            if error:
                # race ilegal path expected exception
                pass
            new_dir_data_cluster = new_dir.data_cluster
            new_dir, error = self._change_directory(new_path2)
            file_source = new_dir.find(new_dir_data_cluster, "by_address")
            destination_dir = new_dir
        else:
            new_dir, error = self._change_directory(new_path)
            if error:
                # race ilegal path expected exception
                pass
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
            # race invalid path
            pass
        file_dir, file_source, file_name = self._pre_operation_processing(from_path)
        self.file_writer.transfer_file(destination_dir, file_source)
        self.refresh()

    def new_directory(self, path):
        destination_dir, file_source, file_name = self._pre_operation_processing(path)
        if not file_source:
            # race file alredy exist exception
            pass
        self.file_writer.new_file(file_name, "d", destination_dir)
        self.refresh()

    def copy_on_image(self, from_path, to_path):
        destination_dir, error = self._change_directory(to_path)
        if error:
            # race invalid path
            pass
        file_dir, file_source, file_name = self._pre_operation_processing(from_path)
        self.file_writer.copy_file(destination_dir, file_source)
        self.refresh()

    def remove_file(self, file_mame, recoverable=True, clean=False):
        dir_entry = self.working_directory.find(file_mame, "by_name_file")  # todo here dir entry none
        if dir_entry:
            self.file_writer.delete_directory_or_file(dir_entry, recoverable, clean)
        self.refresh()

    def get_file_information(self, name):
        return self.working_directory.find(name, "by_name").to_string()
    def refresh(self):
        self.working_directory = self.parse_directory(self.working_directory.data_cluster)