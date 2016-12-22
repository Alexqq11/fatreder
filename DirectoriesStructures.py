class Directory:
    def __init__(self, file_entries_list):
        self.root_status = None
        self.self_adrees = None
        self.parent_adres = None
        self.files = None
        self.path = None
        self._init_files(file_entries_list)
    def _init_files(self, file_entries_list):
        self.files = { entry.get_name() : entry for entry in file_entries_list }
