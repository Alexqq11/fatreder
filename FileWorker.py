import FileEntryStructure as fs_struct


class FatTripper:  # unsafety with out file image error checking
    def __init__(self, core, fat_offsets):
        self.core = core
        self.image_reader = core.image_reader
        self.fat_offsets = fat_offsets
        self.current_fat_offset = fat_offsets[0]
        self.entry_size = 4

    def _get_fat_entry_local_offset(self, fat_entry):
        return fat_entry * self.entry_size

    def _get_fat_entry_global_offset(self, fat_entry):
        return self._get_fat_entry_local_offset(fat_entry) + self.current_fat_offset

    def get_file_clusters_offsets_list(self, fat_entry):
        return [self.core.fat_bot_sector.get_cluster_offset(cls) for cls in self.get_file_clusters_list(fat_entry)]

    def get_file_clusters_list(self, fat_entry):
        end_of_file = False
        clusters_list = []
        self.image_reader.set_global_offset(0)
        current_block = fat_entry
        while not end_of_file:
            clusters_list.append(current_block)
            data = self.image_reader.get_data_local(self._get_fat_entry_global_offset(current_block), self.entry_size,
                                                    True)
            if data >= 268435448:
                end_of_file = True
            else:
                current_block = data
                # else:
                #   clusters_list.append(data)
                #  fat_entry = data

        return clusters_list


class DirectoryParser:
    def __init__(self, core):
        self.core = core
        self.image_reader = core.image_reader
        self.File_entries = []
        self.offsets_list = None
        self.active_offset = None
        self.entry_size = 32
        self.zone_offset = 0
        self.next_offset = 0
        self.current_offset = 0
        self.current_cluster_offset_index = 0
        self.current_next = 0
        self.current_next_swapped = True
        self.current_next_set = False
        self.directory_size = 512 * 8
        self.entries_amount = 0
        self.current_parse_lfn = False  # one classter but in future we need to change offset to another disk clusters

    def _is_lfn(self, offset):
        first_entry_byte = self.image_reader.get_data_local(offset, 1)
        attr_entry_byte = self.image_reader.get_data_local(offset + 11, 1, True)  # need more tests
        # attr_entry_byte = struct.unpack('<B', attr_entry_byte)[0]
        mask = 2 ** 5 + 2 ** 4 + 2 ** 3 + 2 ** 2 + 2 ** 1 + 2 ** 0
        return ((attr_entry_byte & mask) == 15) and (first_entry_byte != b'\xe5')

    def _is_directory(self, offset):
        first_entry_byte = self.image_reader.get_data_local(offset, 1)
        # attr_entry_byte = self.image_reader.get_data(offset + 11, 1)  # need more tests
        return not ((first_entry_byte in [b'\xe5', b'\x00']) or self._is_lfn(offset))

    def _is_end_lfn(self, offset, number):
        ldir_order_byte = self.image_reader.get_data_local(offset, 1, True)
        return ((4 * 16) == (ldir_order_byte & (4 * 16))) and (((4 * 16) | number) == ldir_order_byte)

    def _is_correct_lfn(self, offset, number):
        ldir_order_byte = self.image_reader.get_data_local(offset, 1, True)
        return ldir_order_byte == number  # add hash names checking

    # def _is
    def _is_root_dir(self, directory_offset):
        return directory_offset == self.core.fat_bot_sector.get_root_dir_offset()
        # self.core.fat_bot_sector = ft.FatBootSector(self.core.image_reader)

    def nio_is_dir(self, offset):
        first_entry_byte = self.image_reader.get_data_global(offset, 1)
        return not ((first_entry_byte in [b'\xe5', b'\x00']) or self._is_lfn(offset))

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
            file_entry.set_dir(short_entry)
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
            end_of_cluster += self.core.fat_bot_sector.get_cluster_size()
            if (self.current_offset + self.entry_size) == end_of_cluster:
                self.current_cluster_offset_index += 1
                # check indexation
                if self.current_cluster_offset_index < len(self.offsets_list):
                    self.current_offset = self.offsets_list[self.current_cluster_offset_index]
                    # MAY BE SOMETHING WRONG HERE WITH OUT ELSE
            else:
                self.current_offset += self.entry_size

    def nio_parse_directory(self, directory_offset):
        dir_cluster_number = self.core.fat_bot_sector.get_cluster_number(directory_offset)
        self.offsets_list = self.core.fat_tripper.get_file_clusters_offsets_list(dir_cluster_number)
        self.current_cluster_offset_index = 0
        self.current_next_swapped = True
        self.current_next = 0
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

    def _get_clusters_lists(self, directory_offset):

        pass

    def parse_directory_on_offset(self, directory_offset):
        self.image_reader.set_global_offset(directory_offset)
        while self.zone_offset <= self.directory_size:
            if self._is_directory(self.zone_offset):
                temp_file_entry = fs_struct.FileEntryStructure()
                self.File_entries.append(temp_file_entry)
                temp_short_entry = fs_struct.DirEntryShortFat32()
                temp_short_entry.parse_entry_data(self.image_reader, directory_offset + self.zone_offset,
                                                  directory_offset, True)
                temp_file_entry.set_dir(temp_short_entry)
                self.next_offset = self.zone_offset + self.entry_size
                self.zone_offset -= self.entry_size
                lfn_number = 0
                parsing_lfn = True
                print(directory_offset + self.zone_offset)
                while self.zone_offset >= -32 and parsing_lfn:
                    if self._is_lfn(self.zone_offset):
                        lfn_number += 1
                        if not self._is_end_lfn(self.zone_offset, lfn_number):
                            if self._is_correct_lfn(self.zone_offset, lfn_number):
                                temp_ldir_entry = fs_struct.DirEntryLongFat32()
                                temp_ldir_entry.parse_entry_data(self.image_reader, directory_offset + self.zone_offset,
                                                                 directory_offset, True)
                                temp_file_entry.append_ldir_entry(temp_ldir_entry)
                            else:
                                parsing_lfn = False
                                # temp_file_entry.clear_lfn()
                                self.zone_offset = self.next_offset  # need except
                        else:
                            temp_ldir_entry = fs_struct.DirEntryLongFat32()
                            temp_ldir_entry.parse_entry_data(self.image_reader, directory_offset + self.zone_offset,
                                                             directory_offset, True)
                            temp_file_entry.append_ldir_entry(temp_ldir_entry)
                            parsing_lfn = False
                            self.zone_offset = self.next_offset
                    else:  # if lfn_list not empty need except
                        parsing_lfn = False
                        # temp_file_entry.clear_lfn()
                        self.zone_offset = self.next_offset
                    if parsing_lfn:
                        self.zone_offset -= self.entry_size
            else:
                self.zone_offset += self.entry_size
