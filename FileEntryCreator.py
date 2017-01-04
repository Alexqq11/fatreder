import struct

import FileEntryMetaData
import Structures
import ctypes


class FileEntryCreator(Structures.FileEntryStructure):
    pass


class ShortEntryCreator(Structures.ShortDirectoryEntryStructure):
    def __init__(self):
        super().__init__()
        self.dir_listing = None
    def new_entry(self, name, attributes, file_data_cluster, file_size , dir_listing, time = None):
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
        temp_oem_name = self._generate_short_name(name)
        oem_name = self._generation_last_value(temp_oem_name[0], temp_oem_name[1])
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

    def _generate_short_name(self, name: str):
        name = name.upper()
        oem_name = b''
        oem_liter = None
        oem_string = b''
        incorrect_translate = False
        unsupported_values = b'\x22\x2a\x2b\x2c\x2e\x2f\x3a\x3b\x3c\x3d\x3e\x3f\x5b\x5c\x5d\x5e\x7c'
        translated_name = name.strip()
        extension_marker = translated_name[::-1].find('.', 0)
        if extension_marker != -1:
            translated_name = translated_name[:-extension_marker].strip('.') + '.' + translated_name[-extension_marker:]
        for liter in translated_name:
            try:
                oem_liter = liter.encode("cp866")
                if oem_liter < b'\x20' and oem_liter != b'\x05' or oem_liter in unsupported_values:
                    oem_liter = b'_'
            except UnicodeEncodeError:
                oem_liter = b'_'
                incorrect_translate = True
            oem_string += oem_liter
        for x in range(oem_string):
            if x < 8 and oem_string[x] != b'.':
                oem_name += oem_string[x]
            else:
                break
        if extension_marker != -1:
            oem_name += b'.'
            copied = 0
            for x in range(len(oem_string) - extension_marker, len(oem_string)):
                if copied < 3:
                    oem_name += oem_string[x]
                else:
                    break
        return oem_name, incorrect_translate

    def _check_name(self, oem_name):
        return not oem_name in self.dir_listing

    def _join_name(self, prefix, postfix, extension):
        if (8 - len(prefix)) <= len(prefix):
            return prefix + postfix + b'.' + extension
        else:
            return prefix[0: -len(postfix)] + postfix + b'.' + extension

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
