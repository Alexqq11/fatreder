import ctypes
import struct

import FileEntryMetaData
import Structures


class FileEntryCreator(Structures.FileEntryStructure):
    def __init__(self):
        self.long_entry_creator = LongEntryCreator()
        self.short_entry_creator = ShortEntryCreator()
        self.check_sum = None
        self.entries_list = []
        pass

    def new_entry(self, name, attributes, file_data_cluster, file_size, dir_listing, time=None):
        self.check_sum = None
        self.entries_list = []
        entry, check_sum = self.short_entry_creator.new_entry(name, attributes, file_data_cluster, file_size,
                                                              dir_listing, time)
        self.entries_list.append(entry)
        self.check_sum = check_sum
        self.create_long_directories_entries(name)
        return self.entries_list

    def split_name(self, name):
        name_parts = []
        for x in range(0, len(name), 13):
            name_parts.append(name[x: x + 13])
        return tuple(name_parts)

    def create_long_directories_entries(self, name):
        name_parts = self.split_name(name)
        last_part = False
        for x in range(0, len(name_parts)):
            if x == len(name_parts):
                last_part = True
            entry, number = self.long_entry_creator.new_entry(name_parts[x], x + 1, self.check_sum, last_part)
            self.entries_list.append(entry)


class LongEntryCreator(Structures.LongDirectoryEntryStructure):
    def __init__(self):
        super().__init__()

    def new_entry(self, name_part, number, check_sum, is_last=False):
        self._set_name(name_part)
        self._set_number(number, is_last)
        self._set_meta_data(check_sum)
        return self._join_fields(), number

    def _set_name(self, name_part):
        utf_name = name_part.encode("utf-16")
        utf_name = utf_name[2:]  # todo грязный хак , разобраться почему он добавляет два байта говна
        if len(utf_name) < 26:
            utf_name += b'\x00\x00'
            utf_name = utf_name + b'\xff' * (26 - len(utf_name))
        self.ldir_name1 = utf_name[0:10]
        self.ldir_name2 = utf_name[10:22]
        self.ldir_name3 = utf_name[22:26]

    def _set_meta_data(self, check_sum):
        self.ldir_attribute = b'\x0f'  # struct.pack("<B", 15) #???
        self.ldir_first_cluster_low = b'\x00\x00'
        self.ldir_check_sum = struct.pack("<B", check_sum)
        self.ldir_type = b'\x00'

    def _set_number(self, number, is_last=False):
        if is_last:
            self.ldir_order = struct.pack("<B", ctypes.c_ubyte(number | 0x40).value)
        else:
            self.ldir_order = struct.pack("<B", number)

    def _join_fields(self):
        return self.ldir_order + self.ldir_name1 + self.ldir_attribute + self.ldir_type + self.ldir_check_sum \
               + self.ldir_name2 + self.ldir_first_cluster_low + self.ldir_name3


