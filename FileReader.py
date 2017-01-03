import DirectoriesStructures as dir
import FileEntryStructure as fs_struct


class DataParser():
    def __init__(self, core):
        self.core = core
        self.image_reader = core.image_reader
        self.data_clusters_offsets_list = []
        self.cluster_size = None
        self.buffer = []

    def _set_default_settings(self):
        self.data_clusters_offsets_list = []
        self.cluster_size = None
        self.buffer = []

    def _set_work_settings(self, file_cluster_number):
        self.data_clusters_offsets_list = self.core.fat_tripper.get_file_clusters_offsets_list(file_cluster_number)
        self.cluster_size = self.core.fat_bot_sector.cluster_size

    def parse_buffer(self, file_cluster_number):
        self._set_default_settings()
        self._set_work_settings(file_cluster_number)
        for cluster_offset in self.data_clusters_offsets_list:
            self.buffer.append(self.image_reader.get_data_global(cluster_offset, self.cluster_size))
        buffer_link = self.buffer
        self._set_default_settings()
        return buffer_link

    def parse_non_buffer(self, file_cluster_number):
        self._set_default_settings()
        self._set_work_settings(file_cluster_number)
        for cluster_offset in self.data_clusters_offsets_list:
            yield self.image_reader.get_data_global(cluster_offset, self.cluster_size)  # ???


class DirectoryParser:
    def __init__(self, core):
        self.core = core
        self.image_reader = core.image_reader
        self.File_entries = []
        self.offsets_list = None
        self.entry_size = 32
        self.current_offset = 0
        self.current_cluster_offset_index = 0
        self.current_next = 0
        self.current_next_swapped = True
        self.current_next_set = False
        self.current_parse_lfn = False

    def nio_is_dir(self, offset):
        first_entry_byte = self.image_reader.get_data_global(offset, 1)
        return not ((first_entry_byte in [b'\xe5', b'\x00']) or self.nio_is_lfn(offset))

    def nio_is_lfn(self, offset):
        first_entry_byte = self.image_reader.get_data_global(offset, 1)
        attr_entry_byte = self.image_reader.get_data_global(offset + 11, 1, True)  # need more tests
        mask = 2 ** 6 - 1
        return ((attr_entry_byte & mask) == 15) and (first_entry_byte not in [b'\xe5', b'\x00'])

    def nio_is_correct_lfn(self, offset, number):
        ldir_order_byte = self.image_reader.get_data_global(offset, 1, True)
        return ldir_order_byte == number or self.nio_is_end_lfn(offset, number)  # add hash names checking

    def nio_parse_short_entry(self, entry_global_offset):
        status = self.nio_is_dir(entry_global_offset)
        file_entry = None
        if status:
            file_entry = fs_struct.FileEntryStructure()
            self.File_entries.append(file_entry)
            short_entry = fs_struct.DirEntryShortFat32()
            short_entry.parse_entry_data(self.image_reader, entry_global_offset, return_offset=True)
            file_entry.set_dir(short_entry, entry_global_offset)
        return status, file_entry, False, 0

    def nio_is_end_lfn(self, offset, number):
        ldir_order_byte = self.image_reader.get_data_global(offset, 1, True)
        return ((4 * 16) == (ldir_order_byte & (4 * 16))) and (((4 * 16) | number) == ldir_order_byte)

    def nio_parse_long_entry(self, directory_offset, file_entry, previous_entry_number):
        lfn_status = self.nio_is_lfn(directory_offset)
        correct_lfn_status = self.nio_is_correct_lfn(directory_offset, previous_entry_number + 1)
        end_status = self.nio_is_end_lfn(directory_offset, previous_entry_number + 1)
        if lfn_status and correct_lfn_status:
            ldir_entry = fs_struct.DirEntryLongFat32()
            ldir_entry.parse_entry_data(self.image_reader, directory_offset, return_offset=True)
            file_entry.append_ldir_entry(ldir_entry)
            previous_entry_number += 1
            # elif( not correct_lfn_status): # needs check
            # file_entry.clear_lfn()
        return lfn_status and correct_lfn_status, file_entry, end_status, previous_entry_number

    def reset_to_default_settings(self):
        self.File_entries = []
        self.offsets_list = None
        self.entry_size = 32
        self.current_offset = 0
        self.current_cluster_offset_index = 0
        self.current_next = 0
        self.current_next_swapped = True
        self.current_next_set = False
        self.current_parse_lfn = False

    def nio_offset_manager(self, parsing_lfn):
        if parsing_lfn:
            if not self.current_next_set:
                self.current_next = self.current_offset
                self.current_next_set = True
                self.current_next_swapped = False

            if self.current_offset == self.offsets_list[self.current_cluster_offset_index]:
                self.current_cluster_offset_index -= 1
                if self.current_cluster_offset_index >= 0:  # fix here > --> >= attention!
                    self.current_offset = self.offsets_list[self.current_cluster_offset_index]  # check indexation
                    self.current_offset += self.core.fat_bot_sectorget_cluster_size() - self.entry_size
                else:
                    self.current_cluster_offset_index = 0
                    self.current_parse_lfn = False
                    self.nio_offset_manager(False)
            else:
                self.current_offset -= self.entry_size
        else:
            if not self.current_next_swapped:
                self.current_offset = self.current_next
                self.current_next_set = False
                self.current_next_swapped = True

            end_of_cluster = self.offsets_list[self.current_cluster_offset_index]
            end_of_cluster += self.core.fat_bot_sector.cluster_size
            if (self.current_offset + self.entry_size) == end_of_cluster:
                self.current_cluster_offset_index += 1
                # check indexation
                if self.current_cluster_offset_index < len(self.offsets_list):
                    self.current_offset = self.offsets_list[self.current_cluster_offset_index]
                    # MAY BE SOMETHING WRONG HERE WITH OUT ELSE
            else:
                self.current_offset += self.entry_size

    def nio_parse_directory(self, directory_offset):
        self.reset_to_default_settings()
        dir_cluster_number = self.core.fat_bot_sector.calc_cluster_number(directory_offset)
        self.offsets_list = self.core.fat_tripper.get_file_clusters_offsets_list(dir_cluster_number)
        self.current_offset = directory_offset
        cache = None
        while self.current_cluster_offset_index < len(self.offsets_list):
            if self.current_parse_lfn:
                cache = self.nio_parse_long_entry(self.current_offset, cache[1], cache[3])

                if cache[2] or not cache[0]:  # need some tests
                    self.current_parse_lfn = False
            else:
                cache = self.nio_parse_short_entry(self.current_offset)
                self.current_parse_lfn = cache[0]
            self.nio_offset_manager(self.current_parse_lfn)
        file_entries = self.File_entries
        self.reset_to_default_settings()
        return dir.Directory(file_entries)
