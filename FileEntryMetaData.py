import datetime
import struct
import Structures


class DirectoryAttributesGetter(Structures.DirectoryAttributesStructure):
    def __init__(self, attr, arg_string=False):
        super().__init__()
        self._attribute_byte = None
        self.attr_byte = None
        self.attr_string = None
        if arg_string:
            self.set_string_args(attr)
        else:
            self.set_byte_args(attr)

    def set_byte_args(self,attr_byte):
        self._attribute_byte = attr_byte
        self.attr_byte = struct.unpack('<B', attr_byte)[0]
        self.attr_read_only = (1 == (self.attr_byte & 1))
        self.attr_hidden = (2 == (self.attr_byte & 2))
        self.attr_system = (4 == (self.attr_byte & 4))
        self.attr_volume_id = (8 == (self.attr_byte & 8))
        self.attr_directory = (16 == (self.attr_byte & 16))
        self.attr_archive = (32 == (self.attr_byte & 32))
        self.attr_long_name = (15 == (self.attr_byte & 15))
        self.attr_string = self.get_attributes_string()

    def set_string_args(self, attr_str):
        if 'l' in attr_str:
            attr_str += 'rhsv'
            self.attr_long_name = True
        else: self.attr_long_name = False
        if 'r' in attr_str:  self.attr_read_only = True
        else: self.attr_read_only = False
        if 'h' in attr_str: self.attr_hidden = True
        else: self.attr_hidden = False
        if 's' in attr_str: self.attr_system = True
        else: self.attr_system = False
        if 'v' in attr_str: self.attr_volume_id = True
        else: self.attr_volume_id = False
        if 'd' in attr_str: self.attr_directory = True
        else : self.attr_directory = False
        if 'a' in attr_str: self.attr_archive = True
        else: self.attr_archive = False

        self._calc_attribute_byte()
        self.attr_string = self.get_attributes_string()

    def _calc_attribute_byte(self):
        attribute_byte = 0
        attribute_byte += self.attr_read_only * 1
        attribute_byte += self.attr_hidden  * 2
        attribute_byte += self.attr_system * 4
        attribute_byte += self.attr_volume_id * 8
        attribute_byte += self.attr_directory * 16
        attribute_byte += self.attr_archive * 32
        self.attr_byte = attribute_byte
        self._attribute_byte = struct.pack('<B',attribute_byte)
    @property
    def attributes(self):
        return self.attr_string

    @property
    def attribute_byte(self):
        return  self._attribute_byte

    def read_only(self):
        return self.attr_read_only

    @property
    def hidden(self):
        return self.attr_hidden

    @property
    def system(self):
        return self.attr_system

    @property
    def volume_id(self):
        return self.attr_volume_id

    @property
    def directory(self):
        return self.attr_directory

    @property
    def archive(self):
        return self.attr_archive

    @property
    def long_name(self):
        return self.attr_long_name

    def __add_attr(self, attribute_string, attribute_symbol, attribute_field):
        if attribute_field:
            attribute_string += attribute_symbol
        else:
            attribute_string += '-'
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

class DateTimeGetter:
    def __init__(self, date_time = None):
        self._time_bytes = None
        self._date_bytes = None
        self._init_date_time(date_time)

    @property
    def time_bytes(self):
        return self._time_bytes

    @property
    def date_bytes(self):
        return self._date_bytes

    def _init_date_time(self, date_time = None):
        write_time = None
        if date_time:
            write_time = date_time
        else:
            write_time = datetime.datetime.now()
        self._convert_date(write_time.date())
        self._convert_time(write_time.time())

    def _convert_date(self, date : datetime.date):
        day = bin(date.day)[2:]
        day = ('0' * (5 - len(day))) + day
        month =  bin(date.month)[2:]
        month = ('0' * (4 - len(month))) + month
        year = bin(date.year - 1980)[2:]
        year = ('0' * (7 - len(year))) + year
        binary_date = '0b' + year + month + day
        self._date_bytes = struct.pack('<H', int(binary_date,2))

    def _convert_time(self, time : datetime.time):
        seconds = bin(time.second  // 2)[2:]
        seconds = ('0' * (5 - len(seconds))) + seconds
        minutes = bin(time.minute)[2:]
        minutes = ('0' * (6 - len(minutes))) + minutes
        hours = bin(time.hour)[2:]
        hours = ('0' * (5 - len(hours))) + hours
        binary_time = '0b' + hours + minutes + seconds
        self._time_bytes = struct.pack('<H', int(binary_time,2))

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
        if self.day > 28:
            self.day =28
        if self.hours > 23:
            self.hours = 23
        if self.minutes > 59:
            self.minutes = 59
        if self.seconds > 59:
            self.seconds = 59

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
