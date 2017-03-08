import os
import os.path
import re


class NameConflictResolver:
    def __init__(self):
        self.dir_listing = None
        self.long_listing = None
        self.order_pattern = re.compile("(?P<number>\(\d +\))$")
        pass

    def get_new_names(self, file_name, is_directory, short_names, long_names):
        self.dir_listing = short_names
        self.long_listing = long_names
        new_name_long = self._resolve_long_name(file_name, is_directory, long_names)
        new_short_name = self._resolve_oem_name(new_name_long, short_names)
        return new_name_long, new_short_name

    def _resolve_long_name(self, file_name, is_directory, long_names):
        new_name = file_name
        while new_name in long_names:
            new_name = self._make_increment(new_name, is_directory)

        return new_name

    def _make_increment(self, file_name, is_directory):
        processed_part = file_name
        ext = ''
        if not is_directory:
            processed_part, ext = os.path.splitext(file_name)
        find = self.order_pattern.search(processed_part)
        if find:
            find = find.groupdict()
            processed_part = processed_part[0:-len(find["number"])]
            number = int(find["number"][1:-1])
            processed_part = "{0}({1})".format(processed_part, number)
        else:
            processed_part = "{0}(1)".format(processed_part)
        return "{0}{1}".format(processed_part, ext)

    def _resolve_oem_name(self, name, dir_listing):
        self.dir_listing = dir_listing
        if name not in [".", ".."]:  # fixme tuple
            oem_name, incorrect_translate = self._generate_short_name(name)
            oem_name = self._generation_last_value(oem_name, incorrect_translate)
            return self._write_short_name(oem_name)
        else:
            return self._write_short_name(name.encode("cp866"))

    @staticmethod
    def _write_short_name(oem_name):
        # marker = None
        # name = None
        # extension = None
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

    @staticmethod
    def _is_bad_literal(liter):
        unsupported_values = b'\x22\x2a\x2b\x2c\x2f\x3a\x3b\x3c\x3d\x3e\x3f\x5b\x5c\x5d\x5e\x7c'
        return liter < b'\x20' and liter != b'\x05' or liter in unsupported_values

    def _encode_name_to_oem_encoding(self, name):
        oem_string = b''
        # oem_liter = b''
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

    @staticmethod
    def _clear_name_content(name):
        name = name.upper()
        translated_name = name.replace(' ', '')
        extension_marker = translated_name[::-1].find('.', 0)  # fixme rfind
        if extension_marker != -1:
            translated_name = translated_name[:-extension_marker].replace('.', '') + '.' + translated_name[
                                                                                           -extension_marker:]
        return translated_name, extension_marker

    @staticmethod
    def _translate_to_short_name(oem_string: bytes, extension_marker):
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

    @staticmethod
    def _join_name(prefix, postfix, extension):
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
