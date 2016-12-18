import FileEntryMetaData as meta


class FileEntryStructure:
    def __init__(self):
        self.ldir_list = []
        self.dir = None
        self.human_readable_view = None

    def append_ldir_entry(self, ldir_entry):
        self.ldir_list.append(ldir_entry)

    def set_dir(self, dir_entry):
        self.dir = dir_entry

    def clear_lfn(self):
        self.ldir_list = []

    def get_short_name(self):
        return self.dir.parse_name()

    def get_long_name(self):
        name = ''
        for entries in self.ldir_list:
            name += entries.parse_name_part()
        return name.strip('￿')

    def set_user_representation(self):
        self.human_readable_view = HumanReadableFileView()
        self.human_readable_view.init(self)


class HumanReadableFileView:
    def __init__(self):
        self.directory_name = None
        self.create_datetime_format = None
        self.attributes = None
        self.access_datetime_format = None
        self.write_datetime_format = None

    def init(self, file_object):
        directory = file_object.dir
        self.create_datetime_format = meta.DateTimeFormat(directory.dir_create_date, directory.dir_create_time)
        self.access_datetime_format = meta.DateTimeFormat(directory.dir_last_access_date, 0)
        self.write_datetime_format = meta.DateTimeFormat(directory.dir_write_date, directory.dir_write_time)
        self.attributes = meta.DirectoryAttributes()
        self.attributes.parse_attributes(directory.dir_attributes)
        if len(file_object.ldir_list):
            self.directory_name = file_object.get_long_name()
        else:
            self.directory_name = file_object.get_short_name().lower()

    def to_string(self):
        file_representation = ''
        file_representation += self.write_datetime_format.date.isoformat() + ' '
        file_representation += self.write_datetime_format.time.isoformat() + '    '
        file_representation += self.attributes.get_attributes_string() + '     '
        file_representation += self.directory_name
        return file_representation


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

    def parse_name(self):
        processing_string = self.dir_name.decode('cp866')
        name = processing_string[0:8].strip()
        extension = processing_string[8:].strip()
        if len(extension):
            name += '.' + extension
        return name

    def parse_entry_data(self, image_reader, entry_start_offset, old_offset=0, return_offset=False):
        image_reader.set_global_offset(entry_start_offset)
        self.dir_name = image_reader.get_data(0, 11)
        self.dir_attributes = image_reader.get_data(11, 1)
        self.dir_nt_reserved = image_reader.get_data(12, 1)
        self.dir_create_time_tenth = image_reader.get_data(13, 1)  # 13 1
        self.dir_create_time = image_reader.get_data(14, 2, True)  # 14 2
        self.dir_create_date = image_reader.get_data(16, 2, True)  # 16 2
        self.dir_last_access_date = image_reader.get_data(18, 2, True)  # 18 2
        self.dir_first_cluster_high = image_reader.get_data(20, 2)  # 20 2 // старшее слово номера первого кластера
        self.dir_write_time = image_reader.get_data(22, 2, True)  # 22 2 время последней записи , создание тоже запись
        self.dir_write_date = image_reader.get_data(24, 2, True)  # 24 2 дата последней записи,создание файла тоже запис
        self.dir_first_cluster_low = image_reader.get_data(26, 2)  # 26 2 младшее слово первого кластера
        self.dir_file_size = image_reader.get_data(28, 4, True)  # 28 4
        self.fat_entry_number = image_reader.convert_to_int(self.dir_first_cluster_low + self.dir_first_cluster_high, 4)
        if return_offset:
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

    def parse_name_part(self):
        return (self.ldir_name1 + self.ldir_name2 + self.ldir_name3).decode('utf-16')

    def parse_entry_data(self, image_reader, entry_start_offset, old_offset=0, return_offset=False):
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
        if return_offset:
            image_reader.set_global_offset(old_offset)
