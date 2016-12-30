class Directory:
    def __init__(self, file_entries_list):
        self.root_status = None
        self.self_adrees = None
        self.parent_adres = None
        self.files = None
        self.path = None
        self.entries_list = file_entries_list
        self._init_user_readable_information()
        self._init_files(file_entries_list)

        # self.keys = {'by_long_name' : func1, 'by_short_name': func2, 'by_size': funct3,'by_addres'  }

    def _init_files(self, file_entries_list):
        self.files = {entry.get_name(): entry for entry in file_entries_list}

    def _init_user_readable_information(self):
        for entry in self.entries_list:
            entry.set_user_representation()

    def get_file_cluster_number(self, file_name):  # todo make it more universal in future
        if file_name in self.files:
            value = self.files[file_name].get_content_cluster_number()
            if value == 0:
                value = 2
            return True, value
        else:
            return False, 2

    def find(self, value, key):  # todo it with func dict
        func = None
        if key == "by_address":
            func = lambda value, iterable: value == iterable.get_content_cluster_number()
        elif key == 'by_name_dir':
            func = lambda value, iterable: value.lower() == iterable.get_name().lower() and \
                                           iterable.human_readable_view.attributes.attr_directory
        elif key == 'by_name':
            func = lambda value, iterable: value.lower() == iterable.get_name().lower()
        elif key == 'by_name_file':
            func = lambda value, iterable: value.lower() == iterable.get_name().lower() and \
                                           not iterable.human_readable_view.attributes.attr_directory
        for entry in self.entries_list:
            if func(value, entry):
                return entry
