import FileEntryCollector as FeC
import FileEntryCreator
import DirectoriesStructures as DiSt
import FileReader as FR
class FileWriter():
    def __init__(self, core):
        self.core = core
        self.image_reader = core.image_reader
        self.entry_size = 32
        self.cluster_size = core.fat_bot_sector.cluster_size
        self.file_entry_creator = FileEntryCreator.FileEntryCreator()
        self.file_data_reader = FR.DataParser(core)

    def count_clusters(self, size_in_bytes): # TODO correct
        return (size_in_bytes + self.cluster_size - 1) // self.cluster_size


    def extend_file(self, directory_start_cluster, size_in_bytes): #TODO correct
        clusters_amount = self.count_clusters(size_in_bytes)
        clusters = self.core.fat_tripper.get_file_clusters_list(directory_start_cluster)
        extended_cluster = clusters[len(clusters) - 1]
        status = self.core.fat_tripper.extend_file(extended_cluster, clusters_amount)
        return status

    def allocate_place(self, size_in_bytes):
        """
        return first_data_cluster of allocated area and operation status
        """
        clusters_amount = self.count_clusters(size_in_bytes)
        return  self.core.fat_tripper.allocate_place(clusters_amount)

    def get_file_allocation_offsets(self, cluster_number):
        return self.core.fat_tripper.get_file_clusters_offsets_list(cluster_number)

    def find_place_for_entry_on_current_cluster(self, entries_number):# something wrong here
        directory_offset = self.core.fat_bot_sector.calc_cluster_offset()
        offset = directory_offset
        count = 0
        start_offset = 0
        start_offset_set = False
        cache = ([], False)
        while offset < self.cluster_size + directory_offset:
            check_byte = self.image_reader.get_data_global(offset, 1)
            if check_byte in [b'\x00', b'\xe5']:
                if not start_offset_set:
                    start_offset = offset
                    start_offset_set = True
                count += 1
                if count == entries_number:
                    cache = ([offset for offset in range(start_offset, offset + 1, self.entry_size)], True)
                    break
            else:
                count = 0
                start_offset = 0
                start_offset_set = False
            offset += self.entry_size
        return cache

    def find_place_for_entry(self, directory_start_cluster, entries_number):
        clusters = self.core.fat_tripper.get_file_clusters_list(directory_start_cluster)
        cache = ([], False)
        for cluster in clusters:
            cache = self.find_place_for_entry_on_current_cluster(entries_number) #something wrong here
            if cache[0]:
                break
        return cache

    def not_found_processing(self, directory_data_cluster):
        return self.extend_file(directory_data_cluster, self.cluster_size)

    def new_file(self, name, attr ,destination_directory : DiSt.Directory ):
        start_cluster, allocated_successfully = self.allocate_place(self.cluster_size)
        if allocated_successfully:
            dir_list = destination_directory.short_names
            entry_entries = self.file_entry_creator.new_entry(name, attr, start_cluster , self.cluster_size, dir_list)
            entry_place, found_successfully = self.find_place_for_entry(destination_directory.data_cluster, len(entry_entries))
            if not found_successfully:
                correct_successfully = self.not_found_processing(destination_directory.data_cluster)
                entry_place, found_successfully = self.find_place_for_entry(destination_directory.data_cluster, len(entry_entries))
                if not (correct_successfully and found_successfully):
                    # race no memory exception
                    pass
            for x in range(len(entry_place)):
                self.image_reader.set_data_global(entry_place[x], entry_entries[x])
        else:
            # race no memory exception
            pass


    def rename(self,new_name, destination_directory : DiSt.Directory,file_source : FeC.FileEntry):
        entry_place, found_successfully = self.find_place_for_entry(destination_directory.data_cluster, len(file_source.entries_offsets))
        if not found_successfully:
            correct_successfully = self.not_found_processing(destination_directory.data_cluster)
            entry_place, found_successfully = self.find_place_for_entry(destination_directory.data_cluster, len(file_source.entries_offsets))
            if not (correct_successfully and found_successfully):
                # race no memory exception
                pass
        dir_listing = destination_directory.short_names
        entry_entries = self.file_entry_creator.new_entry(new_name, file_source.attr_string, file_source.data_cluster, file_source.size, dir_listing, file_source.datetime)
        self.copy_entry_writes(entry_place, entry_entries)
        self.delete_file_entry(file_source.entries_offsets, True)


    def transfer_file(self,destination_directory : DiSt.Directory,file_source : FeC.FileEntry):
        entry_place, found_successfully = self.find_place_for_entry(destination_directory.data_cluster, len(file_source.entries_offsets))
        if not found_successfully:
            correct_successfully = self.not_found_processing(destination_directory.data_cluster)
            entry_place, found_successfully = self.find_place_for_entry(destination_directory.data_cluster, len(file_source.entries_offsets))
            if not (correct_successfully and found_successfully):
                # race no memory exception
                pass
        dir_listing = destination_directory.short_names
        entry_entries = self.file_entry_creator.new_entry(file_source.name, file_source.attr_string, file_source.data_cluster, file_source.size, dir_listing, file_source.datetime)
        self.copy_entry_writes(entry_place, entry_entries)
        self.delete_file_entry(file_source.entries_offsets, True)





    def copy_file(self,destination_directory : DiSt.Directory, file_source : FeC.FileEntry):
        entry_place , found_successfully = self.find_place_for_entry(destination_directory.data_cluster, len(file_source.entries_offsets)) #TODO extend dir if it need
        first_data_cluster, allocated_successfully = self.allocate_place(file_source.size)
        if allocated_successfully:
            if not found_successfully:
                correct_successfully = self.not_found_processing(destination_directory.data_cluster)
                entry_place, found_successfully = self.find_place_for_entry(destination_directory.data_cluster,len(file_source.entries_offsets))
                if not (correct_successfully and found_successfully):
                    # race no memory exception
                    pass
            dir_listing = destination_directory.short_names
            entry_entries = self.file_entry_creator.new_entry(file_source.name, file_source.attr_string, first_data_cluster, file_source.size, dir_listing)
            self.copy_entry_writes(entry_place, entry_entries)
            self.copy_file_data(file_source, first_data_cluster)
        else:
            # race no memory exception
            pass


    def copy_entry_writes (self, entry_place, entry_entries ):
        entry_place = entry_place.reverse() # todo optimaze it
        for x in range(len(entry_place)):
            self.image_reader.set_data_global(entry_place[x], entry_entries[x])

    def copy_file_data(self, file_source : FeC.FileEntry, destination_first_cluster ):
        destination_allocation = self.get_file_allocation_offsets(destination_first_cluster)
        pointer = 0
        for data in self.file_data_reader.parse_non_buffer(file_source.data_cluster):
            self.image_reader.set_data_global(destination_allocation[pointer], data)
            pointer += 1



    def delete_directory_or_file(self, file_entry : FeC.FileEntry , recoverable=True, clean=False):
        if clean:
            self.delete_data_clusters(file_entry.data_cluster)
            self.delete_fat_chain(file_entry.data_cluster)
            self.delete_file_entry(file_entry.entries_offsets, True)
        elif recoverable:
            self.delete_file_entry(file_entry.entries_offsets)
        else:
            self.delete_fat_chain(file_entry.data_cluster)
            self.delete_file_entry(file_entry.entries_offsets, True)

    def delete_file_entry(self, file_entries_offsets, clean=False):
        data = b'\xe5'
        if clean:
            data = b'\x00' * 32
        for file_entry_offset in file_entries_offsets:
            self.image_reader.set_data_global(file_entry_offset, data)


    def delete_fat_chain(self, start_cluster):
        self.core.fat_tripper.delete_file_fat_chain(start_cluster)

    def delete_data_clusters(self, start_cluster):
        offsets = self.core.fat_tripper.get_file_clusters_offsets_list(start_cluster)
        zero_cluster = b'\x00' * self.cluster_size
        for offset in offsets:
            self.image_reader.set_data_global(offset, zero_cluster)