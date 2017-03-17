import operator
import sys

import ArgparseModule
import FatTableReader as Ftw
import FileSystemUtils as Fsw
import ImageWorker as Image
import ReservedRegionReader as Rrr
from  FatReaderExceptions import *


class Asker:
    def __init__(self):
        pass

    def askYesNo(self, msg=''):
        answer = input("{}\ty/n?\n".format(msg))
        return answer.lower() in ["y", "yes", "yep", "да", "д"]


class CommandExecutor():
    def __init__(self, core):
        self.commands = ("load", "ls", "cp", "cd", "md", "pwd", "cat", "rm", "move", "rmdir", "exit", "rename", "size")
        self.utils = core.file_system_utils
        self.core = core
        self.args = None

    def execute(self, command, args):
        if command in self.commands:
            self.args = args
            # self.NoneArgumentPath()
            operator.methodcaller(command)(self)
        else:
            raise InvalidCommandException("this command wasn't registered")

    def load(self):
        self.core.load(*self.args.path)
        self.utils = self.core.file_system_utils
        pass

    def ls(self):
        if not self.args.path:
            self.args.path = ["./"]
        elif type(self.args.path) is not list:
            self.args.path = [self.args.path]
        self.utils.ls(*self.args.path, long=self.args.long, all_files=self.args.all_files,
                      recursive=self.args.recursive)
        pass

    def cp(self):
        if self.args.external and self.args.internal:
            raise InvalidCommandException("this arguments can't be used at the same time")
        if self.args.external:
            self.utils.cpf(*self.args.path)
        elif self.args.internal:
            self.utils.cpt(*self.args.path)
        else:
            self.utils.cp(*self.args.path)

    def cd(self):
        self.utils.cd(self.args.path)

    def md(self):
        self.utils.md(*self.args.path)

    def pwd(self):
        self.utils.pwd()

    def cat(self):
        self.utils.cat(*self.args.path, self.args.byte, self.args.text, self.args.encoding)

    def rm(self):
        self.utils.rm(*self.args.path, clear=self.args.clear)

    def move(self):
        self.utils.move(*self.args.path)

    def rename(self):
        self.utils.rename(*self.args.path)

    def rmdir(self):
        self.utils.rmdir(*self.args.path, self.args.clear)

    def size(self):
        self.utils.size(*self.args.path)

    def exit(self):
        self.core.keep_alive = False

    def NoneArgumentPath(self):
        if self.args.path == None:
            self.args.path = []


class Core(Asker):
    def __init__(self, debug=True):
        super().__init__()
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
        if not debug:
            self.run()

    def run(self):
        if len(sys.argv) > 1:
            print(sys.argv)
            try:
                self.argument_handler()
            except FatReaderException:
                pass
            except FileNotFoundError:
                print("Image not found")
        else:
            self.keep_alive = True
            print("please, load image to continue work")
        while self.keep_alive:
            try:
                command_prompt = input("]>")
                if command_prompt:
                    self.argument_handler(command_prompt)
            except FatReaderException:
                pass
            except FileNotFoundError:
                print("Image not found")

        self.close_reader()

    def argument_handler(self, args=None):
        if args == None:
            args, command = self.args_parser.parse(sys.argv)
            self.keep_alive = args.keep_alive
            self.scan_disk = not args.noscan
            if args.load:
                self.load(args.load)
            else:
                print("please, load image to continue work")
        else:
            # args, command = None , None
            if self.keep_alive:
                try:
                    args, command = self.args_parser.parse(self.args_parser.get_args_list(args))
                    if not (self.image_loaded or command == "load"):
                        print("please, load image to continue work")
                    else:
                        if command == "load":
                            pass
                            # ans = self.askYesNo("check image for errors")
                            # print(ans)
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
        self.file_system_utils = Fsw.FatReaderUtils(self)

    def init(self, path):
        self._init_image(path)
        self._init_fat_boot_sector()
        self._init_fat_tripper()
        self.init_FSW()
        self.image_loaded = True

    def close_reader(self):
        self.image_reader.close_reader()


if __name__ == "__main__":
    c = Core(debug=False)
