import struct


class FatTableReader:  # unsafety with out file image error checking
    def __init__(self, core, fat_offsets):
        self.core = core
        self.image_reader = core.image_reader
        self.fat_offsets = fat_offsets
        self.current_fat_index = 0
        self.current_fat_offset = fat_offsets[self.current_fat_index]
        self.entry_size = 4
        self.last_empty_entry = 3
        self.fat_size = core.fat_bot_sector.fat_size
        self.write_protection = False

    def set_write_protection(self):
        self.write_protection = True

    def unset_write_protection(self):
        self.write_protection = False

    def set_cluster_entry(self, current_cluster, next_cluster=268435448):  ## not safety
        bytes = struct.pack('<I', next_cluster)  #:
        self.image_reader.set_data_global(self._get_fat_entry_global_offset(current_cluster), bytes)

    def allocate_place(self, amount_of_clusters): # todo correct 90%  and return status
        empty_entry = self.find_empty_entries(1)[0]
        self.extend_file(empty_entry, amount_of_clusters -1)
        return empty_entry

    def extend_file(self, last_cluster, amount_of_clusters):
        empty_clusters_list = self.find_empty_entries(amount_of_clusters)[0]
        current_cluster = last_cluster
        # next_cluster = None

        for next_cluster in empty_clusters_list:
            self.set_cluster_entry(current_cluster, next_cluster)
            current_cluster = next_cluster
        self.set_cluster_entry(current_cluster)


    def find_empty_entries(self, amount_of_entries):  ## TODO MAKE SIZE CHEKER FOR ALLOCATING DISK SPACE
        clusters_list = []
        start_cluster = 3
        cache = ([],True)
        if not self.write_protection:
            started = False
            while amount_of_entries > len(clusters_list):
                if self._get_fat_entry_global_offset(start_cluster) == self.fat_offsets[self.current_fat_index] + self.fat_size:
                    cache = ([],False)
                    break
                else:
                    if not started:
                        start_cluster = self.last_empty_entry
                        started = True
                    data = self.image_reader.get_data_global(self._get_fat_entry_global_offset(start_cluster),
                                                             self.entry_size, True)
                    if data == 0:
                        clusters_list.append(start_cluster)
                        cache = (clusters_list,True)
                        self.last_empty_entry = start_cluster
                    start_cluster += 1
        return cache

    def _get_fat_entry_local_offset(self, fat_entry):
        return fat_entry * self.entry_size

    def _get_fat_entry_global_offset(self, fat_entry):
        return self._get_fat_entry_local_offset(fat_entry) + self.current_fat_offset

    def get_file_clusters_offsets_list(self, fat_entry):
        return [self.core.fat_bot_sector.calc_cluster_offset(cls) for cls in self.get_file_clusters_list(fat_entry)]

    def delete_file_fat_chain(self, file_cluster, set_end=False):
        entries = self.get_file_clusters_list(file_cluster)
        entries.reverse()
        bytes = b'\x00' * 4
        for current_block in entries:
            self.set_cluster_entry(current_block, 0) #.image_reader.set_data_global(self._get_fat_entry_global_offset(current_block), bytes)
        if set_end:
            self.set_cluster_entry(entries[len(entries) - 1], 268435448)

    def get_file_clusters_list(self, fat_entry):
        end_of_file = False
        clusters_list = []
        self.image_reader.set_global_offset(0)
        current_block = fat_entry
        while not end_of_file:
            clusters_list.append(current_block)
            data = self.image_reader.get_data_global(self._get_fat_entry_global_offset(current_block), self.entry_size,
                                                     True)
            if data >= 268435448:
                end_of_file = True
            else:
                current_block = data
        return clusters_list
