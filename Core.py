import operator
import sys

import ArgparseModule
import FatTableReader as Ftw
import FileSystemUtils as Fsw
import ImageWorker as Image
import ReservedRegionReader as Rrr
import Structures
from FatReaderExceptions import *


class Core:
    def __init__(self, *, path_to_image=None):
        self.image_reader = None
        self.fat_boot_sector = None
        self.fat_table = None
        self.file_system_utils = None
        self.image_loaded = False
        if path_to_image:
            self.load(path_to_image)

    def load(self, path):
        self.init(path)

    def init(self, path):
        self._init_image(path)
        self._init_fat_tripper()
        self.init_file_system_utils()
        self.image_loaded = True

    def _init_image(self, path):
        self.image_reader = Image.ImageReader(path)
        checker = Rrr.BootSectorChecker()
        data = self.image_reader.get_data_global(0, 100)
        result = checker.check(data)
        if result != "FAT32":
            if result == "ERROR":
                self.image_reader.close_reader()
                self.image_reader = None
                raise UnExpectedCriticalError("Image reserved region corrupted or this is not FAT* image")
            else:
                self.image_reader.close_reader()
                self.image_reader = None
                raise UnExpectedCriticalError("this is not FAT32 image , other FAT types not supported")
        else:
            self.fat_boot_sector = Rrr.BootSectorParser(data)

    def _init_fat_tripper(self):
        self.fat_table = Ftw.FatTablesManager(self)

    def init_file_system_utils(self):
        self.file_system_utils = Fsw.FatReaderUtils(self)

    def close_reader(self):
        self.image_reader.close_reader()


if __name__ == "__main__":
    pass