class ShortEntryCreator(Structures.ShortDirectoryEntryStructure):
    def __init__(self):
        super().__init__()
        self.dir_listing = None

    def new_entry(self, name, attributes, file_data_cluster, file_size, dir_listing, time=None):
        self.dir_listing = dir_listing
        self._set_name(name)
        self._set_attributes(attributes)
        self._set_file_size(file_size)
        self._set_data_cluster(file_data_cluster)
        self._set_time(time)
        self._set_reserve_fields()
        return self.join_fields(), self._calc_check_sum()

    def _calc_check_sum(self):
        unsigned_char = ctypes.c_ubyte
        check_sum = unsigned_char(0).value
        for x in self.dir_name:
            if unsigned_char(check_sum & 0x1).value:
                check_sum = unsigned_char(
                    0x80 + unsigned_char(check_sum >> 0x1).value + x).value  # truct.unpack('<B',x)[0]
            else:
                check_sum = unsigned_char(unsigned_char(check_sum >> 0x1).value + x).value
        return check_sum

    def _write_short_name(self, name):  # default_correct_name
        marker = name.split(b'.')
        self.dir_name = marker[0] + (b'\x20' * (12 - len(name))) + marker[1]

    def _set_name(self, name):
        oem_name, incorrect_translate = self._generate_short_name(name)
        oem_name = self._generation_last_value(oem_name, incorrect_translate)
        self._write_short_name(oem_name)

    def _set_attributes(self, attr):
        temp_attr = FileEntryMetaData.DirectoryAttributesGetter(attr, True)
        self.dir_attributes = temp_attr.attribute_byte

    def _set_time(self, date_time=None):
        time_converter = FileEntryMetaData.DateTimeGetter(date_time)
        self.dir_write_date = time_converter.date_bytes
        self.dir_write_time = time_converter.time_bytes
        self.dir_create_date = time_converter.date_bytes
        self.dir_create_time = time_converter.date_bytes
        self.dir_last_access_date = time_converter.date_bytes
        self.dir_create_time_tenth = b'\x00'

    def _set_file_size(self, size_in_bytes):
        self.dir_file_size = struct.pack('<I', size_in_bytes)

    def _set_reserve_fields(self):
        self.dir_nt_reserved = b'\x00'

    def _set_data_cluster(self, data_cluster):
        data_cluster_bytes = struct.pack('<i', data_cluster)
        self.dir_first_cluster_low = data_cluster_bytes[0:2]
        self.dir_first_cluster_high = data_cluster_bytes[2:]

    def join_fields(self):
        return self.dir_name + self.dir_attributes + self.dir_nt_reserved \
               + self.dir_create_time_tenth + self.dir_create_time \
               + self.dir_create_date + self.dir_last_access_date \
               + self.dir_first_cluster_high + self.dir_write_time + self.dir_write_date \
               + self.dir_first_cluster_low + self.dir_file_size

    def _is_bad_literal(self, liter):
        unsupported_values = b'\x22\x2a\x2b\x2c\x2f\x3a\x3b\x3c\x3d\x3e\x3f\x5b\x5c\x5d\x5e\x7c'
        return liter < b'\x20' and liter != b'\x05' or liter in unsupported_values

    def _encode_name_to_oem_encoding(self, name):
        oem_string = b''
        oem_liter = b''
        incorrect_translate = False
        for liter in name:
            try:
                oem_liter = liter.encode("cp866")
                if self._is_bad_literal(oem_liter):
                    incorrect_translate = True
                    oem_liter = b'_'
            except UnicodeEncodeError:  # помоему cp866 сжирает любой шлак, который ей кормят:D
                oem_liter = b'_'
                incorrect_translate = True
            oem_string += oem_liter
        return oem_string, incorrect_translate

    def _clear_name_content(self, name):
        name = name.upper()
        translated_name = name.replace(' ', '')
        extension_marker = translated_name[::-1].find('.', 0)
        if extension_marker != -1:
            translated_name = translated_name[:-extension_marker].replace('.', '') + '.' + translated_name[
                                                                                           -extension_marker:]
        return translated_name, extension_marker

    def _translate_to_short_name(self, oem_string: bytes, extension_marker):
        doth_position = oem_string.find(b'.', 0)
        marker = doth_position
        if doth_position == -1:
            marker = 9
        oem_name = oem_string[0: min(8, marker)]
        if extension_marker != -1:
            oem_name += b'.'
            oem_name += oem_string[doth_position + 1: doth_position + 4]
        return oem_name

    def _generate_short_name(self, name: str):
        translated_name, extension_marker = self._clear_name_content(name)
        oem_string, incorrect_translate = self._encode_name_to_oem_encoding(translated_name)
        oem_name = self._translate_to_short_name(oem_string, extension_marker)
        return oem_name, incorrect_translate

    def _check_name(self, oem_name):
        return not oem_name in self.dir_listing

    def _join_name(self, prefix, postfix, extension):
        if (8 - len(prefix)) >= len(postfix):
            return prefix + postfix + b'.' + extension
        else:
            return prefix[0:8 - len(postfix)] + postfix + b'.' + extension

    def _generation_last_value(self, oem_name, marker=False):
        if not marker and len(oem_name) < 13 and self._check_name(oem_name):
            return oem_name
        else:
            for x in range(1, 1000000):
                marker = oem_name.split(b'.')
                added_str = ('~' + str(x)).encode("cp866")
                new_name = self._join_name(marker[0], added_str, marker[1])
                if (self._check_name(new_name)):
                    return new_name
