class ShortDirectoryEntryStructure:
    def __init__(self):
        self.dir_name = None  # 0 11
        self.dir_attributes = None  # 11 1
        self.dir_nt_reserved = None  # 12 1
        self.dir_create_time_tenth = None  # 13 1
        self.dir_create_time = None  # 14 2
        self.dir_create_date = None  # 16 2
        self.dir_last_access_date = None  # 18 2
        self.dir_first_cluster_high = None  # 20 2 // старшее слово номера первого кластера
        self.dir_write_time = None  # 22 2 время последней записи , создание тоже запись
        self.dir_write_date = None  # 24 2 дата последней записи,создание файла тоже запись
        self.dir_first_cluster_low = None  # 26 2 младшее слово первого кластера (склей их и будет тебе счастье
        self.dir_file_size = None  # 28 4
        self.entry_size = 32  # if fat 32
        self.fat_entry_number = None  # parsed high and low words


class FileEntryStructure:
    def __init(self):
        self._long_name = None
        self._short_name = None
        self._attributes = None
        self._write_date = None
        self._write_time = None
        self._write_datetime = None
        self._data_offset = None
        self._data_cluster = None
        self._entries_offsets = None


class LongDirectoryEntryStructure:
    def __init__(self):
        self.ldir_order = None  # 0 1
        self.ldir_name1 = None  # 1 10
        self.ldir_attribute = None  # 11 1
        self.ldir_type = None  # 12 1
        self.ldir_check_sum = None  # 13 1
        self.ldir_name2 = None  # 14 12
        self.ldir_first_cluster_low = None  # 26 2 must be zero
        self.ldir_name3 = None  # 28 4
        self.entry_size = 32  # for fat 32


class FSInfoStructure:
    def __init__(self):
        self.fsi_lead_signature = None  # 0 4
        self.fsi_reserved1 = None  # 4 480
        self.fsi_structure_signature = None  # 484 4
        self.fsi_free_count = None  # 488 4
        self.fsi_next_free = None  # 492 4
        self.fsi_reserved2 = None  # 496 12
        self.fsi_trail_signature = None  # 508 4


class FatBootSectorStructure:
    def __init__(self):
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


class DirectoryAttributesStructure:
    def __init__(self):
        self.attr_read_only = None
        self.attr_hidden = None
        self.attr_system = None
        self.attr_volume_id = None
        self.attr_directory = None
        self.attr_archive = None
        self.attr_long_name = None

