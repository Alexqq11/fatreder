import ctypes
import datetime
import struct

import FatReaderExceptions
import FileEntryMetaData


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
        self.name_generator = _NameGenerator()
        self._extend_cache = None
        self._attributes = None
        self._write_datetime = None
        self._data_cluster = None
        self._cluster_size = None
        self._entry_offset_in_dir = []
        self.exist = False
        self.core_seted = False
        self.parent_directory_seted = False

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
        self.core_seted = False
        self.parent_directory_seted = False

    def set_core(self, core):
        self.core = core
        self._cluster_size = core.fat_bot_sector.cluster_size
        self.core_seted = True

    def set_parent_directory(self, parent_directory_descriptor):
        self.parent_directory = parent_directory_descriptor
        self.parent_directory_seted = True

    def new_entry_from_bytes(self, entries_data, entry_offsets_in_dir):
        self.entries_data = entries_data  # todo think may be we need check empty list
        self._entry_offset_in_dir = entry_offsets_in_dir
        self._short_name = self._read_short_name()
        if len(self.entries_data) > 1:
            self._long_name = self._read_long_name()
        else:
            self._long_name = self._short_name
        self._write_datetime = self._read_date_time()
        self._data_cluster = self._read_data_cluster()
        pass

    def new_entry(self, file_name, dir_listing, create_long=True, data_cluster=None, size=None, attr="",
                  date_time=None):
        entry = self.name_generator.get_oem_name(file_name, dir_listing)
        self._short_name = entry.decode("cp866")
        self._long_name = self._short_name
        self._attributes = self._parse_attributes(attr)
        entry += self._attributes.attr_byte
        entry += b"\x00" * 8
        first_cluster_high, first_cluster_low = self._generate_address(data_cluster, size)
        entry += first_cluster_high
        write_time, write_date = self._parse_write_time(date_time)
        entry += write_time + write_date + first_cluster_low
        entry += b"\x00" * 4
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
                self._create_long_directory_entry(number, name_part, check_sum, number + 1 == len(name_parts)))

    def _create_long_directory_entry(self, number, name_parts, check_sum, is_last=False):
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
            if not self.core_seted:
                raise Exception("Core module missing")
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

    def rename(self, new_file_name, short_names_listing, long_names_listing=None):
        self._write_short_name(new_file_name, short_names_listing)
        if long_names_listing is not None:
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

    @property
    def data_offset(self):
        return self.core.fat_bot_sector.calc_cluster_offset(self._data_cluster)

    @property
    def data_cluster(self):
        return self._data_cluster

    @property
    def size(self):
        return self.raw_size()

    def raw_size(self):
        return self._read_data(self.entries_data[0], *self._dir.file_size)

    def update_size_in_descriptor(self):
        size = self.calculate_size_on_disk()
        size_data = struct.pack('<I', size)
        self.entries_data = self._replace_data_in_write(self.entries_data[0], size_data, *self._dir.file_size)

    """
       //////////////////////////////////////
       //////   END OPEN METHODS ZONE  //////
       //////   DISK OPERATIONS ZONE   //////
       //////////////////////////////////////
    """

    def delete(self, clear_cluster=False):
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
        if not self.parent_directory_seted:
            raise Exception("Parent directory missing")
        if len(self.entries_data) <= len(self._entry_offset_in_dir):
            self._write_entry_on_disk(self.entries_data,
                                      self._entry_offset_in_dir)  # check is always offsets order correct
            self._free_old_offsets(self._entry_offset_in_dir[len(self.entries_data):])
            self._entry_offset_in_dir = self._entry_offset_in_dir[:len(self.entries_data)]
        else:
            self._free_old_offsets(self._entry_offset_in_dir)
            self._entry_offset_in_dir = []
            self._allocate_offsets_for_entry()
            self._write_entry_on_disk(self.entries_data, self._entry_offset_in_dir)

    def _write_entry_on_disk(self, entries_data, entry_offsets):
        for entry_data, entry_offset in zip(entries_data, entry_offsets):
            self.core.image_reader.set_data_global(entry_offset, entry_data)

    def _delete_fat_chain(self, start_cluster):
        self.core.fat_tripper.delete_file_fat_chain(start_cluster)

    def _delete_file_entry_on_disk(self, file_entries_offsets, clean=False):
        data = b'\xe5'
        if clean:
            data = b'\x00' * 32
        for file_entry_offset in file_entries_offsets:
            self.core.image_reader.set_data_global(file_entry_offset, data)

    def _delete_data_clusters(self, start_cluster):
        offsets = self.core.fat_tripper.get_file_clusters_offsets_list(start_cluster)
        zero_cluster = b'\x00' * self._cluster_size
        for offset in offsets:
            self.core.image_reader.set_data_global(offset, zero_cluster)

    def _free_old_offsets(self, offsets):
        self.parent_directory._mark_free_place(offsets)
        self._delete_file_entry_on_disk(offsets, clean=True)

    def _allocate_offsets_for_entry(self):
        self._entry_offset_in_dir = self.parent_directory._get_entry_place_to_flush(len(self.entries_data))

    def _get_file_allocated_clusters(self, cluster_number):
        return self.core.fat_tripper.get_file_clusters_list(cluster_number)
    def _get_cluster_offset(self, cluster):
        return self.core.fat_bot_sector.calc_cluster_offset(cluster)

    def calculate_size_on_disk(self):
        size_in_bytes = 0
        if self.attributes.directory:
            if not self.core_seted:
                raise Exception("Core missed, please init core to use this func")
            directory = self.core.file_system_utils.low_level_utils.parse_directory_descriptor(self._data_cluster)
            size_in_bytes += len(self._get_file_allocated_clusters(self._data_cluster)) * self._cluster_size
            size_in_bytes += directory.calculate_size_on_disk()
        else:
            # todo make this operation more easy
            size_in_bytes += len(self._get_file_allocated_clusters(self._data_cluster)) * self._cluster_size
        return size_in_bytes

    def write_data_into_file(self,file_size ,data_stream, rewrite= True): # todo make normal file add data with add to exist file
        file_offset_stream = None
        if rewrite:
            start_cluster = self.extend_file(file_size, delete_excessive_allocation=True)
            file_offset_stream = self._data_offsets_stream(self._get_cluster_offset(start_cluster))
        else:
            start_cluster = self.extend_file(file_size, to_selected_size=False)
            file_offset_stream = self._data_offsets_stream(self._get_cluster_offset(start_cluster))
        for data, offset in zip(data_stream, ):
            self.core.image_reader.set_data_global(offset, data)

    def _get_file_last_cluster(self):
        return self.core.fat_tripper.get_file_clusters_list(self._data_cluster)[-1:][0] # maybe if it will be a stream we have a problem

    def _get_file_number_cluster_from_end(self, number):
        return self.core.fat_tripper.get_file_clusters_list(self._data_cluster)[-abs(number):][0]

    def _data_offsets_stream(self, start_cluster_offset):
        get_offset = False
        for x in self.core.fat_tripper.get_file_clusters_offsets_list(self._data_cluster):
            if x == start_cluster_offset:
                get_offset = True
            if get_offset:
                yield x

    def extend_file(self, file_size, to_selected_size = True,delete_excessive_allocation = False):
        preferred_size_in_clusters = self._count_clusters(file_size)
        current_size_in_cluster = self._count_clusters(self.calculate_size_on_disk())
        extend_size = (preferred_size_in_clusters - current_size_in_cluster) if to_selected_size else preferred_size_in_clusters
        if extend_size < 0:
            if delete_excessive_allocation:
                del_start_cluster = self._get_file_number_cluster_from_end(extend_size)
                self._delete_fat_chain(del_start_cluster)
                self.core.fat_tripper.set_cluster_entry(del_start_cluster)
                return self._data_cluster
                # to doing that we need to check how fat tripper del fat_table chain
            else:
                raise Exception("unforeseen operation , you tryied negative file extend")
                # raise  unforeseen operation , you tryied negative file extend
                pass
        else:
            last , status = self.core.fat_tripper.extend_file(self._data_cluster, extend_size)
            if not status:
                raise Exception("No  memory to allocation")
            else:
                return last
            # raise here exception if allocation status equal false


    """
           //////////////////////////////////////
           ////// END DISK OPERATIONS ZONE //////
           ////// START ENTRY WORKERS ZONE //////
           //////////////////////////////////////
    """

    def _replace_data_in_write(self, were, data, offset, length, pack):
        return were[0: offset] + data + were[offset + length:]

    def _write_short_name(self, file_name, dir_listing):
        name_data = self.name_generator.get_oem_name(file_name, dir_listing)
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
        dir_first_cluster_high = self._read_data(self.entries_data[0], *self._dir.first_cluster_low)
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
            FatReaderExceptions.ZeroSizeAllocationException()
        data_cluster, operation_status = self.core.fat_tripper.allocate_place(clusters_amount)
        if operation_status:
            if clear_allocated_area:
                self._delete_data_clusters(data_cluster)
        else:
            FatReaderExceptions.AllocationMemoryOutException()
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

    def _read_data(self, were, offset, length, parse=False):
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


class _NameGenerator:
    def __init__(self):
        self.dir_listing = None
        pass

    def get_oem_name(self, name, dir_listing):
        self.dir_listing = dir_listing
        if name not in [".", ".."]:  # fixme tuple
            oem_name, incorrect_translate = self._generate_short_name(name)
            oem_name = self._generation_last_value(oem_name, incorrect_translate)
            return self._write_short_name(oem_name)
        else:
            return self._write_short_name(name.encode("cp866"))

    def _write_short_name(self, oem_name):
        marker = None
        name = None
        extension = None
        if oem_name not in [b".", b".."]:  # default_correct_name
            marker = oem_name.split(b'.')
            marker.append(b'')
            name, extension = marker[0], marker[1]
            name = name[0:8]
            extension = extension[0:3]
        else:
            name = oem_name
            extension = b''
        return name + (b'\x20' * (11 - len(name) - len(extension))) + extension

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
        extension_marker = translated_name[::-1].find('.', 0)  # fixme rfind
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
        return oem_name not in self.dir_listing

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
                if self._check_name(new_name):
                    return new_name
