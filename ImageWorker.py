import mmap
import struct


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

    def get_data(self, local_offset, size, convert_integer=False):
        self.image.seek(self.file_global_offset + local_offset)
        buffer = self.image.read(size)
        if convert_integer:
            buffer = self.convert_to_int(buffer, size)  # struct.unpack(self._get_parse_mod(size), buffer)[0]
        return buffer

    def close_reader(self):
        self.image.close()
        self.file_stream.close()
