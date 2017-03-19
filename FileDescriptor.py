import ctypes
import datetime
import struct
from FatReaderExceptions import *
import FileEntryMetaData
import FilenameConflictResolver


class LongEntryOffsets:  # (Structures.LongDirectoryEntryStructure):
    def __init__(self):
        # super().__init__()
        self.order = (0, 1, False)  # 0 1
        self.name1 = (1, 10, False)  # 1 10
        self.attribute = (11, 1, False)  # 11 1
        self.type = (12, 1, False)  # 12 1
        self.check_sum = (13, 1, True)  # 13 1
        self.name2 = (14, 12, False)  # 14 12
        self.first_cluster_low = (26, 2, False)  # 26 2 must be zero
        self.name3 = (28, 4, False)  # 28 4


class ShortEntryOffsets:  # (Structures.ShortDirectoryEntryStructure):
    def __init__(self):
        # super().__init__()
        self.name = (0, 11, False)
        self.attributes = (11, 1, False)
        self.nt_reserved = (12, 1, False)
        self.create_time_tenth = (13, 1, False)  # 13 1
        self.create_time = (14, 2, True)  # 14 2
        self.create_date = (16, 2, True)  # 16 2
        self.last_access_date = (18, 2, True)  # 18 2
        self.first_cluster_high = (20, 2, False)  # 20 2 // старшее слово номера первого класте
        self.write_time = (22, 2, True)  # 22 2 время последней записи , создание тоже з
        self.write_date = (24, 2, True)  # 24 2 дата последней записи,создание файла тож
        self.first_cluster_low = (26, 2, False)  # 26 2 младшее слово первого кластера
        self.file_size = (28, 4, True)  # 28 4


