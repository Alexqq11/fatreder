import FatStructures as fat
import FileReader as fw
import ImageWorker as image
import FatTableWorker as ftw
import FileSystemWalker as FSW
""""reserved region class """
""" bs - boot sector"""
""""bpb bios parameter block """


class Core:
    def __init__(self):
        self.image_reader = None
        self.fat_bot_sector = None
        self.fat_tripper = None
        self.dir_parser = None
        self.file_system_utils = None

    def _init_image(self, path):
        self.image_reader = image.ImageReader(path)

    def _init_fat_boot_sector(self):
        self.fat_bot_sector = fat.FatBootSector(self.image_reader)
    def _init_fat_tripper(self):
        self.fat_tripper = ftw.FatTripper(self, self.fat_bot_sector.get_fat_offsets_list())

    def _init_dir_parser(self):
        self.dir_parser = fw.DirectoryParser(self)
    def init_FSW(self):
        self.file_system_utils = FSW.FileSystemUtil(self)

    def init(self, path):
        self._init_image(path)
        self._init_fat_boot_sector()
        self._init_fat_tripper()
        #self._init_dir_parser
        self.init_FSW()

    def close_reader(self):
        self.image_reader.close_reader()
    pass

c = Core()

inp = input("Path to image: ")
c.init(inp) # "..\.\dump (1).iso")
while(True):
    inp = input("]>")
    args = [x for x in inp.split()]
    if (args[0].lower() == 'cd'):
        c.file_system_utils.change_directory(args[1])
    elif (args[0].lower() == 'ls'):
        info = c.file_system_utils.get_working_directory_information()
        for entry in info:
            print(entry)
    elif (args[0].lower() == 'pwd'):
        print(c.file_system_utils.calculate_directory_path())
    elif (args[0].lower() == 'info'):
        print(c.file_system_utils.get_file_information("архЭВМ"))
    elif (args[0].lower() == 'help'):
        print("cd , ls . pwd, info , exit, help")
    elif (args[0].lower() == 'exit'):
        break
    else:
        print('command not found')
"""""""""
c.file_system_utils.change_directory('/архЭВм/Конспекты от Артура/')
c.file_system_utils.change_directory('../')
info = c.file_system_utils.get_working_directory_information()
for entry in info:
    print(entry)
print(c.file_system_utils.calculate_directory_path())
c.file_system_utils.change_directory('../')
info = c.file_system_utils.get_working_directory_information()
for entry in info:
    print(entry)
print(c.file_system_utils.calculate_directory_path())
print(c.file_system_utils.get_file_information("архЭВМ"))
"""
#dir  = c.dir_parser.nio_parse_directory(c.fat_bot_sector.get_root_dir_offset())
#for file in dir.files:
    #print(file)
 #   dir.files[file].set_user_representation()
  #  print(dir.files[file].human_readable_view.to_string())
#print(dir.files)
"""""""""
for x in c.dir_parser.File_entries:
    x.set_user_representation()
    print(x.human_readable_view.to_string())
"""""
c.close_reader()
er
