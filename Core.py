import FatTableReader as Ftw
import FileSystemUtils as Fsw
import ImageWorker as Image
import ReservedRegionReader as Rrr
from  FatReaderExceptions import *
import ArgparseModule
class Core:
    def __init__(self):
        self.image_reader = None
        self.fat_bot_sector = None
        self.fat_tripper = None
        self.dir_parser = None
        self.file_system_utils = None
        self.rrp = None

    def _init_image(self, path):
        self.image_reader = Image.ImageReader(path)

    def _init_fat_boot_sector(self):
        self.fat_bot_sector = Rrr.BootSectorParser(self.image_reader)  # fat.FatBootSector(self.image_reader)

    def _init_fat_tripper(self):
        self.fat_tripper = Ftw.FatTableReader(self, self.fat_bot_sector.fat_offsets_list)

    def init_FSW(self):
        self.file_system_utils = Fsw.FileSystemUtil(self)

    def init(self, path):
        self._init_image(path)
        self._init_fat_boot_sector()
        self._init_fat_tripper()
        self.init_FSW()

    def close_reader(self):
        self.image_reader.close_reader()

    pass
if __name__ == "__main__":
    c = Core()
    c.init("..\.\dump (1).iso")

    while (True):
        try:
            command_prompt = input("]>")
        except FatReaderException:
            pass

    c.close_reader()
