import FatReaderExceptions
import FileDescriptor
import FilenameConflictResolver


class DirectoryDescriptor:
    def __init__(self, core, file_entries, directory_data):
        self.core = core
        self._root_status = None
        self._self_data_cluster = None
        self._self_data_offset = None
        self._parent_data_cluster = None
        self._parent_data_offset = None
        self.entries_list = file_entries
        self.conflict_name_resolver = FilenameConflictResolver.NameConflictResolver()
        self._writes_place = None
        self._free_entries_amount = None
        self._drop_existing_data(directory_data)
        self._default_cluster_allocation_size = 1
        self._cluster_size = core.fat_bot_sector.cluster_size
        self.searching_dict = None
        self._short_names = [entry.short_name for entry in file_entries]
        self._long_names = [entry.name for entry in file_entries]
        self._init_files(file_entries)

    def _drop_existing_data(self, directory_data):
        self._writes_place = []
        free_place_counter = 0
        for data, offset, status in directory_data:
            self._writes_place = (status, offset)
            if status:
                free_place_counter += 1
        self._free_entries_amount = free_place_counter

    def drop_data(self):
        self.core = None
        self._root_status = None
        self._self_data_cluster = None
        self._self_data_offset = None
        self._parent_data_cluster = None
        self._parent_data_offset = None
        self.entries_list = None
        self.searching_dict = None
        self._short_names = None  # tuple([entry.short_name for entry in file_entries_list])
        self._long_names = None  # tuple([entry.long_name for entry in file_entries_list])
        self._writes_place = None  # free_entry_place
        self._free_entries_amount = None  # free_entries_amount
        self._default_cluster_allocation_size = None
        self._cluster_size = None  # core.fat_bot_sector.cluster_size

    def _find_place_for_entry(self, amount):
        last_index = 0
        index_pool = []
        while len(index_pool) != amount:
            index_pool, last_index = self.try_found_place_for_entry(amount, last_index)
            if len(index_pool) != amount:
                self._extend_directory()
        return index_pool

    def _get_entry_place_to_flush(self, amount):
        index_pool = self._find_place_for_entry(amount)
        offsets_pool = []
        for x in index_pool:
            status, offset = self._writes_place[x]
            offsets_pool.append(offset)
            self._writes_place[x] = (False, offset)
        return reversed(offsets_pool)

    def _mark_free_place(self, offsets):
        index_pool = []
        for number, (status, offset) in enumerate(self._writes_place):
            if offset in offsets:
                index_pool.append(number)
            if len(index_pool) == len(offsets):
                break
        for x in index_pool:
            status, offset = self._writes_place[x]
            self._writes_place[x] = (True, offset)

    def try_found_place_for_entry(self, amount, start_position=0):
        index_pool = []
        last_index = 0
        for index, (status, offset) in enumerate(self._writes_place[start_position:]):
            last_index = index
            if status:
                index_pool.append((index, offset))
                if len(index_pool) == amount:
                    break
            else:
                if index_pool:
                    index_pool = []
        return index_pool, last_index

    def calculate_size_on_disk(self):
        size = 0
        for x in self.entries():
            size += x.calculate_size_on_disk()
        return size

    def _extend_directory(self):
        cluster, status = self.core.fat_tripper.extend_file(self.data_cluster, self._default_cluster_allocation_size)
        if not status:
            raise FatReaderExceptions.AllocationMemoryOutException
        self._note_allocated_place(cluster)

    def _note_allocated_place(self, cluster):
        extended_clusters_offsets = self.core.fat_tripper.get_clusters_offsets_list(cluster)
        for offset in extended_clusters_offsets:
            self._writes_place += [(True, offset + x) for x in range(0, self._cluster_size, 32)]
        self._free_entries_amount += self._cluster_size // 32 * len(extended_clusters_offsets)

    def delete(self, clear=False):
        for x in self.entries():
            x.delete(clear)
        self.drop_data()

    def make_directory(self, name):
        new_file = FileDescriptor.FileDescriptor()
        new_file.set_core(self.core)
        new_file.set_parent_directory(self)
        new_file.new_entry(
            *self.conflict_name_resolver.get_new_names(name, True, tuple(self._long_names), tuple(self._short_names)),
            attr="d")  # TODO WRITE THIS
        new_file.flush()
        self.entries_list.append(new_file)
        new_dir_data_offset = new_file.data_offset
        new_dir_data_cluster = new_file.data_cluster
        self._short_names.append(new_file.short_name)
        self._long_names.append(new_file.name)
        dir_self = FileDescriptor.FileDescriptor()
        dir_self.set_core(self.core)
        dir_self.new_entry('.', [], create_long=False, data_cluster=new_dir_data_cluster, attr="dh")
        dir_self._entry_offset_in_dir = [new_dir_data_offset]
        dir_self._flush()
        dir_parent = FileDescriptor.FileDescriptor()
        dir_parent.set_core(self.core)
        dir_parent.new_entry('..', [], create_long=False, data_cluster=self.data_cluster, attr="dh")
        dir_parent._entry_offset_in_dir = [new_dir_data_offset + 32]
        dir_parent._flush()
        return new_dir_data_cluster

    def make_file(self, name):
        new_file = FileDescriptor.FileDescriptor()
        new_file.set_core(self.core)
        new_file.set_parent_directory(self)
        new_file.new_entry(
            *self.conflict_name_resolver.get_new_names(name, True, tuple(self._long_names), tuple(self._short_names)))
        new_file.flush()
        self.entries_list.append(new_file)
        self._short_names.append(new_file.short_name)
        self._long_names.append(new_file.name)

    def rename_file(self, file_name, new_name):
        file_descriptor = self.find(file_name, "by_name")
        self._short_names.remove(file_descriptor.short_name)
        self._long_names.remove(file_descriptor.name)
        file_descriptor.rename(new_name, self._short_names, self._long_names)
        self._short_names.append(file_descriptor.short_name)
        self._long_names.append(file_descriptor.name)

    def remove_file(self, file_name):
        file_descriptor = self.find(file_name, "by_name")
        self._short_names.remove(file_descriptor.short_name)
        self._long_names.remove(file_descriptor.name)
        self.entries_list.remove(file_descriptor)
        file_descriptor.delete()

    @property
    def short_names(self):
        return self._short_names

    @property
    def long_names(self):
        return self._long_names

    @property
    def is_root(self):
        return self._root_status

    @property
    def data_cluster(self):
        return self._self_data_cluster

    @property
    def data_offset(self):
        return self._self_data_offset

    @property
    def parent_directory_cluster(self):
        return self._parent_data_cluster

    @property
    def parent_directory_offset(self):
        return self._parent_data_offset

    def _init_search_dict(self):
        self.searching_dict = {"by_address": lambda value, iterable: value == iterable.data_cluster,
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
            self._self_data_cluster = self_entry.data_cluster
            self._self_data_offset = self_entry.data_offset
            self._parent_data_cluster = parent_entry.data_cluster
            self._parent_data_offset = parent_entry.data_offset
            self._root_status = False
        elif len(file_entries_list):  # can be crashed when directory have trash  it needs to check cluster!!!!
            if file_entries_list[0].attributes.volume_id:
                self._self_data_cluster = 2
                self._self_data_offset = self.core.fat_bot_sector.root_directory_offset
                self._parent_data_cluster = 2
                self._parent_data_offset = self._self_data_offset = self.core.fat_bot_sector.root_directory_offset
                self._root_status = True
            else:
                # check cluster number ? it will be helpful to find type of error
                pass  # todo rase here something
        else:
            # this can happends if we create new directory  but not create  . .. dirs
            pass

    def get_file_data_cluster(self, file_name):  # todo make it more universal in future
        entry = self.find(file_name, "by_name")
        if entry:
            value = entry.data_cluster
            if value == 0:
                value = 2
            return True, value
        else:  # todo reformate this
            return False, 2

    def directories_sources(self):
        return filter(lambda x: x.attributes.directory, self.entries_list)

    def files_sources(self):
        return filter(lambda x: not x.attributes.directory, self.entries_list)

    def entries(self):
        for x in self.entries_list:
            yield x

    def find(self, value, key):
        if key in self.searching_dict:
            for entry in self.entries_list:
                if self.searching_dict[key](value, entry):
                    return entry
