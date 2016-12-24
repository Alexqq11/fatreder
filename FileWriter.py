class FileWriter():
    def __init__(self, core):
        self.core = core
        self.image_reader = core.image_reader
        self.entry_size = 32
        self.cluster_size = core.fat_bot_sector.get_cluster_size()

    def count_clusters(self,size_in_bytes):
        return (size_in_bytes + self.cluster_size - 1) // self.cluster_size

    def reserve_place_for_data(self,size_in_bytes):
        reserved_clusters = self.core.fat_tripper.find_empty_entries(self.count_clusters(size_in_bytes))
        #self.core.fat_tripper.set_write_protection()
        return reserved_clusters

    def extend_file(self, directory_start_cluster, size_in_bytes):
        clusters_amount = self.count_clusters(size_in_bytes)
        clusters = self.core.fat_tripper.get_file_clusters_list(directory_start_cluster)
        extended_cluster = clusters[len(clusters) - 1]
        self.core.fat_tripper.extend_file(extended_cluster, clusters_amount)

    def find_place_for_entry_on_current_cluster(self, directory_cluster, entries_number):
        directory_offset = self.core.fat_bot_sector.get_cluster_offset()
        offset = directory_offset
        count = 0
        start_offset = 0
        start_offset_set = False
        cache = (False,[])
        while(offset < self.cluster_size + directory_offset):
            check_byte = self.image_reader.get_data_global(offset, 1)
            if check_byte in [b'\x00', b'\xe5']:
                if not start_offset_set:
                    start_offset = offset
                    start_offset_set = True
                count += 1
                if (count == entries_number):
                    cache = (True, [offset for offset in range(start_offset, offset +1, self.entry_size)])
                    break
            else:
                count = 0
                start_offset = 0
                start_offset_set = False
            offset += self.entry_size
        return cache

    def find_place_for_entry(self, directory_start_cluster,entries_number):
        clusters = self.core.fat_tripper.get_file_clusters_list(directory_start_cluster)
        cache = (False,[])
        for cluster in clusters:
            cache = self.find_place_for_entry_on_current_cluster(cluster, entries_number)
            if cache[0]:
                break
        return cache

    def delete_file_entry(self):
        pass

    def delete_fat_chain(self):
        pass
    def delete_file_with_clean(self):
        pass

    def delete_directory_with_clean(self):
        pass

    def delete_file_without_clean(self):
        pass
    def delete_directory_without_clean(self):
        pass