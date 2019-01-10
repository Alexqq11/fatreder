import operator
import sys

import ArgparseModule
import Core
import Structures
from FatReaderExceptions import *

class CommandExecutor:
    def __init__(self, core, fat_reader):
        self.fat_reader = fat_reader
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
        self.fat_reader.load(*self.args.path)
        self.utils = self.core.file_system_utils
        pass

    def ls(self):
        if not self.args.path:
            self.args.path = ["./"]
        elif type(self.args.path) is not list:
            self.args.path = [self.args.path]
        for x in self.utils.ls(*self.args.path, long=self.args.long, all_files=self.args.all_files,
                      recursive=self.args.recursive):
            print(x)
        pass

    def cp(self):
        if self.args.export and self.args.import_file:
            raise InvalidCommandException("this arguments can't be used at the same time")
        if self.args.export:
            self.utils.cp_export(*self.args.path)
        elif self.args.import_file:
            self.utils.cp_import(*self.args.path)
        else:
            self.utils.cp(*self.args.path)

    def cd(self):
        self.utils.cd(self.args.path)

    def md(self):
        self.utils.md(*self.args.path)

    def pwd(self):
        print(self.utils.pwd())

    def cat(self):
        for x in self.utils.cat(*self.args.path, self.args.byte, self.args.text, self.args.encoding):
            print(x)

    def rm(self):
        self.utils.rm(*self.args.path, clear=self.args.clear)

    def move(self):
        self.utils.move(*self.args.path)

    def rename(self):
        self.utils.rename(*self.args.path)

    def rmdir(self):
        self.utils.rmdir(*self.args.path, self.args.clear)

    def size(self):
        print(self.utils.size(*self.args.path))

    def exit(self):
        self.fat_reader.keep_alive = False


class FatReader(Structures.Asker):
    def __init__(self):
        super().__init__()
        self.core = Core.Core()
        self.args_parser = ArgparseModule.ArgsParser()
        self.command_executor = CommandExecutor(self.core, self)
        self.keep_alive = False
        self.scan_disk = True
        self.image_loaded = False

    def close_reader(self):
        self.core.close_reader()

    def load(self, path):
        self.core.load(path)
        self.image_loaded = self.core.image_loaded

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
                command_prompt = self._input("]>")
                if command_prompt:
                    self.argument_handler(command_prompt)
            except FatReaderException:
                pass
            except FileNotFoundError:
                print("Image not found")

        self.close_reader()

    def argument_handler(self, args=None):
        if args is None:
            if args.path is None:
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




if __name__ == "__main__":
    fat_reader = FatReader()
    fat_reader.run()

