import mmap
import os
import struct

""""reserved region class """
""" bs - boot sector"""
""""bpb bios parameter block """


class Core:
    def __init__(self):
        self.image_reader = None
        self.fat_bot_sector = None
        self.dir_parser = None

    def _init_image(self, path):
        self.image_reader = ImageReader(path)

    def _init_fat_boot_sector(self):
        self.fat_bot_sector = FatBootSector(self.image_reader)
    def _init_dir_parser(self):
        self.dir_parser = DirectoryParser(self.image_reader, [])

    def init(self, path):
        self._init_image(path)
        self._init_fat_boot_sector()
        self._init_dir_parser()

    def close_reader(self):
        self.image_reader.close_reader()

    pass


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

    def get_root_dir_offset(self):
        return self.get_fat_offset() + self.bpb_number_fats * self.bpb_fat_size_32 * self.bpb_bytes_per_sector

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
                                                    True)  # 22 2 amount fat sectors for one fat12/16 table in fat32 zero watch to fat 32
        self.bpb_sectors_per_track = self.reader.get_data(24, 2,
                                                          True)  # 24 2 for interrupt 13 and accses to disks with geometry #old tech
        self.bpb_number_heads = self.reader.get_data(26, 2, True)  # 26 2 ammount of disk heads
        self.bpb_hidden_sectors = self.reader.get_data(28, 4, True)  # 28 4
        self.bpb_total_sectors_32 = self.reader.get_data(32, 4, True)  # 32 4 new 32 bit field sm old 16 bit field
        # there was can been fat12/16 fields but we starting write fat 32 fields
        self.bpb_fat_size_32 = self.reader.get_data(36, 4, True)  # 36 4 amoun of sectors one fat
        self.bpb_ext_flags = self.reader.get_data(40, 2)  # 40 2
        self.file_system_version = self.reader.get_data(42, 2)  # 42 2
        self.bpb_root_cluster = self.reader.get_data(44, 4, True)  # 44 4
        self.bpb_file_system_information = self.reader.get_data(48, 2,
                                                                True)  # 48 2 кол-во свободных кластеров на диске, чтобы утилитам легче жить
        self.bpb_backup_boot_sector = self.reader.get_data(50, 2, True)  # 50 2
        self.bpb_reserved = self.reader.get_data(52, 12)  # 52 12
        self.bs_driver_number = self.reader.get_data(64, 1)  # 64 1
        self.bs_reserved1 = self.reader.get_data(65, 1)  # 65 1
        self.bs_boot_signature = self.reader.get_data(66, 1)  # 66 1
        self.bs_volume_id = self.reader.get_data(67, 4)  # 67 4
        self.bs_volume_label = self.reader.get_data(71, 11)  # 71 11
        self.bs_file_system_type = self.reader.get_data(82, 8)  # 82 8
        # end boot sector signature 0xaa55 have been lost

    def count_fat_table_offset(self, lol):
        pass


class ImageReader:
    def __init__(self, path):
        self.image = None
        self.file_stream = None
        self._set_mapped_image(path)
        self.file_global_offset = 0

    def _set_mapped_image(self, path):
        with open(path, "r+b") as f:
            self.file_stream = f
            self.image = mmap.mmap(f.fileno(), 0)

    def _get_parse_mod(self, size):
        mod_parameter = ''
        if (size == 1):
            mod_parameter = '<B'
        elif (size == 2):
            mod_parameter = '<H'
        elif (size == 4):
            mod_parameter = '<I'
        return mod_parameter

    def set_global_offset(self, offset):
        self.file_global_offset = offset

    def convert_to_int(self, data, size):
        return struct.unpack(self._get_parse_mod(size), data)[0]

    def get_data(self, local_offset, size, convert_integer=False):
        self.image.seek(self.file_global_offset + local_offset)
        buffer = self.image.read(size)
        if (convert_integer):
            buffer = self.convert_to_int(buffer, size)  # struct.unpack(self._get_parse_mod(size), buffer)[0]
        return buffer

    def close_reader(self):
        self.image.close()
        self.file_stream.close()


