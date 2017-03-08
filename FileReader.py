import struct

import DirectoryDescriptor
import FileDescriptor
from FatReaderExceptions import CoreNotInitedError


class DataParser:
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

    def parse_non_buffer(self, file_cluster_number):
        self._set_default_settings()
        self._set_work_settings(file_cluster_number)
        for cluster_offset in self.data_clusters_offsets_list:
            yield self.image_reader.get_data_global(cluster_offset, self.cluster_size)  # ???


class DirectoryParser:
    def __init__(self):
        self._core = None
        self._reader = None
        self._fat_table = None
        self._fat_bpd = None
        self._directory_data = []
        self._file_descriptors = []
        self._core_inited = False
        pass

    def init_core(self, core):
        self._core = core
        self._reader = core.image_reader
        self._fat_table = core.fat_tripper
        self._fat_bpd = core.fat_bot_sector
        self._core_inited = True

    def parse_at_cluster(self, directory_cluster):
        if not self._core_inited:
            raise CoreNotInitedError()
        self._directory_data = []
        self._file_descriptors = []
        self._parse_directory_raw_data(directory_cluster)
        self._parse_directory_from_raw_data()
        return DirectoryDescriptor.DirectoryDescriptor(self._core, self._file_descriptors, self._directory_data)

    def _parse_directory_raw_data(self, directory_cluster):
        directory_offsets = self._fat_table.get_file_clusters_offsets_list(directory_cluster)
        for offset in directory_offsets:
            data = self._reader.get_data_global(offset, self._fat_bpd.cluster_size)
            for entry_pointer in range(0, self._fat_bpd.cluster_size, 32):
                entry_data = data[entry_pointer: entry_pointer + 32]
                self._directory_data.append((entry_data, offset + entry_pointer, self._is_free(entry_data)))

    @staticmethod
    def _is_end_lfn(data, number):
        ldir_order_byte, *_ = struct.unpack("<B", data[0:1])
        return ((4 * 16) == (ldir_order_byte & (4 * 16))) and (((4 * 16) | number) == ldir_order_byte)

    def _is_correct_lfn(self, data, number):
        ldir_order_byte, *_ = struct.unpack("<B", data[0 : 1])
        return ldir_order_byte == number or self._is_end_lfn(data, number)  # todo add hash checks

    def _is_dir(self, data):
        return not (self._is_free(data) or self._is_lfn(data))

    @staticmethod
    def _is_free(data):
        first_entry_byte = data[0]
        return first_entry_byte in [b'\xe5', b'\x00']

    def _is_lfn(self, data):
        attr_entry_byte, *_ = struct.unpack("<B", data[11:12])
        mask = 2 ** 6 - 1
        return ((attr_entry_byte & mask) == 15) and (not self._is_free(data))

    def _parse_directory_from_raw_data(self):
        for number, (data, offset, is_free) in enumerate(self._directory_data):
            if not is_free:
                if self._is_dir(data):
                    data_slice = self._parse_current_entry(number)
                    new_directory = FileDescriptor.FileDescriptor()
                    new_directory.new_entry_from_bytes(self._directory_data[data_slice])
                    self._file_descriptors.append(new_directory)

    def _parse_current_entry(self, entry_number):
        slice_end = entry_number + 1
        slice_start = entry_number
        previous = 0
        if entry_number == 0:
            return slice(slice_start, slice_end)
        entry_number -= 1  # now we parsing lfn
        while True:
            data, offset, is_free = self._directory_data[entry_number]
            if is_free or self._is_dir(data) or not (self._is_lfn(data) and self._is_correct_lfn(data, previous + 1)):
                entry_number += 1
                slice_start = entry_number
                break
            else:
                if self._is_end_lfn(data, previous + 1):
                    slice_start = entry_number
                    break
                else:
                    previous += 1
                    entry_number -= 1
                    if entry_number == -1:  # todo think about system that says if directory entry is corrupted
                        entry_number += 1
                        slice_start = entry_number
                        break
        return slice(slice_start, slice_end)

    def parse_at_offset(self, directory_offset):
        self.parse_at_cluster(self._fat_bpd.calc_cluster_number(directory_offset))
