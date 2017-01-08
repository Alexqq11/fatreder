import FileEntryCollector
import FileReader
import  os
class InputOutputModule:
    def __init__(self):
        self.cluster_size = 512 # todo change it
        self.file_stream = None
        self.core = None
        pass

    def read_file_data(self, path):
        file_stream = open(path,'rb')
        file_stream.seek(-1)
        file_end = self.file_stream.tell()
        start_pos = 0
        while start_pos == file_end:
            yield file_stream.reed(min(file_end - start_pos, self.cluster_size))
            start_pos += self.cluster_size
        file_stream.close()

    def write_file_data(self, path, file_source : FileEntryCollector.FileEntry):
        f = open(path,'wb')
        dp = FileReader.DataParser(self.core)
        for data in dp.parse_non_buffer(file_source.data_cluster):
            f.write(data)
        f.close()
    def create_dir(self, path):
        os.mkdir(path)
    def get_dir_list(self, path):
        dir_object = os.scandir(path)
        fatReader_entry_list = []
        for file_name in dir_object:
                fatReader_entry_list.append(file_name , os.path.join(path , file_name), os.path.isdir(os.path.join(path, file_name)))



