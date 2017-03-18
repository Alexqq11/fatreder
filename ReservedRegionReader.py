import ImageWorker
import Structures
import struct

class BootSectorParser(Structures.FatBootSectorStructure):
    def __init__(self, data):
        super().__init__()
        self.data_offset = Structures.BootSectorOffsets()
        self._data = data  # check data ?
        self.bs_jmp_boot = self.get_data(0, 3)  # 0 3
        self.bs_oem_name = self.get_data(3, 8)  # 3 8
        self.bpb_bytes_per_sector = self.get_data(11, 2, True)  # 11 2
        self.bpb_sectors_per_cluster = self.get_data(13, 1, True)  # 13 1
        self.bpb_reserved_region_sectors_count = self.get_data(14, 2, True)  # 14 2
        self.bpb_number_fats = self.get_data(16, 1, True)  # 16 1
        self.bpb_root_entry_count = self.get_data(17, 2, True)  # 17 2 for fat32 it zero
        self.bpb_total_sectors_16 = self.get_data(19, 2, True)  # 19 2 old field in fat 32 must be zero
        self.bpb_media = self.get_data(21, 1)  # 21 1 stand
        self.bpb_fat_size_16 = self.get_data(22, 2, True)  # 22 2
        self.bpb_sectors_per_track = self.get_data(24, 2, True)  # 24 2
        self.bpb_number_heads = self.get_data(26, 2, True)  # 26 2 amount of disk heads
        self.bpb_hidden_sectors = self.get_data(28, 4, True)  # 28 4
        self.bpb_total_sectors_32 = self.get_data(32, 4, True)  # 32 4 new 32 bit field sm old 16 bit field
        self.bpb_fat_size_32 = self.get_data(36, 4, True)  # 36 4 amount of sectors one fat
        self.bpb_ext_flags = self.get_data(40, 2)  # 40 2
        self.file_system_version = self.get_data(42, 2)  # 42 2
        self.bpb_root_cluster = self.get_data(44, 4, True)  # 44 4
        self.bpb_file_system_information = self.get_data(48, 2, True)  # 48 2
        self.bpb_backup_boot_sector = self.get_data(50, 2, True)  # 50 2
        self.bpb_reserved = self.get_data(52, 12)  # 52 12
        self.bs_driver_number = self.get_data(64, 1)  # 64 1
        self.bs_reserved1 = self.get_data(65, 1)  # 65 1
        self.bs_boot_signature = self.get_data(66, 1)  # 66 1
        self.bs_volume_id = self.get_data(67, 4)  # 67 4
        self.bs_volume_label = self.get_data(71, 11)  # 71 11
        self.bs_file_system_type = self.get_data(82, 8)  # 82 8

        self._cluster_size = self.bpb_sectors_per_cluster * self.bpb_bytes_per_sector
        self._fat_zone_offset = self.bpb_bytes_per_sector * self.bpb_reserved_region_sectors_count
        self._root_directory_offset = self.fat_zone_offset
        self._root_directory_offset += self.bpb_number_fats * self.bpb_fat_size_32 * self.bpb_bytes_per_sector
        self._fat_size = (self.root_directory_offset - self.fat_zone_offset) // self.bpb_number_fats
        self._fat_offsets_list = self._fat_offsets_list()
        self._data_clusters_amount = self._calc_data_clusters()

    @staticmethod
    def _get_parse_mod(size):
        mod_parameter = ''
        if size == 1:
            mod_parameter = '<B'
        elif size == 2:
            mod_parameter = '<H'
        elif size == 4:
            mod_parameter = '<I'
        return mod_parameter

    def convert_to_int(self, data, size):
        value, *trash = struct.unpack(self._get_parse_mod(size), data)
        return value

    def get_data(self, offset, length, parse = False):
        if parse:
            return self.convert_to_int(self._data[offset: offset + length], length)
        else:
            return self._data[offset: offset + length]

    def _calc_data_clusters(self):
        data_sectors = self.bpb_total_sectors_32 - (self.root_directory_offset // self.bpb_bytes_per_sector)
        return data_sectors // self.bpb_sectors_per_cluster

    def _fat_offsets_list(self):
        fats_offsets = []
        for fat_number in range(self.bpb_number_fats):
            current_sector = self.bpb_reserved_region_sectors_count + self.bpb_fat_size_32 * fat_number
            fats_offsets.append(current_sector * self.bpb_bytes_per_sector)
        return tuple(fats_offsets)

    @property
    def data_clusters_amount(self):
        return self._data_clusters_amount

    @property
    def max_allocation(self):
        return self.data_clusters_amount + 2

    @property
    def cluster_size(self):  # use it
        return self._cluster_size

    @property
    def fat_zone_offset(self):
        return self._fat_zone_offset

    @property
    def fat_offsets_list(self):
        return self._fat_offsets_list

    @property
    def fat_size(self):
        return self._fat_size

    @property
    def root_directory_offset(self):
        return self._root_directory_offset

    def calc_cluster_offset(self, cluster_number):
        offset = (cluster_number - 2) * self.bpb_sectors_per_cluster * self.bpb_bytes_per_sector
        offset += self.root_directory_offset
        return offset

    def calc_cluster_number(self, cluster_offset):
        number = cluster_offset - self.root_directory_offset
        number = number // (self.bpb_sectors_per_cluster * self.bpb_bytes_per_sector) + 2
        return number
