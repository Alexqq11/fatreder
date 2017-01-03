class Directory:
    def __init__(self, file_entries_list):
        self.root_status = None
        self.self_adrees = None
        self.parent_adres = None
        self.files = None
        self.path = None
        self.entries_list = file_entries_list
        self._init_files(file_entries_list)

        # self.keys = {'by_long_name' : func1, 'by_short_name': func2, 'by_size': funct3,'by_addres'  }

    def _init_files(self, file_entries_list):
        self.files = {entry.name : entry for entry in file_entries_list}

    def get_file_cluster_number(self, file_name):  # todo make it more universal in future
        if file_name in self.files:
            value = self.files[file_name].data_cluster
            if value == 0:
                value = 2
            return True, value
        else:
            return False, 2

    def find(self, value, key):  # todo it with func dict
        func = None
        if key == "by_address":
            func = lambda value, iterable: value == iterable.data_clusterc
        elif key == 'by_name_dir':
            func = lambda value, iterable: iterable.is_correct_name(value) and iterable.attributes.directory
        elif key == 'by_name':
            func = lambda value, iterable: iterable.is_correct_name(value)
        elif key == 'by_name_file':
            func = lambda value, iterable:iterable.is_correct_name(value) and not iterable.attributes.directory
        for entry in self.entries_list:
            if func(value, entry):
                return entry
