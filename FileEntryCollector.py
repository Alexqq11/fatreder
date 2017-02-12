import ctypes
import struct
import ImageWorker
import FileEntryMetaData as FEntryMD
import Structures


class FileEntryCollector:
    def __init__(self, cluster_to_offset):
        self.ldir_list = []
        self.dir = None  # DirEntryShortFat32()
        self._cluster_to_offset = cluster_to_offset

    def append_ldir_entry(self, ldir_entry):
        self.ldir_list.append(ldir_entry)

    def set_dir(self, dir_entry):
        self.dir = dir_entry

    def get_file_entry(self):
        offset = None
        if self._cluster_to_offset:
            offset = self._cluster_to_offset(self.dir.data_cluster_number)
        return FileEntry(self.long_name,
                         self.short_name,
                         self.dir.attributes,
                         self.dir.write_date,
                         self.dir.write_time,
                         self.dir.write_datetime,
                         offset,
                         self.dir.data_cluster_number,
                         self.count_sub_entries_offsets(),
                         self.dir.size
                         )

    def count_sub_entries_offsets(self):
        offsets = list()
        offsets.append(self.dir.entry_start_offset)
        for entry in self.ldir_list:
            offsets.append(entry.entry_start_offset)
        return tuple(offsets)

    @property
    def short_name(self):
        return self.dir.name

    @property
    def long_name(self):
        name = ''
        for entries in self.ldir_list:
            name += entries.name_part
        return name.strip('\0 ￿')


class FileEntry(Structures.FileEntryStructure):
    def __init__(self, long_name, short_name, attr, date, time, datetime, data_offset, data_cluster, entries_offsets,
                 size):
        super().__init__()
        self._long_name = long_name
        self._short_name = short_name
        self._attributes = attr
        self._write_date = date
        self._write_time = time
        self._write_datetime = datetime
        self._data_offset = data_offset
        self._data_cluster = data_cluster
        self._entries_offsets = entries_offsets
        self._size = size

    @property
    def size(self):
        return self._size

    @property
    def long_name(self):
        return self._long_name

    @property
    def short_name(self):
        return self._short_name

    @property
    def name(self):
        if self._long_name:
            return self.long_name
        else:
            return self.short_name.lower()

    @property
    def attributes(self):
        return self._attributes

    @property
    def attr_string(self):
        return self.attributes.attributes

    @property
    def date(self):
        return self._write_date

    @property
    def time(self):
        return self._write_time

    @property
    def datetime(self):
        return self._write_datetime

    @property
    def data_offset(self):
        return self._data_offset

    @property
    def data_cluster(self):
        return self._data_cluster

    @property
    def entries_offsets(self):
        return self._entries_offsets

    def to_string(self, long=False, all=False):
        file_representation = ''
        if long and ("h" not in self.attr_string or all):
            file_representation += self.date.isoformat() + ' '
            file_representation += self.time.isoformat() + '    '
            file_representation += self.attributes.get_attributes_string() + '     '
        if "h" not in self.attr_string or all:
            file_representation += self.name
        return file_representation

    def is_correct_name(self, name):
        return name.lower() == self.short_name.lower() or name.lower() == self.long_name.lower()


class LongEntryReader(Structures.LongDirectoryEntryStructure):
    def __init__(self, image_reader: ImageWorker.ImageReader, entry_start_offset, data=None):
        super().__init__()
        self._data = None
        if not data:
            image_reader.set_global_offset(entry_start_offset)
            self._data = image_reader.get_data_local(0, 32)
        else:
            self._data = data  # check data ?
        self.image_reader = image_reader
        self.ldir_order = self.get_data(0, 1)  # 0 1
        self.ldir_name1 = self.get_data(1, 10)  # 1 10
        self.ldir_attribute = self.get_data(11, 1)  # 11 1
        self.ldir_type = self.get_data(12, 1)  # 12 1
        self.ldir_check_sum = self.get_data(13, 1, True)  # 13 1
        self.ldir_name2 = self.get_data(14, 12)  # 14 12
        self.ldir_first_cluster_low = self.get_data(26, 2)  # 26 2 must be zero
        self.ldir_name3 = self.get_data(28, 4)  # 28 4
        self.entry_size = 32  # for fat 32
        self._entry_start_offset = entry_start_offset

    def get_data(self, start, size, parse_int=False):
        data = self._data[start: start + size]
        if parse_int:
            data = self.image_reader.convert_to_int(data, size)
        return data

    @property
    def entry_start_offset(self):
        return self._entry_start_offset

    @property
    def name_part(self):
        return (self.ldir_name1 + self.ldir_name2 + self.ldir_name3).decode('utf-16')

    def is_correct_check_sum(self, check_sum):
        return check_sum == self.ldir_check_sum


class ShortEntryReader(Structures.ShortDirectoryEntryStructure):
    def __init__(self, image_reader: ImageWorker.ImageReader, entry_start_offset, data=None):
        super().__init__()
        self._data = None
        if not data:
            image_reader.set_global_offset(entry_start_offset)
            self._data = image_reader.get_data_local(0, 32)
        else:
            self._data = data  # check data ?
        self.image_reader = image_reader
        self.dir_name = self.get_data(0, 11)
        self.dir_attributes = self.get_data(11, 1)
        self.dir_nt_reserved = self.get_data(12, 1)
        self.dir_create_time_tenth = self.get_data(13, 1)  # 13 1
        self.dir_create_time = self.get_data(14, 2, True)  # 14 2
        self.dir_create_date = self.get_data(16, 2, True)  # 16 2
        self.dir_last_access_date = self.get_data(18, 2, True)  # 18 2
        self.dir_first_cluster_high = self.get_data(20, 2)  # 20 2 // старшее слово номера первого класте
        self.dir_write_time = self.get_data(22, 2, True)  # 22 2 время последней записи , создание тоже з
        self.dir_write_date = self.get_data(24, 2, True)  # 24 2 дата последней записи,создание файла тож
        self.dir_first_cluster_low = self.get_data(26, 2)  # 26 2 младшее слово первого кластера
        self.dir_file_size = self.get_data(28, 4, True)  # 28 4
        self._check_sum = self._calc_check_sum()
        self.datetime = FEntryMD.DateTimeFormat(self.dir_write_date, self.dir_write_time)  # todo attention if zero
        self._attributes = FEntryMD.DirectoryAttributesGetter(self.dir_attributes)
        self._entry_start_offset = entry_start_offset

    def get_data(self, start, size, parse_int=False):
        data = self._data[start: start + size]
        if parse_int:
            data = self.image_reader.convert_to_int(data, size)
        return data

    @property
    def attributes(self):
        return self._attributes

    @property
    def size(self):
        return self.dir_file_size

    @property
    def write_time(self):
        return self.datetime.time

    @property
    def write_date(self):
        return self.datetime.date

    @property
    def write_datetime(self):
        return self.datetime.datetime

    @property
    def entry_start_offset(self):
        return self._entry_start_offset

    @property
    def data_cluster_number(self):
        value = struct.unpack('<I', self.dir_first_cluster_low + self.dir_first_cluster_high)[0]
        if value == 0:  # todo check this about bad effects attention
            value = 2
        return value

    @property
    def check_sum(self):
        return self._check_sum

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

    @property
    def name(self):
        processing_string = self.dir_name.decode('cp866')
        name = processing_string[0:8].strip()
        extension = processing_string[8:].strip()
        if len(extension):
            name += '.' + extension
        return name
