import FileEntryStructure as fs_struct


class FatTripper:  # unsafety with out file image error checking
    def __init__(self, fat_offsets, image_reader):
        self.image_reader = image_reader
        self.fat_offsets = fat_offsets
        self.current_fat_offset = fat_offsets[0]
        self.entry_size = 4

    def _get_fat_entry_local_offset(self, fat_entry):
        return fat_entry * self.entry_size

    def _get_fat_entry_global_offset(self, fat_entry):
        return self._get_fat_entry_local_offset(fat_entry) + self.current_fat_offset

    def get_file_clusters_list(self, fat_entry):
        end_of_file = False
        clusters_list = []
        self.image_reader.set_global_offset(0)
        while not end_of_file:
            data = self.image_reader.get_data(self._get_fat_entry_global_offset(fat_entry), self.entry_size, True)
            if data >= 268435448:
                end_of_file = True
            else:
                clusters_list.append(data)
                fat_entry = data

        return clusters_list


class DirectoryParser:
    def __init__(self, image_reader, offsets_list):
        self.image_reader = image_reader
        self.File_entries = []
        self.offsets_list = offsets_list
        self.active_offset = None
        self.entry_size = 32
        self.zone_offset = 0
        self.next_offset = 0
        self.directory_size = 512 * 8
        self.entries_amount = 0  # one classter but in future we need to change offset to another disk clusters

    def _is_lfn(self, offset):
        first_entry_byte = self.image_reader.get_data(offset, 1)
        attr_entry_byte = self.image_reader.get_data(offset + 11, 1, True)  # need more tests
        # attr_entry_byte = struct.unpack('<B', attr_entry_byte)[0]
        mask = 2 ** 5 + 2 ** 4 + 2 ** 3 + 2 ** 2 + 2 ** 1 + 2 ** 0
        return ((attr_entry_byte & mask) == 15) and (first_entry_byte != b'\xe5')

    def _is_directory(self, offset):
        first_entry_byte = self.image_reader.get_data(offset, 1)
        # attr_entry_byte = self.image_reader.get_data(offset + 11, 1)  # need more tests
        return not ((first_entry_byte in [b'\xe5', b'\x00']) or self._is_lfn(offset))

    def _is_end_lfn(self, offset, number):
        ldir_order_byte = self.image_reader.get_data(offset, 1, True)
        return ((4 * 16) == (ldir_order_byte & (4 * 16))) and (((4 * 16) | number) == ldir_order_byte)

    def _is_correct_lfn(self, offset, number):
        ldir_order_byte = self.image_reader.get_data(offset, 1, True)
        return ldir_order_byte == number  # add hash names checking

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
