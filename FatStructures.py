class FatBootSector:
    def __init__(self, image_reader):
        self.reader = image_reader
        self.bs_jmp_boot = None  # 0 3
        self.bs_oem_name = None  # 3 8
        self.bpb_bytes_per_sector = None  # 11 2
        self.bpb_sectors_per_cluster = None  # 13 1
        self.bpb_reserved_region_sectors_count = None  # 14 2
        self.bpb_number_fats = None  # 16 1
        self.bpb_root_entry_count = None  # 17 2 for fat32 it zero
        self.bpb_total_sectors_16 = None  # 19 2 old sixteen bits field in fat 32 must be zero
        self.bpb_media = None  # 21 1 stand
        self.bpb_fat_size_16 = None  # 22 2 amount fat sectors for one fat12/16 table in fat32 zero watch to fat 32
        self.bpb_sectors_per_track = None  # 24 2 for interrupt 13 and accses to disks with geometry #old tech
        self.bpb_number_heads = None  # 26 2 ammount of disk heads
        self.bpb_hidden_sectors = None  # 28 4
        self.bpb_total_sectors_32 = None  # 32 4 new 32 bit field sm old 16 bit field
        # there was can been fat12/16 fields but we starting write fat 32 fields
        self.bpb_fat_size_32 = None  # 36 4 amoun of sectors one fat
        self.bpb_ext_flags = None  # 40 2
        self.file_system_version = None  # 42 2
        self.bpb_root_cluster = None  # 44 4
        self.bpb_file_system_information = None  # 48 2
        self.bpb_backup_boot_sector = None  # 50 2
        self.bpb_reserved = None  # 52 12
        self.bs_driver_number = None  # 64 1
        self.bs_reserved1 = None  # 65 1
        self.bs_boot_signature = None  # 66 1
        self.bs_volume_id = None  # 67 4
        self.bs_volume_label = None  # 71 11
        self.bs_file_system_type = None  # 82 8
        self._read_fat_boot_sector()

    def get_fat_offset(self):
        return self.bpb_bytes_per_sector * self.bpb_reserved_region_sectors_count

    def get_fat_offsets_list(self):
        return (self.bpb_bytes_per_sector * (self.bpb_reserved_region_sectors_count + self.bpb_fat_size_32 * x) for x in
                range(1, self.bpb_number_fats + 1))

    def get_root_dir_offset(self):
        return self.get_fat_offset() + self.bpb_number_fats * self.bpb_fat_size_32 * self.bpb_bytes_per_sector

    def get_cluster_offset(self, cluster_number):
        offset = (cluster_number - 2) * self.bpb_sectors_per_cluster * self.bpb_sectors_per_cluster
        offset += self.get_root_dir_offset()
        return offset

    def _read_fat_boot_sector(self):
        self.bs_jmp_boot = self.reader.get_data(0, 3)  # 0 3
        self.bs_oem_name = self.reader.get_data(3, 8)  # 3 8
        self.bpb_bytes_per_sector = self.reader.get_data(11, 2, True)  # 11 2
        self.bpb_sectors_per_cluster = self.reader.get_data(13, 1, True)  # 13 1
        self.bpb_reserved_region_sectors_count = self.reader.get_data(14, 2, True)  # 14 2
        self.bpb_number_fats = self.reader.get_data(16, 1, True)  # 16 1
        self.bpb_root_entry_count = self.reader.get_data(17, 2, True)  # 17 2 for fat32 it zero
        self.bpb_total_sectors_16 = self.reader.get_data(19, 2,
                                                         True)  # 19 2 old sixteen bits field in fat 32 must be zero
        self.bpb_media = self.reader.get_data(21, 1)  # 21 1 stand
        self.bpb_fat_size_16 = self.reader.get_data(22, 2,
                                                    True)  # 22 2 amount fat sectors for one fat12/16 table
        self.bpb_sectors_per_track = self.reader.get_data(24, 2,
                                                          True)  # 24 2 for interrupt 13 and accses to disks
        self.bpb_number_heads = self.reader.get_data(26, 2, True)  # 26 2 ammount of disk heads
        self.bpb_hidden_sectors = self.reader.get_data(28, 4, True)  # 28 4
        self.bpb_total_sectors_32 = self.reader.get_data(32, 4, True)  # 32 4 new 32 bit field sm old 16 bit field
        # there was can been fat12/16 fields but we starting write fat 32 fields
        self.bpb_fat_size_32 = self.reader.get_data(36, 4, True)  # 36 4 amoun of sectors one fat
        self.bpb_ext_flags = self.reader.get_data(40, 2)  # 40 2
        self.file_system_version = self.reader.get_data(42, 2)  # 42 2
        self.bpb_root_cluster = self.reader.get_data(44, 4, True)  # 44 4
        self.bpb_file_system_information = self.reader.get_data(48, 2,
                                                                True)  # 48 2 кол-во свободных кластеров на диске
        self.bpb_backup_boot_sector = self.reader.get_data(50, 2, True)  # 50 2
        self.bpb_reserved = self.reader.get_data(52, 12)  # 52 12
        self.bs_driver_number = self.reader.get_data(64, 1)  # 64 1
        self.bs_reserved1 = self.reader.get_data(65, 1)  # 65 1
        self.bs_boot_signature = self.reader.get_data(66, 1)  # 66 1
        self.bs_volume_id = self.reader.get_data(67, 4)  # 67 4
        self.bs_volume_label = self.reader.get_data(71, 11)  # 71 11
        self.bs_file_system_type = self.reader.get_data(82, 8)  # 82 8
        # end boot sector signature 0xaa55 have been lost


class FSInfo:
    def __init__(self):
        self.fsi_lead_signature = None  # 0 4
        self.fsi_reserved1 = None  # 4 480
        self.fsi_structure_signature = None  # 484 4
        self.fsi_free_count = None  # 488 4
        self.fsi_next_free = None  # 492 4
        self.fsi_reserved2 = None  # 496 12
        self.fsi_trail_signature = None  # 508 4
