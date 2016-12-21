import datetime
import struct


class DirectoryAttributes:
    def __init__(self):
        self.attr_read_only = None
        self.attr_hidden = None
        self.attr_system = None
        self.attr_volume_id = None
        self.attr_directory = None
        self.attr_archive = None
        self.attr_long_name = None

    def __add_attr(self, attribute_string, attribute_symbol, attribute_field):
        if attribute_field:
            attribute_string += attribute_symbol
        else:
            attribute_string += '_'
        return attribute_string

    def get_attributes_string(self):
        attribute_string = ''
        attribute_string = self.__add_attr(attribute_string, 'r', self.attr_read_only)
        attribute_string = self.__add_attr(attribute_string, 'h', self.attr_hidden)
        attribute_string = self.__add_attr(attribute_string, 's', self.attr_system)
        attribute_string = self.__add_attr(attribute_string, 'v', self.attr_volume_id)
        attribute_string = self.__add_attr(attribute_string, 'd', self.attr_directory)
        attribute_string = self.__add_attr(attribute_string, 'a', self.attr_archive)
        attribute_string = self.__add_attr(attribute_string, 'l', self.attr_long_name)
        return attribute_string

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


class DateTimeFormat:
    def __init__(self, date_bytes, time_bytes):
        self.date_bytes = date_bytes
        self.time_bytes = time_bytes
        self.year = None
        self.day = None
        self.month = None
        self.seconds = None
        self.minutes = None
        self.hours = None
        self.datetime = None
        self.time = None
        self.date = None
        self._parse_date()
        self._parse_time()
        self._set_date_time()

    def _set_date_time(self):

        if self.month == 0 or self.month > 12:  # exceptions
            self.month = 1
        if self.day == 0:
            self.day = 1
        if self.hours > 23:
            self.hours = 23
        if self.minutes > 59:
            self.minutes = 59
        if self.seconds > 59:
            self.seconds =59

        self.datetime = datetime.datetime(self.year, self.month, self.day, self.hours, self.minutes, self.seconds)
        self.time = datetime.time(self.hours, self.minutes, self.seconds)
        self.date = datetime.date(self.year, self.month, self.day)

    def _count_data(self, from_in, to_in, where):
        step = 1
        number_summary = 0
        i = to_in
        while i >= from_in:  # for i in range(to_in - 1 , from_in + 1, -1):
            number_summary += where[i] * step
            step *= 2
            i -= 1
        return number_summary

    def _shift(self, lst):
        len_lst = len(lst)
        if len_lst < 16:
            lst.reverse()
            while len_lst < 16:
                lst.append(0)
                len_lst += 1
            lst.reverse()
        return lst

    def _parse_date(self):
        bin_list = [int(x) for x in bin(self.date_bytes)[2:]]
        bin_list = self._shift(bin_list)  # caution
        self.year = 1980 + self._count_data(0, 6, bin_list)
        self.month = self._count_data(7, 10, bin_list)
        self.day = self._count_data(11, 15, bin_list)

    def _parse_time(self):
        bin_list = self._shift([int(x) for x in bin(self.time_bytes)[2:]])
        self.hours = self._count_data(0, 4, bin_list)
        self.minutes = self._count_data(5, 10, bin_list)
        self.seconds = 2 * self._count_data(11, 15, bin_list)
