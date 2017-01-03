class FileWriter():
    def __init__(self, core):
        self.core = core
        self.image_reader = core.image_reader
        self.entry_size = 32
        self.cluster_size = core.fat_bot_sector.cluster_size

    def count_clusters(self, size_in_bytes):
        return (size_in_bytes + self.cluster_size - 1) // self.cluster_size

    def reserve_place_for_data(self, size_in_bytes):
        reserved_clusters = self.core.fat_tripper.find_empty_entries(self.count_clusters(size_in_bytes))
        # self.core.fat_tripper.set_write_protection()
        return reserved_clusters

    def extend_file(self, directory_start_cluster, size_in_bytes):
        clusters_amount = self.count_clusters(size_in_bytes)
        clusters = self.core.fat_tripper.get_file_clusters_list(directory_start_cluster)
        extended_cluster = clusters[len(clusters) - 1]
        self.core.fat_tripper.extend_file(extended_cluster, clusters_amount)

    def find_place_for_entry_on_current_cluster(self, directory_cluster, entries_number):
        directory_offset = self.core.fat_bot_sector.calc_cluster_offset()
        offset = directory_offset
        count = 0
        start_offset = 0
        start_offset_set = False
        cache = (False, [])
        while (offset < self.cluster_size + directory_offset):
            check_byte = self.image_reader.get_data_global(offset, 1)
            if check_byte in [b'\x00', b'\xe5']:
                if not start_offset_set:
                    start_offset = offset
                    start_offset_set = True
                count += 1
                if (count == entries_number):
                    cache = (True, [offset for offset in range(start_offset, offset + 1, self.entry_size)])
                    break
            else:
                count = 0
                start_offset = 0
                start_offset_set = False
            offset += self.entry_size
        return cache

    def find_place_for_entry(self, directory_start_cluster, entries_number):
        clusters = self.core.fat_tripper.get_file_clusters_list(directory_start_cluster)
        cache = (False, [])
        for cluster in clusters:
            cache = self.find_place_for_entry_on_current_cluster(cluster, entries_number)
            if cache[0]:
                break
        return cache

    def delete_file_entry(self, file_entry_offset, entry_size_in_bytes, clean=False):
        data = b'\xe5'
        if clean:
            data = b'\x00' * entry_size_in_bytes
        self.image_reader.set_data_global(file_entry_offset, data)
        pass

    def delete_fat_chain(self, start_cluster):
        self.core.fat_tripper.delete_file_fat_chain(start_cluster)

    def delete_data_clusters(self, start_cluster):
        offsets = self.core.fat_tripper.get_file_clusters_offsets_list(start_cluster)
        zero_cluster = b'\x00' * self.cluster_size
        for offset in offsets:
            self.image_reader.set_data_global(offset, zero_cluster)

    def delete_directory_or_file(self, file_entry_offset, file_entry_size_in_bytes, file_data_cluster, recoverable=True,
                                 clean=False):
        if clean:
            self.delete_data_clusters(file_data_cluster)
            self.delete_fat_chain(file_data_cluster)
            self.delete_file_entry(file_entry_offset, file_entry_size_in_bytes, True)
        elif recoverable:
            self.delete_file_entry(file_entry_offset, file_entry_size_in_bytes)
        else:
            self.delete_fat_chain(file_data_cluster)
            self.delete_file_entry(file_entry_offset, file_entry_size_in_bytes, True)