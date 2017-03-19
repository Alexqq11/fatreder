import struct

import Structures
from FatReaderExceptions import *


class FatTablesManager(Structures.Asker):
    def __init__(self, core, check_fats=True):
        super().__init__()
        self._core = core
        self._fats_amount = len(core.fat_boot_sector.fat_offsets_list)
        self._fats_offsets = core.fat_boot_sector.fat_offsets_list
        active, mirroring = core.fat_boot_sector.active_fat
        self._fats_mirroring = mirroring
        self._active_fat_number = active
        self._main_fat = FatTable(core, self._fats_offsets[active])
        self._fats = []  # [FatTable(core, offset) for offset in self._fats_offsets]
        if check_fats:
            self._fats = [FatTable(core, offset) for offset in self._fats_offsets]
            self.check_fats()

    def set_mapped_for_chain(self, cluster):
        self._main_fat.set_mapped_for_chain(cluster)

    def clear_fat_trash(self):
        self._main_fat.clear_fat_trash()

    def get_next(self, cluster):
        return self._main_fat[cluster] if self._main_fat[cluster] < 268435448 else cluster

    def fix_cycle(self, start_cluster , cut_position):
        self._main_fat.fix_cycle(start_cluster, cut_position)

    def set_cluster_entry(self, cluster_number, value = 268435448):
        self._main_fat[cluster_number] = value
        self.flush()
    def get_file_clusters_list(self, cluster):
        return list(self._main_fat.file_clusters_stream(cluster))
    def find_empty_entries(self, amount):
        return self._main_fat.find_empty_clusters(amount)
    def allocate_place(self, amount_of_clusters):
        value = self._main_fat.allocate_place(amount_of_clusters)
        self.flush()
        return value

    def extend_file(self, file_start_cluster, amount_of_clusters):
        value = self._main_fat.extend_file(file_start_cluster, amount_of_clusters)
        self.flush()
        return value

    def calculate_free_space(self):
        return self._main_fat.calculate_free_space()

    def get_file_clusters_offsets_list(self, cluster):
        return self._main_fat.get_file_clusters_offsets_list(cluster)

    def delete_file_fat_chain(self, cluster, set_end=False):
        self._main_fat.delete_file_fat_chain(cluster, set_end)
        self.flush()

    def flush(self):
        if self._fats_mirroring:
            self._main_fat.flush_in_offsets(self._fats_offsets, True)
        else:
            self._main_fat.flush()

    def check_fats(self):
        if self._fats_mirroring:
            fat_zero = self._fats[0]
            correct_state = True
            for fat in self._fats:
                if not fat_zero == fat:
                    correct_state = False
            if not correct_state:
                self.sync_fat_choice()
        else:
            self._fats = []

    def sync_fat_choice(self):
        choices = []
        for number, fat in enumerate(self._fats):
            question = "{}. : fat number {} free space in bytes {}b".format(number, number, fat.calculate_free_space())
            choices.append(question)
        ans = self.ask_choice_list("we want to sync fat tables , please select one main from list,\n" +
                                   " we suggest choice option with smallest free size!\n you make it at own risk\n ",
                                   choices)
        main_fat = self._fats[int(ans)]
        main_fat.flush_in_offsets(self._fats_offsets)
        self._fats = []


