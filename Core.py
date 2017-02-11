import operator
import sys

import ArgparseModule
import FatTableReader as Ftw
import FileSystemUtils as Fsw
import ImageWorker as Image
import ReservedRegionReader as Rrr
from  FatReaderExceptions import *


class CommandExecutor:
    def __init__(self, core):
        self.commands = ("load", "ls", "cp", "cd", "md", "pwd", "cat", "rm", "move", "rmdir", "exit")
        self.utils = core.file_system_utils
        self.core = core
        self.args = None

    def execute(self, command, args):
        if command in self.commands:
            self.args = args
            self.NoneArgumentPath()
            operator.methodcaller(command)(self)
        else:
            raise InvalidCommandException()

    def load(self):
        self.core.load(*self.args.path)
        self.utils = self.core.file_system_utils
        pass

    def ls(self):
        self.utils.ls(*self.args.path, self.args.long, self.args.all)
        pass

    def cp(self):
        if self.args.external and self.args.internal:
            raise InvalidCommandException()
        if self.args.external:
            self.utils.copy_from_os(*self.args.path)
        elif self.args.internal:
            self.utils.copy_to_os(*self.args.path)
        else:
            self.utils.cp(*self.args.path)

    def cd(self):
        self.utils.change_directory(self.args.path)

    def md(self):
        self.utils.make_dirs(*self.args.path)

    def pwd(self):
        self.utils.calculate_directory_path()

    def cat(self):
        self.utils.cat(*self.args.path, self.args.byte, self.args.text, self.args.encoding)

    def rm(self):
        self.utils.remove_file(*self.args.path, clean=self.args.clear)

    def move(self):
        self.utils.move(*self.args.path)

    def rmdir(self):
        self.utils.rmdir(*self.args.path, self.args.clear)
    def exit(self):
        self.core.keep_alive = False

    def NoneArgumentPath(self):
        if self.args.path == None:
            self.args.path = []


class Core:
    def __init__(self):
        self.image_reader = None
        self.fat_bot_sector = None
        self.fat_tripper = None
        self.dir_parser = None
        self.file_system_utils = None
        self.rrp = None
        self.args_parser = ArgparseModule.ArgsParser()
        self.command_executor = CommandExecutor(self)
        self.keep_alive = False
        self.scan_disk = True
        self.image_loaded = False
        self.run()

    def run(self):
        if len(sys.argv)> 1:
            print(sys.argv)
            self.argument_handler()
        else:
            self.keep_alive = True
        while self.keep_alive:
            try:
                command_prompt = input("]>")
                self.argument_handler(command_prompt)
            except FatReaderException:
                pass
        self.close_reader()

    def argument_handler(self, args=None):
        if args == None:
            args, command= self.args_parser.parse(sys.argv)
            self.keep_alive = args.keep_alive
            self.scan_disk = not args.noscan
            if args.load:
                self.load(args.load)

        else:
            #args, command = None , None
            if self.keep_alive:
                try:
                    args, command = self.args_parser.parse(self.args_parser.get_args_list(args))
                    self.command_executor.execute(command, args)
                except SystemExit:
                    pass


    def load(self, path):
        self.init(path)

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
        self.image_loaded = True
    def close_reader(self):
        self.image_reader.close_reader()

    pass
class NotAValue:
    def __init__(self):
        pass

if __name__ == "__main__":
    c = Core()
