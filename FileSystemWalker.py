import FileReader as FR
import FileWriter as FW
import os.path
class FileSystemUtil:
    def __init__(self, core):
        ''' by default working directory is a root directory'''
        self.core = core
        self.file_reader = FR.DataParser(core)
        self.directory_reader = FR.DirectoryParser(core)
        self.file_writer = FW.FileWriter(core)
        self.root_directory_offset = core.fat_bot_sector.get_root_dir_offset()
        self.working_directory = self.directory_reader.nio_parse_directory(self.root_directory_offset)
        self.current_path = '/'

    def get_cluster_offset(self, cluster_number):
        return self.core.fat_bot_sector.get_cluster_offset(cluster_number)

    def parse_directory(self,cluster_number):
        return self.directory_reader.nio_parse_directory(self.get_cluster_offset(cluster_number))

    def calculate_directory_path(self):
        parent_cluster = self.working_directory.get_file_cluster_number('..')
        own_cluster = self.working_directory.get_file_cluster_number('.')
        temp_dir = None
        path = '/'
        while parent_cluster[0]:
            temp_dir = self.parse_directory(parent_cluster[1])
            path = '/' + temp_dir.find(own_cluster[1],'by_address').get_name() + path
            own_cluster = parent_cluster
            parent_cluster = temp_dir.get_file_cluster_number('..')
        return path
    def change_directory(self, path):
        path_list = path.split('/')
        temp_dir = None
        operation_status = True
        for way_elem in path_list:
            if way_elem == '' and temp_dir == None:
                temp_dir = self.parse_directory(2)
            elif way_elem == '' and not temp_dir == None and way_elem == path_list[len(path_list) - 1]:
                break
            else:
                if temp_dir == None:
                    temp_dir = self.working_directory
                dir_entry = temp_dir.find(way_elem, 'by_name_dir')
                if not dir_entry == None:
                    temp_dir = self.parse_directory(dir_entry.get_content_cluster_number())

                    dir_entry = None
                else:
                    operation_status = False
                    break
        if operation_status:
            self.working_directory = temp_dir
    def get_working_directory_information(self):
        info = []
        for files in self.working_directory.entries_list:
            files.set_user_representation()
            info.append(files.human_readable_view.to_string())
        return info

    def get_file_information(self, name):
        return self.working_directory.find(name,"by_name").human_readable_view.to_string()