import FatStructures as fat
import FileWorker as fw
import ImageWorker as image

""""reserved region class """
""" bs - boot sector"""
""""bpb bios parameter block """


class Core:
    def __init__(self):
        self.image_reader = None
        self.fat_bot_sector = None
        self.fat_tripper = None
        self.dir_parser = None

    def _init_image(self, path):
        self.image_reader = image.ImageReader(path)

    def _init_fat_boot_sector(self):
        self.fat_bot_sector = fat.FatBootSector(self.image_reader)
    def _init_fat_tripper(self):
        self.fat_tripper = fw.FatTripper(self, self.fat_bot_sector.get_fat_offsets_list())

    def _init_dir_parser(self):
        self.dir_parser = fw.DirectoryParser(self)

    def init(self, path):
        self._init_image(path)
        self._init_fat_boot_sector()
        self._init_fat_tripper()
        self._init_dir_parser()

    def close_reader(self):
        self.image_reader.close_reader()

    pass

c = Core()
c.init("..\.\dump (1).iso")
c.dir_parser.nio_parse_directory(c.fat_bot_sector.get_root_dir_offset())
print(len(c.dir_parser.File_entries))

for x in c.dir_parser.File_entries:
    x.set_user_representation()
    print(x.human_readable_view.to_string())
c.close_reader()
