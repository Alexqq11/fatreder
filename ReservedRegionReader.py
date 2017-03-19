
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
        self.bpb_ext_flags = self.get_data(40, 2, True)  # 40 2
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
        self._second_cluster_offset = self.fat_zone_offset
        self._second_cluster_offset += self.bpb_number_fats * self.bpb_fat_size_32 * self.bpb_bytes_per_sector
        self._fat_size = (self.root_directory_offset - self.fat_zone_offset) // self.bpb_number_fats
        self._fat_offsets_list = self._fat_offsets_list()
        self._data_clusters_amount = self._calc_data_clusters()
        self._mirroring = None
        self._active_fat = None
        self._parse_ext_flags()

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

    @property
    def active_fat(self):
        return  self._active_fat , self._mirroring

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

    def _parse_ext_flags(self):
        data = bin(self.bpb_ext_flags)[2:]
        data = '0' * (16 - len(data)) + data
        fat_number = int(data[-4:],2)
        reserved = int(data[-7:-4],2)
        mirroring = int(data[-8:-7],2)
        if mirroring == 0:
            self._mirroring = True
        else:
            self._mirroring = False
        self._active_fat = fat_number


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
    def root_directory_cluster(self):
        return self.bpb_root_cluster

    @property
    def root_directory_offset(self):
        return self.calc_cluster_offset(self.bpb_root_cluster)#self._second_cluster_offset

    def calc_cluster_offset(self, cluster_number):
        offset = (cluster_number - 2) * self.bpb_sectors_per_cluster * self.bpb_bytes_per_sector
        offset += self._second_cluster_offset
        return offset

    def calc_cluster_number(self, cluster_offset):
        number = cluster_offset - self.root_directory_offset
        number = number // (self.bpb_sectors_per_cluster * self.bpb_bytes_per_sector) + 2
        return number

class BootSectorChecker:
    def __init__(self):
        self.data_offsets = Structures.BootSectorOffsets()

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

    def read(self, data, offset, length, parse):
        if parse:
            return self.convert_to_int(data[offset: offset + length], length)
        else:
            return data[offset: offset + length]

    def check_clusters_and_sectors_size(self, data):
        checked_field = self.read(data, *self.data_offsets.bpb_bytes_per_sector)
        correct_bytes_per_sector = checked_field in [512, 1024, 2048, 4096]
        checked_field = self.read(data, *self.data_offsets.bpb_sectors_per_cluster)
        correct_sectors_per_cluster = checked_field in [1, 2, 4, 8, 16, 32, 64, 128]
        checked_field = self.read(data, *self.data_offsets.bpb_bytes_per_sector)
        checked_field_2 = self.read(data, *self.data_offsets.bpb_sectors_per_cluster)
        correct_bytes_per_cluster = checked_field * checked_field_2 <= 32 * 1024
        return correct_bytes_per_cluster and correct_bytes_per_sector and correct_sectors_per_cluster

    def analyse_special_fields_1(self, data):
        prediction = "FAT32"
        checked_field = self.read(data, *self.data_offsets.bpb_reserved_region_sectors_count)
        if checked_field < 1:
            prediction = "ERROR"
        elif checked_field == 1:
            prediction = "FAT12/16?"
        elif checked_field != 32 and checked_field != 1:
            prediction = "FAT32?"
        return prediction

    def analyse_special_fields_2(self, data):
        checked_field = self.read(data, *self.data_offsets.bpb_root_entry_count)
        checked_field_2 = self.read(data, *self.data_offsets.bpb_bytes_per_sector)
        prediction = "FAT32"
        if checked_field == 0:
            return prediction
        else:
            prediction = "FAT12/16"
        if ((checked_field * 32) * checked_field_2) // self.gcd((checked_field * 32),
                                                                checked_field_2) != checked_field_2:
            prediction = "ERROR"
        return prediction

    def analyse_special_fields_3(self, data):
        checked_field = self.read(data, *self.data_offsets.bpb_fat_size_16)
        checked_field_2 = self.read(data, *self.data_offsets.bpb_fat_size_32)
        if checked_field_2 != 0 and checked_field == 0:
            return "FAT32"
        elif checked_field != 0 and checked_field_2 == 0:
            return "FAT12/16"
        else:
            return "ERROR"

    def analyse_special_fields_4(self, data):
        checked_field = self.read(data, *self.data_offsets.bpb_total_sectors_16)
        checked_field_2 = self.read(data, *self.data_offsets.bpb_total_sectors_32)
        if checked_field != 0 and checked_field_2 == 0:
            return "FAT12/16"
        elif checked_field == 0 and checked_field_2 != 0:
            return "FAT32?"
        else:
            return "ERROR"

    def gcd(self, a, b):
        return b if self.gcd(b, a % b) else a

    def check(self, data):
        prediction = self.check_bpb_fields(data)
        if prediction != "ERROR":
            try:
                fat_type = self.detect_fat_type(data)
            except Exception:
                fat_type = "ERROR"
        else:
            fat_type = "ERROR"
        if fat_type == "FAT32":
            checked_field = self.read(data, *self.data_offsets.bpb_root_cluster)
            if checked_field < 2:
                fat_type = "ERROR"
        return fat_type

    def detect_fat_type(self, data):
        root_dir_sectors = (((self.read(data, *self.data_offsets.bpb_root_entry_count) * 32) +
                             (self.read(data, *self.data_offsets.bpb_bytes_per_sector) - 1)) //
                            self.read(data, *self.data_offsets.bpb_bytes_per_sector))
        if self.read(data, *self.data_offsets.bpb_fat_size_16) != 0:
            fat_size = self.read(data, *self.data_offsets.bpb_fat_size_16)
        else:
            fat_size = self.read(data, *self.data_offsets.bpb_fat_size_16)
        if self.read(data, *self.data_offsets.bpb_total_sectors_16) != 0:
            tot_sec = self.read(data, *self.data_offsets.bpb_total_sectors_16)
        else:
            tot_sec = self.read(data, *self.data_offsets.bpb_total_sectors_32)
        data_sec = (tot_sec - (self.read(data, *self.data_offsets.bpb_reserved_region_sectors_count) +
                               (self.read(data, *self.data_offsets.bpb_number_fats) * fat_size) + root_dir_sectors))
        count_of_clusters = data_sec / self.read(data, *self.data_offsets.bpb_sectors_per_cluster)
        if count_of_clusters < 4085:
            return "FAT12/16"
        elif count_of_clusters < 65525:
            return "FAT12/16"
        else:
            return "FAT32"

    def check_bpb_fields(self, data):
        correct = self.check_clusters_and_sectors_size(data)
        if not correct:
            return "ERROR"
        prediction_1 = self.analyse_special_fields_1(data)
        prediction_2 = self.analyse_special_fields_2(data)
        prediction_3 = self.analyse_special_fields_3(data)
        prediction_4 = self.analyse_special_fields_4(data)
        predictions = [prediction_1, prediction_2, prediction_3, prediction_4]
        if "ERROR" in [prediction_1, prediction_2, prediction_3, prediction_4]:
            return "ERROR"
        is_fat32 = True

        for x in predictions:
            if x != "FAT32" and x != "FAT32?":
                is_fat32 = False
                break

        is_fat12_16 = not is_fat32
        for x in predictions:
            if x != "FAT12/16" and x != "FAT12/16?":
                is_fat12_16 = False
                break
        if is_fat32 and not is_fat12_16:
            return "FAT32"
        elif not is_fat32 and is_fat12_16:
            return "FAT12/16"
        else:
            return "UNDEFINED"