class FatTable:
    def __init__(self, core, offset, data=None):
        self._core = core
        self._offset = offset
        if data is None:
            data = core.image_reader.get_data_global(offset, core.fat_boot_sector.fat_size)
        self._max_allocation = min(core.fat_boot_sector.max_allocation, len(data) // 4)
        self._byte_data = [data[x:x + 4] for x in range(0, self._max_allocation * 4, 4)]
        self._mapped_memory = None

    def _init_mapped(self):
        self._mapped_memory = [False for x in range(len(self._byte_data))]
        self._mapped_memory[0] = True
        self._mapped_memory[1] = True

    def set_mapped_for_chain(self, data_cluster):
        if self._mapped_memory is None:
            self._init_mapped()
        for cluster_number in self.file_clusters_stream(data_cluster):
            self._mapped_memory[cluster_number] = True

    def clear_fat_trash(self):
        for cluster_number , mapped_status in enumerate(self._mapped_memory):
            if not mapped_status and cluster_number > 1:
                self[cluster_number] = 0
        self._del_mapped()
    def _del_mapped(self):
        self._mapped_memory = []

    def _get_fat_entry_global_offset(self, cluster):
        return cluster * 4 + self._offset

    def get_file_clusters_offsets_list(self, cluster):
        return [self._core.fat_boot_sector.calc_cluster_offset(cls) for cls in self.file_clusters_stream(cluster)]

    def file_clusters_stream(self, cluster_number):
        while cluster_number < 268435448:
            yield cluster_number
            cluster_number = self[cluster_number]

    def fix_cycle(self, start_cluster, cut_position):
        for number , cluster in enumerate(self.file_clusters_stream(start_cluster)):
            if number == cut_position:
                self[cluster] = 268435448
                break

    def allocate_place(self, amount_of_clusters):
        empty_clusters = self.find_empty_clusters(1)
        if self[empty_clusters[0]] == 0:
            self[empty_clusters[0]] = 268435448
        else:
            raise UnExpectedCriticalError("be shure it never happens founded shredinger cluster")
        try:
            self.extend_place(empty_clusters[0], amount_of_clusters - 1)
        except AllocationMemoryOutException:
            self[empty_clusters[0]] = 0
            raise  AllocationMemoryOutException
        return empty_clusters[0]

    def extend_file(self, file_start_cluster, amount_of_clusters):  # now it works correctly with any cluster of file
        last, *trash = tuple(self.file_clusters_stream(file_start_cluster))[-1:]
        self.extend_place(last, amount_of_clusters)
        return last

    def extend_place(self, last_cluster, amount_of_clusters):
        empty_clusters_list = self.find_empty_clusters(amount_of_clusters)
        return self._extend_file(empty_clusters_list, last_cluster)

    def _extend_file(self, empty_clusters_list, last_cluster):
        current_cluster = last_cluster
        for next_cluster in empty_clusters_list:
            self[current_cluster] = next_cluster
            current_cluster = next_cluster
        self[current_cluster] = 268435448

    def delete_file_fat_chain(self, cluster, set_end=False):
        next_cluster = self[cluster]
        if set_end:
            self[cluster] = 268435448
        else:
            self[cluster] = 0
        if next_cluster < 268435448:
            return self.delete_file_fat_chain(next_cluster)

    def calculate_free_space(self):
        free_clusters_amount = 0
        for cluster in self.free_clusters_stream():
            free_clusters_amount +=1
        return free_clusters_amount * self._core.fat_boot_sector.cluster_size

    def find_empty_clusters(self, amount_of_clusters):
        clusters_list = []
        for number, cluster in enumerate(self.free_clusters_stream()):
            if number < amount_of_clusters:
                clusters_list.append(cluster)
            else:
                break
        if len(clusters_list) < amount_of_clusters:
            raise AllocationMemoryOutException()
        return clusters_list

    def free_clusters_stream(self):
        for cluster_number , cluster_value in self:
            if cluster_value == 0:
                yield cluster_number

    def get_raw_data(self):
        return b"".join(self._byte_data)

    def __getitem__(self, item):
        if item > 1:
            value, *trash = struct.unpack('<I', self._byte_data[item])
            return value
        else:
            raise IndexError("Index must be more than 1")

    def __iter__(self):
        for cluster_number, cluster_value in enumerate(self._byte_data):
            value, *trash = struct.unpack('<I', cluster_value)
            if cluster_number > 1:
                yield (cluster_number, value)

    def __len__(self):
        return self._max_allocation

    def __setitem__(self, key, value):
        value = struct.pack('<I', value)
        self._byte_data[key] = value

    def __eq__(self, other):
        return self._byte_data == other._byte_data

    def flush(self):
        self._core.image_reader.set_data_global(self._offset, b''.join(self._byte_data))

    def flush_in_offsets(self, offsets, flush_self=False):
        for offset in offsets:
            if offset != self._offset or flush_self:
                self._core.image_reader.set_data_global(offset, b''.join(self._byte_data))

