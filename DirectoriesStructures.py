class Directory:
    def __init__(self, file_entries_list):
        self.root_status = None
        self.self_data_cluster = None
        self.self_data_offset = None
        self.parent_data_cluster = None
        self.parent_data_offset = None
        self.entries_list = file_entries_list
        self.searching_dict = None
        self._init_files(file_entries_list)

    @property
    def is_root(self):
        return self.root_status

    @property
    def data_cluster(self):
        return self.self_data_cluster

    @property
    def data_offset(self):
        return self.self_data_offset

    @property
    def parent_directory_cluster(self):
        return self.parent_directory_cluster

    @property
    def parent_directory_offset(self):
        return self.parent_data_offset

    def _init_search_dict(self):
        self.searching_dict = {"by_address": lambda value, iterable: value == iterable.data_clustercv,
                               'by_name_dir': lambda value, iterable: iterable.is_correct_name(value) and
                                                                      iterable.attributes.directory,
                               'by_name': lambda value, iterable: iterable.is_correct_name(value),
                               'by_name_file': lambda value, iterable: iterable.is_correct_name(value) and
                                                                       not iterable.attributes.directory}

    def _init_files(self, file_entries_list):
        self._init_search_dict()
        self_entry = self.find(".", "by_name")
        parent_entry = self.find("..", "by_name")
        if self_entry and parent_entry:
            self.self_data_cluster = self_entry.data_cluster
            self.self_data_offset = self_entry.data_offset
            self.parent_data_cluster = parent_entry.data_cluster
            self.parent_data_offset = parent_entry.data_offset
            self.root_status = False
        else:
            if file_entries_list[0].attributes.volume_id:
                self.self_data_cluster = 2
                self.self_data_offset = file_entries_list[0].entries_offsets[0]
                self.parent_data_cluster = 2
                self.parent_data_offset = file_entries_list[0].entries_offsets[0]
                self.root_status = True
            else:
                pass  # todo rase here something

    def get_file_data_cluster(self, file_name):  # todo make it more universal in future
        entry = self.find(file_name, "by_name")
        if entry:
            value = entry.data_cluster
            if value == 0:
                value = 2
            return True, value
        else:  # todo reformate this
            return False, 2

    def find(self, value, key):  # todo it with func dict
        if key in self.searching_dict:
            for entry in self.entries_list:
                if self.searching_dict[key](value, entry):
                    return entry
