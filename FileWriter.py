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

    def allocate_place(self, size_in_bytes, clear_allocated_area=True):
        """
        return first_data_cluster of allocated area and operation status
        """
        clusters_amount = self.count_clusters(size_in_bytes)
        data_cluster , operation_status = self.core.fat_tripper.allocate_place(clusters_amount)
        if operation_status:
            self.delete_data_clusters(data_cluster)
        return  data_cluster , operation_status

    def get_file_allocation_offsets(self, cluster_number):
        return self.core.fat_tripper.get_file_clusters_offsets_list(cluster_number)

    def find_place_for_entry_on_current_cluster(self, cluster_offset , entries_number , entries_offsets_in, allocation_status_in):# something wrong here
        offset = cluster_offset
        start_offset = cluster_offset
        entries_offsets = entries_offsets_in
        allocation_status = allocation_status_in
        count = 0
        while offset < self.cluster_size + cluster_offset:
            check_byte = self.image_reader.get_data_global(offset, 1)
            if check_byte in [b'\x00', b'\xe5']:
                if count == 0:
                    start_offset = offset
                count += 1
                if count == entries_number:
                    allocation_status = True
                    break
            else:
                count = 0
            offset += self.entry_size
            # entries_offsets = [offset for offset in range(start_offset, offset + 1, self.entry_size)]
        entries_offsets = [offset for offset in range(start_offset, start_offset + count * self.entry_size , self.entry_size)]
        # cdif count == 0: entries_offsets = []
        return entries_offsets , allocation_status

    def find_place_for_entry(self, directory_start_cluster, entries_number):
        clusters_offsets = self.core.fat_tripper.get_file_clusters_offsets_list(directory_start_cluster)
        entries_offsets = []
        allocation_status = False
        for cluster_offset in clusters_offsets:
            if allocation_status:
                break
            else:
                entries_offsets , allocation_status = self.find_place_for_entry_on_current_cluster(cluster_offset, entries_number , entries_offsets, allocation_status) #something wrong here

        return entries_offsets, allocation_status

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
            self.copy_entry_writes(entry_place,entry_entries)
            if "d" in attr:
                self._add_directory_writes(destination_directory, start_cluster)

        else:
            # race no memory exception
            pass
    def _add_directory_writes(self, parent_directory: DiSt.Directory , dir_data_cluster):
        parent_entries = self.file_entry_creator.new_entry('..', 'd', parent_directory.data_cluster ,self.cluster_size, tuple())
        current_entries = self.file_entry_creator.new_entry('.','d', dir_data_cluster, self.cluster_size,tuple())
        entry_entries = [parent_entries[0],current_entries[0]]
        entry_place, found_successfully = self.find_place_for_entry(dir_data_cluster, 2)
        self.copy_entry_writes(entry_place, entry_entries)

    def rename(self,new_name, destination_directory : DiSt.Directory,file_source : FeC.FileEntry):
        dir_listing = destination_directory.short_names
        entry_entries = self.file_entry_creator.new_entry(new_name, file_source.attr_string, file_source.data_cluster, file_source.size, dir_listing, file_source.datetime)
        entry_place, found_successfully = self.find_place_for_entry(destination_directory.data_cluster,
                                                                    len(entry_entries))
        if not found_successfully:
            correct_successfully = self.not_found_processing(destination_directory.data_cluster)
            entry_place, found_successfully = self.find_place_for_entry(destination_directory.data_cluster,
                                                                        len(entry_entries))
            if not (correct_successfully and found_successfully):
                # race no memory exception
                pass
        self.copy_entry_writes(entry_place, entry_entries)
        self.delete_file_entry(file_source.entries_offsets, True)


    def transfer_file(self,destination_directory : DiSt.Directory,file_source : FeC.FileEntry):
        dir_listing = destination_directory.short_names
        entry_entries = self.file_entry_creator.new_entry(file_source.name, file_source.attr_string, file_source.data_cluster, file_source.size, dir_listing, file_source.datetime)
        entry_place, found_successfully = self.find_place_for_entry(destination_directory.data_cluster, len(entry_entries))
        if not found_successfully:
            correct_successfully = self.not_found_processing(destination_directory.data_cluster)
            entry_place, found_successfully = self.find_place_for_entry(destination_directory.data_cluster,len(entry_entries))
            if not (correct_successfully and found_successfully):
                # race no memory exception
                pass
        self.copy_entry_writes(entry_place, entry_entries)
        self.delete_file_entry(file_source.entries_offsets, True)





    def copy_file(self,destination_directory : DiSt.Directory, file_source : FeC.FileEntry):
         #TODO extend dir if it need
        first_data_cluster, allocated_successfully = self.allocate_place(file_source.size) # TODO  don't belive Size attr,  count it itself
        if allocated_successfully:
            dir_listing = destination_directory.short_names
            entry_entries = self.file_entry_creator.new_entry(file_source.name, file_source.attr_string, first_data_cluster, file_source.size, dir_listing)
            entry_place, found_successfully = self.find_place_for_entry(destination_directory.data_cluster,
                                                                        len(entry_entries))
            if not found_successfully:
                correct_successfully = self.not_found_processing(destination_directory.data_cluster)
                entry_place, found_successfully = self.find_place_for_entry(destination_directory.data_cluster,len(entry_entries))
                if not (correct_successfully and found_successfully):
                    # race no memory exception
                    pass
            self.copy_entry_writes(entry_place, entry_entries)
            self.copy_file_data(file_source, first_data_cluster)
        else:
            # race no memory exception
            pass


    def copy_entry_writes (self, entry_place, entry_entries ):
        entry_place.reverse() # todo optimaze it
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