import FileDescriptor
import FilenameConflictResolver
import OSDescriptors
from FatReaderExceptions import *


class DirectoryDescriptor:
    def __init__(self, core, file_entries, directory_data):
        self.core = core
        self._root_status = None
        self.self_descriptor = None
        self.parent_descriptor = None
        self._self_data_cluster = None
        self._self_data_offset = None
        self._parent_data_cluster = None
        self._parent_data_offset = None
        self.entries_list = file_entries
        self.activate_files_descriptors()
        self.conflict_name_resolver = FilenameConflictResolver.NameConflictResolver()
        self._writes_place = None
        self._free_entries_amount = None
        self._drop_existing_data(directory_data)
        self._default_cluster_allocation_size = 1
        self._cluster_size = core.fat_boot_sector.cluster_size
        self.searching_dict = None
        self._short_names = [entry.short_name for entry in file_entries]
        self._long_names = [entry.name for entry in file_entries]
        self._init_files(file_entries)

    def activate_files_descriptors(self):
        for descriptor in self.entries_list:
            descriptor.set_core(self.core)
            descriptor.set_parent_directory(self)

    def _drop_existing_data(self, directory_data):
        self._writes_place = []
        free_place_counter = 0
        for data, offset, status in directory_data:
            self._writes_place.append((status, offset))
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
        self._cluster_size = None  # core.fat_boot_sector.cluster_size

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
        for index, offset in index_pool:
            status, offset = self._writes_place[index]
            offsets_pool.append(offset)
            self._writes_place[index] = (False, offset)
        offsets_pool.reverse()
        return offsets_pool

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
        cluster = self.core.fat_table.extend_file(self.data_cluster, self._default_cluster_allocation_size)
        self._note_allocated_place(cluster)

    def _note_allocated_place(self, cluster):
        extended_clusters_offsets = self.core.fat_table.get_clusters_offsets_list(cluster)
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
            *self.conflict_name_resolver.get_new_names(name, True, tuple(self._short_names), tuple(self._long_names)),
            attr="d")  # TODO WRITE THIS
        new_file.flush()
        self.entries_list.append(new_file)
        new_dir_data_offset = new_file.data_offset
        new_dir_data_cluster = new_file.data_cluster
        self._short_names.append(new_file.short_name)
        self._long_names.append(new_file.name)
        dir_self = FileDescriptor.FileDescriptor()
        dir_self.set_core(self.core)
        dir_self.new_entry('.', b'.', create_long=False, data_cluster=new_dir_data_cluster, attr="dh")
        dir_self._entry_offset_in_dir = [new_dir_data_offset]
        dir_self._flush()
        dir_parent = FileDescriptor.FileDescriptor()
        dir_parent.set_core(self.core)
        dir_parent.new_entry('..', b'..', create_long=False, data_cluster=self.data_cluster, attr="dh")
        dir_parent._entry_offset_in_dir = [new_dir_data_offset + 32]
        dir_parent._flush()
        return new_dir_data_cluster

    def make_file(self, name):
        new_file = FileDescriptor.FileDescriptor()
        new_file.set_core(self.core)
        new_file.set_parent_directory(self)
        new_file.new_entry(
            *self.conflict_name_resolver.get_new_names(name, False, tuple(self._short_names), tuple(self._long_names)),
            create_long=True)
        new_file.flush()
        self.entries_list.append(new_file)
        self._short_names.append(new_file.short_name)
        self._long_names.append(new_file.name)
        return new_file

    def rename_file(self, file_name, new_name):
        file_descriptor = self.find(file_name, "by_name")
        self._short_names.remove(file_descriptor.short_name)
        self._long_names.remove(file_descriptor.name)
        file_descriptor.rename(new_name, self._short_names, self._long_names)
        self._short_names.append(file_descriptor.short_name)
        self._long_names.append(file_descriptor.name)
        file_descriptor.flush()

    def remove_file(self, file_name):
        file_descriptor = self.find(file_name, "by_name")
        self._short_names.remove(file_descriptor.short_name)
        self._long_names.remove(file_descriptor.name)
        self.entries_list.remove(file_descriptor)
        file_descriptor.delete()

    def move(self, file_descriptor: FileDescriptor.FileDescriptor):
        new_entry = FileDescriptor.FileDescriptor()
        new_entry.set_core(self.core)
        new_entry.set_parent_directory(self)
        new_entry.new_entry_from_descriptor(file_descriptor)
        new_entry.flush()
        if new_entry.attributes.directory:
            entry_directory = self.core.file_system_utils.low_level_utils.parse_directory_descriptor(
                file_descriptor.data_cluster)
            parent_directory_descriptor = entry_directory.parent_descriptor
            parent_directory_descriptor._write_data_cluster(self.data_cluster)
            parent_directory_descriptor.flush()
        file_descriptor._delete_file_entry_on_disk(file_descriptor._entry_offset_in_dir)  # check correct work of this

    def parse_descriptors(self, file_descriptor, is_image_descriptor=False):
        to_directory = self.make_directory(file_descriptor.name)
        to_directory = self.core.file_system_utils.low_level_utils.parse_directory_descriptor(to_directory)
        if is_image_descriptor:
            from_directory = self.core.file_system_utils.low_level_utils.parse_directory_descriptor(
                file_descriptor.data_cluster)
        else:
            from_directory = OSDescriptors.DirectoryDescriptor(file_descriptor.file_path)
        return to_directory, from_directory

    def copy(self, file_descriptor: FileDescriptor.FileDescriptor, is_image_descriptor=True):
        if file_descriptor.directory:
            to_directory, from_directory = self.parse_descriptors(file_descriptor, is_image_descriptor)
            for descriptor in from_directory.entries():
                to_directory.copy(descriptor, is_image_descriptor)
        else:
            descriptor = self.make_file(file_descriptor.name)
            size = file_descriptor.calculate_size_on_disk()
            descriptor.write_data_into_file(size, file_descriptor.data_stream(self._cluster_size))
            descriptor.update_size_in_descriptor()
            descriptor.flush()

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
                               'by_name_dir': lambda value, iterable:
                               iterable.is_correct_name(value) and iterable.attributes.directory,
                               'by_name': lambda value, iterable: iterable.is_correct_name(value),
                               'by_name_file': lambda value, iterable:
                               iterable.is_correct_name(value) and not iterable.attributes.directory}

    def _init_files(self, file_entries_list):
        self._init_search_dict()
        self_entry = self.find(".", "by_name")
        parent_entry = self.find("..", "by_name")
        self.self_descriptor = self_entry
        self.parent_descriptor = parent_entry
        if self_entry and parent_entry:
            self._self_data_cluster = self_entry.data_cluster
            self._self_data_offset = self_entry.data_offset
            self._parent_data_cluster = parent_entry.data_cluster
            self._parent_data_offset = parent_entry.data_offset
            self._root_status = False
        elif len(file_entries_list):  # can be crashed when directory have trash  it needs to check cluster!!!!
            if file_entries_list[0].attributes.volume_id:
                self._self_data_cluster = 2
                self._self_data_offset = self.core.fat_boot_sector.root_directory_offset
                self._parent_data_cluster = 2
                self._parent_data_offset = self._self_data_offset = self.core.fat_boot_sector.root_directory_offset
                self._root_status = True
            else:
                # check cluster number ? it will be helpful to find type of error
                raise UnExpectedParsingError("Unexpected error: check cluster number what you trying to parse,\n" +
                                             "this directory doesn't contains parent or self directory link,\n" +
                                             "this is not root entry or root entry with corrupted id,\n " +
                                             "this directory contains another files descriptors\n" +
                                             "you can try to use special util to restore this directory\n" +
                                             "but you do at your own risk\n")
        else:
            raise UnExpectedParsingError("Unexpected error: check cluster number what you trying to parse,\n" +
                                         "this directory doesn't contains parent or self directory link,\n" +
                                         "this directory doesn't contains any files descriptors\n" +
                                         "you can try to use special util to restore this directory\n" +
                                         "but you do at your own risk\n")
            pass

    def directories_sources(self):
        return filter(lambda x: x.attributes.directory, self.entries_list)

    def files_sources(self):
        return filter(lambda x: not x.attributes.directory, self.entries_list)

    def entries(self):
        for x in self.entries_list:
            if x.name not in [".", ".."]:
                yield x

    def find(self, value, key):
        if key in self.searching_dict:
            for entry in self.entries_list:
                if self.searching_dict[key](value, entry):
                    return entry
