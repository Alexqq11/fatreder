import struct
class FatTripper:  # unsafety with out file image error checking
    def __init__(self, core, fat_offsets):
        self.core = core
        self.image_reader = core.image_reader
        self.fat_offsets = fat_offsets
        self.current_fat_index = 0
        self.current_fat_offset = fat_offsets[self.current_fat_index]
        self.entry_size = 4
        self.last_empty_entry = 2
        self.fat_size = core.fat_bot_sector.get_fat_size
        self.write_protection = False
    def set_write_protection(self):
        self.write_protection = True
    def unset_write_protection(self):
        self.write_protection = False
    def set_cluster_entry(self, current_cluster, next_cluster = 268435448):## not safety
        bytes = struct.pack('<I',next_cluster)#:
        self.image_reader.set_data(self._get_fat_entry_global_offset(current_cluster), bytes)

    def extend_file(self, last_cluster, amount_of_clusters):
        empty_clusters_list = self.find_empty_entries(amount_of_clusters)
        current_cluster = last_cluster
        #next_cluster = None
        for next_cluster in empty_clusters_list:
            self.set_cluster_entry(current_cluster, next_cluster)
            current_cluster = next_cluster

    def find_empty_entries(self, amount_of_entries): # need check to we stay in current fat zone
        clusters_list = []
        start_cluster = None
        cache = (True, [])
        if not self.write_protection:
            while amount_of_entries > len(clusters_list):
                if self._get_fat_entry_global_offset(start_cluster) == self.fat_offsets[self.current_fat_index] + self.fat_size:
                    cache = (False, [])
                    break
                else:
                    start_cluster = self.last_empty_entry
                    data = self.image_reader.get_data_global(self._get_fat_entry_global_offset(start_cluster), self.entry_size,True)
                    if data == 0:
                        clusters_list.append(start_cluster)
                        cache = (True,  clusters_list)
                        self.last_empty_entry = start_cluster
                    start_cluster += 1
        return cache

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
            data = self.image_reader.get_data_global(self._get_fat_entry_global_offset(current_block), self.entry_size,
                                                    True)
            if data >= 268435448:
                end_of_file = True
            else:
                current_block = data
                # else:
                #   clusters_list.append(data)
                #  fat_entry = data

        return clusters_list