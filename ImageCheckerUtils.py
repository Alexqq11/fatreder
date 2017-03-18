import struct

import Structures


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

class FatTableChecker:
    pass


class FilesAllocationChecker:
    pass
