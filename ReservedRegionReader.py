import ImageWorker
import Structures


class BootSectorParser(Structures.FatBootSectorStructure):
    def __init__(self, reader: ImageWorker.ImageReader):
        super().__init__()
        self.reader = reader
        self.bs_jmp_boot = self.reader.get_data_local(0, 3)  # 0 3
        self.bs_oem_name = self.reader.get_data_local(3, 8)  # 3 8
        self.bpb_bytes_per_sector = self.reader.get_data_local(11, 2, True)  # 11 2
        self.bpb_sectors_per_cluster = self.reader.get_data_local(13, 1, True)  # 13 1
        self.bpb_reserved_region_sectors_count = self.reader.get_data_local(14, 2, True)  # 14 2
        self.bpb_number_fats = self.reader.get_data_local(16, 1, True)  # 16 1
        self.bpb_root_entry_count = self.reader.get_data_local(17, 2, True)  # 17 2 for fat32 it zero
        self.bpb_total_sectors_16 = self.reader.get_data_local(19, 2, True)  # 19 2 old field in fat 32 must be zero
        self.bpb_media = self.reader.get_data_local(21, 1)  # 21 1 stand
        self.bpb_fat_size_16 = self.reader.get_data_local(22, 2, True)  # 22 2
        self.bpb_sectors_per_track = self.reader.get_data_local(24, 2, True)  # 24 2
        self.bpb_number_heads = self.reader.get_data_local(26, 2, True)  # 26 2 amount of disk heads
        self.bpb_hidden_sectors = self.reader.get_data_local(28, 4, True)  # 28 4
        self.bpb_total_sectors_32 = self.reader.get_data_local(32, 4, True)  # 32 4 new 32 bit field sm old 16 bit field
        self.bpb_fat_size_32 = self.reader.get_data_local(36, 4, True)  # 36 4 amount of sectors one fat
        self.bpb_ext_flags = self.reader.get_data_local(40, 2)  # 40 2
        self.file_system_version = self.reader.get_data_local(42, 2)  # 42 2
        self.bpb_root_cluster = self.reader.get_data_local(44, 4, True)  # 44 4
        self.bpb_file_system_information = self.reader.get_data_local(48, 2, True)  # 48 2
        self.bpb_backup_boot_sector = self.reader.get_data_local(50, 2, True)  # 50 2
        self.bpb_reserved = self.reader.get_data_local(52, 12)  # 52 12
        self.bs_driver_number = self.reader.get_data_local(64, 1)  # 64 1
        self.bs_reserved1 = self.reader.get_data_local(65, 1)  # 65 1
        self.bs_boot_signature = self.reader.get_data_local(66, 1)  # 66 1
        self.bs_volume_id = self.reader.get_data_local(67, 4)  # 67 4
        self.bs_volume_label = self.reader.get_data_local(71, 11)  # 71 11
        self.bs_file_system_type = self.reader.get_data_local(82, 8)  # 82 8

        self._cluster_size = self.bpb_sectors_per_cluster * self.bpb_bytes_per_sector
        self._fat_zone_offset = self.bpb_bytes_per_sector * self.bpb_reserved_region_sectors_count
        self._root_directory_offset = self.fat_zone_offset + self.bpb_number_fats * self.bpb_fat_size_32 \
                                                             * self.bpb_bytes_per_sector
        self._fat_size = (self.root_directory_offset - self.fat_zone_offset) // self.bpb_number_fats
        self._fat_offsets_list = self._fat_offsets_list()

    def _fat_offsets_list(self):
        fats_offsets = []
        for fat_number in range(self.bpb_number_fats):
            current_sector = self.bpb_reserved_region_sectors_count + self.bpb_fat_size_32 * fat_number
            fats_offsets.append(current_sector * self.bpb_bytes_per_sector)
        return tuple(fats_offsets)

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
