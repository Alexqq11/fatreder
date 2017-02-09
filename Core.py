import FatTableReader as Ftw
import FileSystemUtils as Fsw
import ImageWorker as Image
import ReservedRegionReader as Rrr
from  FatReaderExceptions import *
from  CUICommandParser import *
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

    def initCommands(c : Core):
        commands_list = []
        cd = Command("cd", c.file_system_utils.change_directory,dict())
        commands_list.append(cd)
        ls = Command("ls",c.file_system_utils.get_working_directory_information,dict())
        ls.add_function_flags(("h","ls"),{"hidden": True})
        ls.add_function_flags(("a", "ls"),{"datetime": True, "attributes": True,"size": True})
        ls.add_function_flags(("a", "h", "ls"), {"datetime": True, "attributes": True, "size": True, "hidden": True})
        commands_list.append(ls)
        rm = Command("rm",c.file_system_utils.remove_file,{"recoverable":False})
        rm.add_function_flags(tuple("c"), {"recoverable" : False, "clear": True})
        rm.add_function_flags(tuple("r"), {"recoverable" : True, "clear": False})
        commands_list.append(rm)
        cp = Command("cp", None, dict())
        cp.add_function_flags(tuple("f"), dict(),c.file_system_utils.copy_on_image)
        cp.add_function_flags(tuple("d"), dict(),c.file_system_utils.copy_directory)
        commands_list.append(cp)
        mkdir = Command("mkdir", c.file_system_utils.new_directory,dict())
        commands_list.append(mkdir)
        info = Command("info", c.file_system_utils.get_file_information,dict())
        commands_list.append(info)
        transfer = Command("transfer",c.file_system_utils.transfer,dict())
        commands_list.append(transfer)
        rename = Command("rename", c.file_system_utils.rename, dict())
        commands_list.append(rename)
        return  commands_list

    command_executor = CommandExecutor(initCommands(c))
    while (True):
        try:
            command_prompt = input("]>")
            command_executor.execute_command(command_prompt)
        except FatReaderException:
            pass


            """""""""
            args = [x for x in inp.split()]
            command =CommandParser(inp)
            command.command = args[0]
            if (args[0] == 'cd'):
                c.file_system_utils.change_directory(command.path[0])
            elif (command.command == 'ls'):
                info = c.file_system_utils.get_working_directory_information()
                for entry in info:
                    print(entry)
            elif (command.command == 'pwd'):
                print(c.file_system_utils.calculate_directory_path())
            elif (command.command == 'info'):
                print(c.file_system_utils.get_file_information(args[1]))
            elif (command.command == 'help'):
                print("cd , ls . pwd, info ,cp, mkdir, rn, ts, exit, help")
            elif (command.command == 'exit'):
                break
            elif (command.command == 'mkdir'):
                c.file_system_utils.new_directory(join_name(args))
            elif (command.command == 'cp'):
                c.file_system_utils.copy_on_image(args[1], args[2])
            elif (command.command == 'cp-d'):
                c.file_system_utils.copy_directory(args[1], args[2])
            elif (command.command == 'rn'):
                c.file_system_utils.rename(args[1], args[2])
            elif (command.command == 'ts'):
                c.file_system_utils.transfer(args[1], args[2])
            elif (command.command == 'rm-r'):
                c.file_system_utils.remove_file(join_name(args))
            elif (command.command == 'rm-a'):
                c.file_system_utils.remove_file(join_name(args), recoverable=False)
            elif (command.command == 'rm-c'):
                c.file_system_utils.remove_file(join_name(args), clean=True)
            elif (command.command == 'cat'):
                data = c.file_system_utils.cat_data(args[1])
                i = iter(data)
                encoding = 'utf-8'
                if len(args) == 3:
                    encoding = args[2]
                print(next(i).decode(encoding))
            else:
                print('command not found')
       """""""""
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
    # dir  = c.dir_parser.nio_parse_directory(c.fat_bot_sector.get_root_dir_offset())
    # for file in dir.files:
    # print(file)
    #   dir.files[file].set_user_representation()
    #  print(dir.files[file].human_readable_view.to_string())
    # print(dir.files)
    """""""""
    for x in c.dir_parser.File_entries:
        x.set_user_representation()
        print(x.human_readable_view.to_string())
    """""
    c.close_reader()