class FSInfo:
    def __init__(self):
        self.fsi_lead_signature = None  # 0 4
        self.fsi_reserved1 = None  # 4 480
        self.fsi_structure_signature = None  # 484 4
        self.fsi_free_count = None  # 488 4
        self.fsi_next_free = None  # 492 4
        self.fsi_reserved2 = None  # 496 12
        self.fsi_trail_signature = None  # 508 4


class DirectoryAttributes:
    def __init__(self):
        self.attr_read_only = None
        self.attr_hidden = None
        self.attr_system = None
        self.attr_volume_id = None
        self.attr_directory = None
        self.attr_archive = None
        self.attr_long_name = None

    def parse_attributes(self, attr_byte):
        attr_byte = struct.unpack('<B', attr_byte)[0]
        self.attr_read_only = (1 == (attr_byte & 1))
        self.attr_hidden = (2 == (attr_byte & 2))
        self.attr_system = (4 == (attr_byte & 4))
        self.attr_volume_id = (8 == (attr_byte & 8))
        self.attr_directory = (16 == (attr_byte & 16))
        self.attr_archive = (32 == (attr_byte & 32))
        self.attr_long_name = (15 == (attr_byte & 15))

    def is_lfn(self, ldir_order_byte, ldir_attr_byte):
        ldir_attr_byte = struct.unpack('<B', ldir_attr_byte)[0]
        mask = 2 ** 5 + 2 ** 4 + 2 ** 3 + 2 ** 2 + 2 ** 1 + 2 ** 0
        return ((ldir_attr_byte & mask) == 15) and (ldir_order_byte != b'\xe5')


class DirectoryParser:
    def __init__(self, image_reader, offsets_list):
        self.image_reader = image_reader
        self.File_entries = []
        self.offsets_list = offsets_list
        self.active_offset = None
        self.entry_size = 32
        self.zone_offset = 0
        self.next_offset = 0
        self.directory_size = 512 * 8
        self.entries_amount = 0  # one classter but in future we need to change offset to another disk clusters

    def _is_lfn(self, offset):
        first_entry_byte = self.image_reader.get_data(offset, 1)
        attr_entry_byte = self.image_reader.get_data(offset + 11, 1, True)  # need more tests
        # attr_entry_byte = struct.unpack('<B', attr_entry_byte)[0]
        mask = 2 ** 5 + 2 ** 4 + 2 ** 3 + 2 ** 2 + 2 ** 1 + 2 ** 0
        return ((attr_entry_byte & mask) == 15) and (first_entry_byte != b'\xe5')

    def _is_directory(self, offset):
        first_entry_byte = self.image_reader.get_data(offset, 1)
        #attr_entry_byte = self.image_reader.get_data(offset + 11, 1)  # need more tests
        return not ((first_entry_byte in [b'\xe5', b'\x00']) or self._is_lfn(offset))

    def _is_end_lfn(self, offset, number):
        ldir_order_byte = self.image_reader.get_data(offset, 1, True)
        return ((4 * 16) == (ldir_order_byte & (4 * 16))) and (((4 * 16) | number) == ldir_order_byte)

    def _is_correct_lfn(self, offset, number):
        ldir_order_byte = self.image_reader.get_data(offset, 1, True)
        return ldir_order_byte == number  # add hash names checking

    def parse_directory_on_offset(self, directory_offset):
        self.image_reader.set_global_offset(directory_offset)
        while (self.zone_offset <= self.directory_size):
            if (self._is_directory(self.zone_offset)):
                temp_file_entry = FileEntryStructure()
                self.File_entries.append(temp_file_entry)
                temp_short_entry = DirEntryShortFat32()
                temp_short_entry.parse_entry_data(self.image_reader, directory_offset +self.zone_offset, directory_offset, True)
                temp_file_entry.set_dir(temp_short_entry)
                self.next_offset = self.zone_offset + self.entry_size
                self.zone_offset -= self.entry_size
                lfn_number = 0
                parsing_lfn = True
                while (self.zone_offset >= -32 and parsing_lfn):
                    if (self._is_lfn(self.zone_offset)):
                        lfn_number += 1
                        if (not self._is_end_lfn(self.zone_offset, lfn_number)):
                            if (self._is_correct_lfn(self.zone_offset, lfn_number)):
                                temp_ldir_entry = DirEntryLongFat32()
                                temp_ldir_entry.parse_entry_data(self.image_reader, directory_offset + self.zone_offset, directory_offset, True)
                                temp_file_entry.append_ldir_entry(temp_ldir_entry)
                            else:
                                parsing_lfn = False
                                temp_file_entry.clear_lfn()
                                self.zone_offset = self.next_offset  # need except
                        else:
                            temp_ldir_entry = DirEntryLongFat32()
                            temp_ldir_entry.parse_entry_data(self.image_reader, directory_offset +self.zone_offset, directory_offset, True)
                            temp_file_entry.append_ldir_entry(temp_ldir_entry)
                            parsing_lfn = False
                            self.zone_offset = self.next_offset
                    else:  # if lfn_list not empty need except
                        parsing_lfn = False
                        temp_file_entry.clear_lfn()
                        self.zone_offset = self.next_offset
                        DO_NOTHING  = 1
            else:
                self.zone_offset += self.entry_size


