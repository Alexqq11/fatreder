import mmap
import struct


class ImageReader:
    def __init__(self, path):
        self.image = None
        self.file_stream = None
        self.path = path
        self._set_mapped_image()
        self.file_global_offset = 0
        self.readonly = None

    def _set_mapped_image(self, params="r+b"):
        length = 512*1024*1024
        if self.image:
            self.close_reader()
        if params == "r+b":
            self.readonly = True
        elif params == "xb":
            self.readonly = False
        f = open(self.path, params)
        self.file_stream = f
        self.image = f    #self.image = mmap.mmap(f.fileno(), length, offset=0)

    def _get_parse_mod(self, size):
        mod_parameter = ''
        if size == 1:
            mod_parameter = '<B'
        elif size == 2:
            mod_parameter = '<H'
        elif size == 4:
            mod_parameter = '<I'
        return mod_parameter

    def set_global_offset(self, offset):
        self.file_global_offset = offset

    def convert_to_int(self, data, size):
        return struct.unpack(self._get_parse_mod(size), data)[0]

    def set_data_global(self, offset, data):
        #if self.readonly:
            #self._set_mapped_image("xb")
        self.image.seek(offset)
        self.image.write(data)

    def get_data_global(self, offset, size, convert_integer=False):
        if not self.readonly:
            self._set_mapped_image()
        self.image.seek(offset)
        buffer = self.image.read(size)
        if convert_integer:
            buffer = self.convert_to_int(buffer, size)  # struct.unpack(self._get_parse_mod(size), buffer)[0]
        return buffer

    def get_data_local(self, local_offset, size, convert_integer=False):
        if not self.readonly:
            self._set_mapped_image()
        self.image.seek(self.file_global_offset + local_offset)
        buffer = self.image.read(size)
        if convert_integer:
            buffer = self.convert_to_int(buffer, size)  # struct.unpack(self._get_parse_mod(size), buffer)[0]
        return buffer

    def close_reader(self):
        #self.image.close()
        self.file_stream.close() # todo exceptions
        self.image = None
        self.file_stream = None
