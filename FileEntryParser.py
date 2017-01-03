import Structures
import ctypes
class LongEntryParser(Structures.LongDirectoryEntryStructure):
    def __init__(self, image_reader, entry_start_offset):
        super().__init__()
        image_reader.set_global_offset(entry_start_offset)
        self.ldir_order = image_reader.get_data_local(0, 1)  # 0 1
        self.ldir_name1 = image_reader.get_data_local(1, 10)  # 1 10
        self.ldir_attribute = image_reader.get_data_local(11, 1)  # 11 1
        self.ldir_type = image_reader.get_data_local(12, 1)  # 12 1
        self.ldir_check_sum = image_reader.get_data_local(13, 1,True)  # 13 1
        self.ldir_name2 = image_reader.get_data_local(14, 12)  # 14 12
        self.ldir_first_cluster_low = image_reader.get_data_local(26, 2)  # 26 2 must be zero
        self.ldir_name3 = image_reader.get_data_local(28, 4)  # 28 4
        self.entry_size = 32  # for fat 32
    @property
    def name_part(self):
        return (self.ldir_name1 + self.ldir_name2 + self.ldir_name3).decode('utf-16')

    def is_correct_check_sum(self,short_name : str):
        sum = ctypes.c_ubyte
        value = sum(0).value
        for x in short_name:
            if (sum(value & 0x1).value):
                value = sum(0x80 + sum(value >> 0x1).value + ord(x)).value
            else:
                value = sum(sum(value >> 0x1).value + ord(x)).value
        return value == self.ldir_check_sum