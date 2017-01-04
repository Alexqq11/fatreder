import FileReader as FR
import FileWriter as FW
#import Core


class FileSystemUtil:
    def __init__(self, core):#: Core.Core):
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

    def change_directory(self, path):
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

                    dir_entry = None
                else:
                    operation_status = False
                    break
        if operation_status:
            self.working_directory = temp_dir

    def get_working_directory_information(self, names = True, datetime = False, attributes = False , hidden = False):
        info = []
        for files in self.working_directory.entries_list:
            info.append(files.to_string())
        return info
    #todo rewrite rm
    def remove_file(self, file_mame,recoverable = True, clean = False):
        dir_entry = self.working_directory.find(file_mame, "by_name_file")  # todo here dir entry none
        if dir_entry:
            self.file_writer.delete_directory_or_file(dir_entry, recoverable, clean)

    def get_file_information(self, name):
        return self.working_directory.find(name, "by_name").to_string()