class FileDescriptor:
    def __init__(self):
        self.core = None
        self.parent_directory = None
        self.entries_data = []
        self._ldir = LongEntryOffsets()
        self._dir = ShortEntryOffsets()
        self._long_name = None
        self._short_name = None
        self._extend_cache = None
        self._attributes = None
        self._write_datetime = None
        self._data_cluster = None
        self._cluster_size = None
        self._entry_offset_in_dir = []
        self.exist = False
        self.core_inited = False
        self.parent_directory_inited = False

    """
    //////////////////////////////////////
    ////// START CONSTRUCTOR ZONE   //////
    //////////////////////////////////////
    """

    def drop_file_descriptor(self):
        self.core = None
        self.parent_directory = None
        self.entries_data = []
        self._long_name = None
        self._short_name = None
        self._attributes = None
        self._write_datetime = None
        self._data_cluster = None
        self._cluster_size = None
        self._entry_offset_in_dir = []
        self.exist = False
        self.core_inited = False
        self.parent_directory_inited = False

    def set_core(self, core):
        self.core = core
        self._cluster_size = core.fat_boot_sector.cluster_size
        self.core_inited = True

    def set_parent_directory(self, parent_directory_descriptor):
        self.parent_directory = parent_directory_descriptor
        self.parent_directory_inited = True

    def _parse_entries_data(self):
        self._short_name = self._read_short_name()
        if len(self.entries_data) > 1:
            self._long_name = self._read_long_name()
        else:
            self._long_name = self._short_name
        self._write_datetime = self._read_date_time()
        self._data_cluster = self._read_data_cluster()
        self._attributes = self._read_attribute()

    def new_entry_from_bytes(self, entries_data):
        entries_data = reversed(entries_data)
        entries_data = [list(t) for t in zip(*entries_data)]
        self.entries_data, self._entry_offset_in_dir, *_ = entries_data  # todo think may be we need check empty list
        self._parse_entries_data()
        pass

    def new_entry_from_descriptor(self, file_descriptor):
        self.entries_data = file_descriptor.entries_data
        self._parse_entries_data()

    def new_entry(self, file_name, short_filename, create_long=True, data_cluster=None, size=None, attr="",
                  date_time=None):
        entry = short_filename
        self._short_name = entry.decode("cp866")
        self._long_name = self._short_name
        self._attributes = self._parse_attributes(attr)
        entry += b' ' * (11 - len(entry))
        # print(self._attributes.attr_byte)
        # print(bytes(self._attributes.attr_byte))
        entry += bytes([self._attributes.attr_byte])
        entry += b"\x00" * 8
        first_cluster_high, first_cluster_low = self._generate_address(data_cluster, size)
        entry += first_cluster_high
        write_time, write_date = self._parse_write_time(date_time)
        entry += write_time + write_date + first_cluster_low
        entry += b"\x00" * 4
        length = len(entry)
        self.entries_data.append(entry)
        if date_time is None:
            self._write_datetime = datetime.datetime.now()
        else:
            self._write_datetime = date_time
        if create_long:
            self._long_name = file_name
            check_sum = self._calc_check_sum(self._read_data(entry, *self._dir.name))
            self._write_long_directory(file_name, check_sum)

    def _write_long_directory(self, file_name, check_sum):
        if len(self.entries_data) > 1:
            entry = self.entries_data[0]
            self.entries_data = []
            self.entries_data.append(entry)
        name_parts = self._split_name(file_name)
        for number, name_part in enumerate(name_parts):
            self.entries_data.append(
                self._create_long_directory_entry(number + 1, name_part, check_sum, number + 1 == len(name_parts)))

    @staticmethod
    def _create_long_directory_entry(number, name_parts, check_sum, is_last=False):
        entry = struct.pack("<B", ctypes.c_ubyte(number | 0x40 if is_last else number).value)
        entry += name_parts[0]
        entry += b'\x0f\x00'
        entry += struct.pack("<B", check_sum)
        entry += name_parts[1]
        entry += b"\x00\x00"
        entry += name_parts[2]
        return entry

    def _generate_address(self, data_cluster=None, size=None):
        if size is None:
            size = self._cluster_size
        if data_cluster is not None:
            self._data_cluster = data_cluster
            return self._parse_data_cluster(data_cluster)  # todo  make existing allocation here
        else:
            self._core_used()
            start_cluster = self._allocate_place(size)
            self._data_cluster = start_cluster
            return self._parse_data_cluster(start_cluster)

    """
    //////////////////////////////////////
    ////// END OF CONSTRUCTORS ZONE //////
    ////// START OPEN METHODS ZONE  //////
    //////////////////////////////////////
    """

    @property
    def name(self):
        if self._long_name:
            return self._long_name
        else:
            return self._short_name.lower()

    def rename(self, new_file_name, short_names, long_names=None):  # TODO Rewrite
        names = FilenameConflictResolver.NameConflictResolver()
        long_name, short_name = names.get_new_names(new_file_name, self.attributes.directory, short_names, long_names)
        self._write_short_name(short_name)
        if long_names:
            check_sum = self._calc_check_sum(self._read_data(self.entries_data[0], *self._dir.name))
            self._write_long_directory(new_file_name, check_sum)

    @property
    def attr_string(self):
        return self.attributes.attributes

    @property
    def attributes(self):
        return self._attributes

    @attributes.setter
    def attributes(self, attr):  # todo lock changing directory attribute
        self._attributes = FileEntryMetaData.DirectoryAttributesGetter(attr)
        self._write_attributes()
        pass

    @property
    def directory(self):
        return self.attributes.directory

    def _write_attributes(self):
        entry = self._replace_data_in_write(self.entries_data[0], self._attributes.attr_byte, *self._dir.attributes)
        self.entries_data[0] = entry

    @property
    def write_datetime(self):
        return self._write_datetime

    @write_datetime.setter
    def write_datetime(self, date_time):
        self._write_datetime = date_time
        self._write_write_datetime_into_entry(date_time)

    def _write_write_datetime_into_entry(self, date_time):
        date = FileEntryMetaData.DateTimeGetter(date_time)
        entry = self._replace_data_in_write(self.entries_data[0], date.time_bytes, *self._dir.write_time)
        entry = self._replace_data_in_write(entry, date.date_bytes, *self._dir.write_date)
        self.entries_data[0] = entry

    @property
    def date(self):
        return self._write_datetime.date()

    @property
    def time(self):
        return self._write_datetime.time()

    def _core_used(self):
        if not self.core_inited:
            raise CoreNotInitedError()

    @property
    def data_offset(self):
        self._core_used()
        return self.core.fat_boot_sector.calc_cluster_offset(self._data_cluster)

    @property
    def data_cluster(self):
        return self._data_cluster

    @property
    def long_name(self):
        return self._long_name

    @property
    def short_name(self):
        return self._short_name

    @property
    def size(self):
        return self.raw_size()

    def raw_size(self):
        return self._read_data(self.entries_data[0], *self._dir.file_size)

    def update_size_in_descriptor(self):
        size = self.calculate_size_on_disk()
        size_data = struct.pack('<I', size)
        self.entries_data[0] = self._replace_data_in_write(self.entries_data[0], size_data, *self._dir.file_size)

    def to_string(self, long=False, all_files=False):
        file_representation = ''
        if long and ("h" not in self.attr_string or all_files):
            file_representation += self.date.isoformat() + ' '
            file_representation += self.time.isoformat() + '    '
            file_representation += self.attributes.get_attributes_string() + '     '
        if "h" not in self.attr_string or all_files:
            file_representation += self.name
        return file_representation

    def is_correct_name(self, name):
        return name.lower() == self.short_name.lower() or name.lower() == self.long_name.lower()

    """
       //////////////////////////////////////
       //////   END OPEN METHODS ZONE  //////
       //////   DISK OPERATIONS ZONE   //////
       //////////////////////////////////////
    """

    def delete(self, clear_cluster=False):
        self._core_used()
        self._free_old_offsets(self._entry_offset_in_dir)
        self._entry_offset_in_dir = []
        if self.attributes.directory:
            if self.name not in [".", ".."]:
                directory = self.core.file_system_utils.low_level_utils.parse_directory_descriptor(self._data_cluster)
                directory.delete(clear_cluster)
        if clear_cluster:
            self._delete_data_clusters(self._data_cluster)
        if self.name not in [".", ".."]:
            self._delete_fat_chain(self._data_cluster)  # todo check fat cluster deleting for delete firs cluster
        self.drop_file_descriptor()

    def flush(self):
        if not self.parent_directory_inited:
            raise CoreNotInitedError("Parent directory is missing") #Exception("Parent directory missing")
        self._flush()

    def _flush(self):
        if len(self.entries_data) == len(self._entry_offset_in_dir):
            self._write_entry_on_disk(self.entries_data,
                                      self._entry_offset_in_dir)
        elif len(self.entries_data) <= len(self._entry_offset_in_dir):
            self._write_entry_on_disk(self.entries_data,
                                      self._entry_offset_in_dir)
            # check is always offsets order correct
            self._free_old_offsets(self._entry_offset_in_dir[len(self.entries_data):])
            self._entry_offset_in_dir = self._entry_offset_in_dir[:len(self.entries_data)]
        else:
            self._free_old_offsets(self._entry_offset_in_dir)
            self._entry_offset_in_dir = []
            self._allocate_offsets_for_entry()
            self._write_entry_on_disk(self.entries_data, self._entry_offset_in_dir)

    def _write_entry_on_disk(self, entries_data, entry_offsets):
        self._core_used()
        for entry_data, entry_offset in zip(entries_data, entry_offsets):
            self.core.image_reader.set_data_global(entry_offset, entry_data)

    def _delete_fat_chain(self, start_cluster):
        self._core_used()
        self.core.fat_table.delete_file_fat_chain(start_cluster)

    def _delete_file_entry_on_disk(self, file_entries_offsets, clean=False):
        self._core_used()
        data = b'\xe5'
        if clean:
            data = b'\x00' * 32
        for file_entry_offset in file_entries_offsets:
            self.core.image_reader.set_data_global(file_entry_offset, data)

    def _delete_data_clusters(self, start_cluster):
        self._core_used()
        offsets = self.core.fat_table.get_file_clusters_offsets_list(start_cluster)
        zero_cluster = b'\x00' * self._cluster_size
        for offset in offsets:
            self.core.image_reader.set_data_global(offset, zero_cluster)

    def _free_old_offsets(self, offsets):
        self.parent_directory._mark_free_place(offsets)
        self._delete_file_entry_on_disk(offsets, clean=True)

    def _allocate_offsets_for_entry(self):
        self._entry_offset_in_dir = self.parent_directory._get_entry_place_to_flush(len(self.entries_data))

    def _get_file_allocated_clusters(self, cluster_number):
        self._core_used()
        return self.core.fat_table.get_file_clusters_list(cluster_number)

    def _get_cluster_offset(self, cluster):
        self._core_used()
        return self.core.fat_boot_sector.calc_cluster_offset(cluster)

    def calculate_size_on_disk(self):
        size_in_bytes = 0
        if self.attributes.directory:
            self._core_used()
            directory = self.core.file_system_utils.low_level_utils.parse_directory_descriptor(self._data_cluster)
            size_in_bytes += len(self._get_file_allocated_clusters(self._data_cluster)) * self._cluster_size
            size_in_bytes += directory.calculate_size_on_disk()
        else:
            # todo make this operation more easy
            size_in_bytes += len(self._get_file_allocated_clusters(self._data_cluster)) * self._cluster_size
        return size_in_bytes

    def write_data_into_file(self, file_size, data_stream,
                             rewrite=True):  # todo make normal file add data with add to exist file
        if rewrite:
            start_cluster = self.extend_file(file_size, delete_excessive_allocation=True)
            file_offset_stream = self._data_offsets_stream(self._get_cluster_offset(start_cluster))
        else:
            start_cluster = self.extend_file(file_size, to_selected_size=False)
            file_offset_stream = self._data_offsets_stream(self._get_cluster_offset(start_cluster)) # TODO  USE IT YEPTA
        self._core_used()
        for data, offset in zip(data_stream, file_offset_stream):#self._data_offsets_stream()):
            self.core.image_reader.set_data_global(offset, data)

    def data_stream(self, chunk_size=512):
        self._core_used()
        for cluster_offset in self.core.fat_table.get_file_clusters_offsets_list(self._data_cluster):
            yield self.core.image_reader.get_data_global(cluster_offset, self.core.fat_boot_sector.cluster_size)

    def _get_file_last_cluster(self):
        self._core_used()
        return self.core.fat_table.get_file_clusters_list(self._data_cluster)[-1:][
            0]  # maybe if it will be a stream we have a problem

    def _get_file_number_cluster_from_end(self, number):
        self._core_used()
        return self.core.fat_table.get_file_clusters_list(self._data_cluster)[-abs(number):][0]

    def _data_offsets_stream(self, start_cluster_offset=None):
        self._core_used()
        get_offset = False
        if start_cluster_offset is None:
            get_offset = True
        for x in self.core.fat_table.get_file_clusters_offsets_list(self._data_cluster):
            if x == start_cluster_offset:
                get_offset = True
            if get_offset:
                yield x

    def extend_file(self, file_size, to_selected_size=True, delete_excessive_allocation=False):
        preferred_size_in_clusters = self._count_clusters(file_size)
        current_size_in_cluster = self._count_clusters(self.calculate_size_on_disk())
        extend_size = (
            preferred_size_in_clusters - current_size_in_cluster) if to_selected_size else preferred_size_in_clusters
        if extend_size < 0:
            if delete_excessive_allocation:
                del_start_cluster = self._get_file_number_cluster_from_end(extend_size)
                self._delete_fat_chain(del_start_cluster)
                self._core_used()
                self.core.fat_table.set_cluster_entry(del_start_cluster)
                return self._data_cluster
            else:
                raise UnExpectedCriticalError("Critical error: unforeseen operation , you tries negative file extend")
                pass
        else:
            self._core_used()
            last = self.core.fat_table.extend_file(self._data_cluster, extend_size)
            return last

    """
           //////////////////////////////////////
           ////// END DISK OPERATIONS ZONE //////
           ////// START ENTRY WORKERS ZONE //////
           //////////////////////////////////////
    """

    def _replace_data_in_write(self, were, data, offset, length, pack):
        return were[0: offset] + data + were[offset + length:]

    def _write_short_name(self, file_name):
        name_data = file_name
        self.entries_data[0] = self._replace_data_in_write(self.entries_data[0], name_data, *self._dir.name)
        self._short_name = name_data.decode("cp866")

    def _write_data_cluster(self, data_cluster):
        first_cluster_high, first_cluster_low = self._generate_address(data_cluster, None)
        entry = self._replace_data_in_write(self.entries_data[0], first_cluster_high, *self._dir.first_cluster_high)
        self.entries_data[0] = self._replace_data_in_write(entry, first_cluster_low, *self._dir.first_cluster_low)

    def _read_short_name(self):
        processing_string = self._read_data(self.entries_data[0], *self._dir.name).decode('cp866')
        name = processing_string[0:8].strip()
        extension = processing_string[8:].strip()
        if len(extension):
            name += '.' + extension
        return name

    def _read_long_name(self):
        data = b''
        for entry_number in range(1, len(self.entries_data)):
            data += self._read_data(self.entries_data[entry_number], *self._ldir.name1)
            data += self._read_data(self.entries_data[entry_number], *self._ldir.name2)
            data += self._read_data(self.entries_data[entry_number], *self._ldir.name3)
        return data.decode('utf-16').strip('\0 ￿')

    def _read_date_time(self):
        data = FileEntryMetaData.DateTimeFormat(self._read_data(self.entries_data[0], *self._dir.write_date),
                                                self._read_data(self.entries_data[0], *self._dir.write_time))
        return data.datetime

    def _parse_attributes(self, attr):
        return FileEntryMetaData.DirectoryAttributesGetter(attr, arg_string=True)

    def _read_attribute(self):
        attr = FileEntryMetaData.DirectoryAttributesGetter(self._read_data(self.entries_data[0], *self._dir.attributes))
        return attr

    def _read_data_cluster(self):
        dir_first_cluster_low = self._read_data(self.entries_data[0], *self._dir.first_cluster_low)
        dir_first_cluster_high = self._read_data(self.entries_data[0], *self._dir.first_cluster_high)
        cluster = dir_first_cluster_low + dir_first_cluster_high
        value = struct.unpack('<I', cluster)[0]
        if value == 0:  # todo check this about bad effects attention
            value = 2
        return value

    def _count_clusters(self, size_in_bytes):  # TODO correct
        return (size_in_bytes + self._cluster_size - 1) // self._cluster_size

    def _allocate_place(self, size_in_bytes, clear_allocated_area=True):
        clusters_amount = self._count_clusters(size_in_bytes)
        if clusters_amount == 0:
            raise ZeroSizeAllocationException()
        self._core_used()
        data_cluster = self.core.fat_table.allocate_place(clusters_amount)
        if clear_allocated_area:
            self._delete_data_clusters(data_cluster)
        return data_cluster

    def _parse_data_cluster(self, data_cluster):
        data_cluster_bytes = struct.pack('<i', data_cluster)
        first_cluster_low = data_cluster_bytes[0:2]
        first_cluster_high = data_cluster_bytes[2:]
        return first_cluster_high, first_cluster_low

    def _parse_write_time(self, date_time=None):
        time_converter = FileEntryMetaData.DateTimeGetter(date_time)
        write_date = time_converter.date_bytes
        write_time = time_converter.time_bytes
        return write_time, write_date

    def _split_name(self, name):
        name_parts = []
        for x in range(0, len(name), 13):
            name_parts.append(self._name_part_to_bytes(name[x: x + 13]))
        return name_parts

    def _name_part_to_bytes(self, name_part):
        utf_name = name_part.encode("utf-16")
        utf_name = utf_name[2:]  # todo грязный хак , разобраться почему он добавляет два байта говна
        if len(utf_name) < 26:
            utf_name += b'\x00\x00'
            utf_name = utf_name + b'\xff' * (26 - len(utf_name))
        return utf_name[0:10], utf_name[10:22], utf_name[22:26]

    def _get_parse_mod(self, size):
        mod_parameter = ''
        if size == 1:
            mod_parameter = '<B'
        elif size == 2:
            mod_parameter = '<H'
        elif size == 4:
            mod_parameter = '<I'
        return mod_parameter

    def convert_to_int(self, data, size):
        return struct.unpack(self._get_parse_mod(size), data)[0]

    def _read_data(self, were: bytes, offset, length, parse=False):
        if parse:
            return self.convert_to_int(were[offset: offset + length], length)
        else:
            return were[offset: offset + length]

    def _calc_check_sum(self, name):
        unsigned_char = ctypes.c_ubyte
        check_sum = unsigned_char(0).value
        for x in name:
            if unsigned_char(check_sum & 0x1).value:
                check_sum = unsigned_char(
                    0x80 + unsigned_char(check_sum >> 0x1).value + x).value  # truct.unpack('<B',x)[0]
            else:
                check_sum = unsigned_char(unsigned_char(check_sum >> 0x1).value + x).value
        return check_sum