class FileEntryStructure:
    def __init__(self):
        self.ldir_list = []
        self.dir = None

    def append_ldir_entry(self, ldir_entry):
        self.ldir_list.append(ldir_entry)

    def set_dir(self, dir_entry):
        self.dir = dir_entry

    def clear_lfn(self):
        self.ldir_list = []


class DirEntryShortFat32:
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

    def parse_entry_data(self, image_reader, entry_start_offset, old_offset = 0 , return_offset = False):
        image_reader.set_global_offset(entry_start_offset)
        self.dir_name = image_reader.get_data(0, 11)
        self.dir_attributes = image_reader.get_data(11, 1)
        self.dir_nt_reserved = image_reader.get_data(12, 1)
        self.dir_create_time_tenth = image_reader.get_data(13, 1)  # 13 1
        self.dir_create_time = image_reader.get_data(14, 2)  # 14 2
        self.dir_create_date = image_reader.get_data(16, 2)  # 16 2
        self.dir_last_access_date = image_reader.get_data(18, 2)  # 18 2
        self.dir_first_cluster_high = image_reader.get_data(20, 2)  # 20 2 // старшее слово номера первого кластера
        self.dir_write_time = image_reader.get_data(22, 2)  # 22 2 время последней записи , создание тоже запись
        self.dir_write_date = image_reader.get_data(24, 2)  # 24 2 дата последней записи,создание файла тоже запись
        self.dir_first_cluster_low = image_reader.get_data(26,
                                                           2)  # 26 2 младшее слово первого кластера (склей их и будет тебе счастье
        self.dir_file_size = image_reader.get_data(28, 4, True)  # 28 4
        self.fat_entry_number = image_reader.convert_to_int(self.dir_first_cluster_low + self.dir_first_cluster_high, 4)
        if (return_offset):
            image_reader.set_global_offset(old_offset)


class DirEntryLongFat32:
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

    def parse_entry_data(self, image_reader, entry_start_offset, old_offset = 0 , return_offset = False):
        image_reader.set_global_offset(entry_start_offset)
        self.ldir_order = image_reader.get_data(0, 1)  # 0 1
        self.ldir_name1 = image_reader.get_data(1, 10)  # 1 10
        self.ldir_attribute = image_reader.get_data(11, 1)  # 11 1
        self.ldir_type = image_reader.get_data(12, 1)  # 12 1
        self.ldir_check_sum = image_reader.get_data(13, 1)  # 13 1
        self.ldir_name2 = image_reader.get_data(14, 12)  # 14 12
        self.ldir_first_cluster_low = image_reader.get_data(26, 2)  # 26 2 must be zero
        self.ldir_name3 = image_reader.get_data(28, 4)  # 28 4
        self.entry_size = 32  # for fat 32
        if(return_offset):
            image_reader.set_global_offset(old_offset)


c = Core()
c.init("..\.\dump (1).iso")
print(c.fat_bot_sector.__dict__)
print(c.fat_bot_sector.get_fat_offset())
print(c.fat_bot_sector.get_root_dir_offset())
c.dir_parser.parse_directory_on_offset(c.fat_bot_sector.get_root_dir_offset())
print(len(c.dir_parser.File_entries))
for x in c.dir_parser.File_entries:
    print(x.dir.dir_name)

c.close_reader()
