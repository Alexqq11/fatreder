import argparse
import shlex


class ArgsParser:
    def __init__(self):
        self.parser = None
        self.subparsers = None
        self.init_parsers()

    def parse(self, args_list):
        return self.parser.parse_args(args_list), args_list[0]

    def get_args_list(self, string):
        return shlex.split(string)

    def init_parsers(self):
        # global parser
        parser_program = argparse.ArgumentParser(prog="fatreader",
                                                 description='watch an extract file and directories in fat32 images')
        parser_program.add_argument('-n', "--no-scan", dest='noscan', action='store_true',
                                    help='do not check the image for errors')
        parser_program.add_argument('-k', "--keep-alive", dest='keep_alive', action='store_true',
                                    help='do not exit from util after get sys.args')
        parser_program.add_argument('-l', "--load", dest='load', action='store', help=' load working image from path')
        subparsers = parser_program.add_subparsers(help='sub-command help')

        parser_load = subparsers.add_parser("load", help="load -h , --help", description="load open image")
        parser_load.add_argument(dest='path', metavar='path', nargs=1)
        parser_load.add_argument('-n', "--no-scan", dest='noscan', action='store_true',
                                 help='do not check the image for errors')
        # ls
        parser_ls = subparsers.add_parser("ls", help="ls -h, --help",
                                          description='ls is a command to print list files in directory in fat reader util')
        parser_ls.add_argument(dest='path', metavar='path', nargs='?')  # * - all ? zero or one
        parser_ls.add_argument('-l', '--long', dest='long', action='store_true',
                               help='print file information in human readable format')
        parser_ls.add_argument('-a', '--all', dest='all_files', action='store_true',
                               help='print file information for all files in directory')
        parser_ls.add_argument('-r', '--recursive', dest='recursive', action='store_true',
                               help='print file information for files in directory and subdirectories')

        # cp
        parser_cp = subparsers.add_parser("cp", help="cp -h, --help",
                                          description='cp is a command to copy files or directories from/on/in image')
        parser_cp.add_argument(dest='path', metavar='path', nargs=2)  # * - all ? zero or one
        parser_cp.add_argument('-e', '--external', dest='external', action='store_true',
                               help='copy file or directory from os to image')
        parser_cp.add_argument('-i', '--internal', dest='internal', action='store_true',
                               help='copy file or directory from image to os')

        # cd
        parser_cd = subparsers.add_parser("cd", help="cd -h, --help",
                                          description='cd is a command to change dir in fat32 image')
        parser_cd.add_argument(dest='path', metavar='path', nargs='?')  # * - all ? zero or one | number

        # md
        parser_md = subparsers.add_parser("md", help="md -h, --help",
                                          description='md is a command to make directory(ies) in image')
        parser_md.add_argument(dest='path', metavar='path', nargs=1)  # * - all ? zero or one | number

        # pwd
        parser_pwd = subparsers.add_parser("pwd", help="pwd -h, --help",
                                           description='pwd is a command to calculate ful path to working directory in image')
        # exit
        parser_exit = subparsers.add_parser("exit", help="exit -h, --help",
                                            description='exit from fat reader util')

        # move
        parser_move = subparsers.add_parser("move", help="move -h, --help",
                                            description='move is a command to move files or directories in image')
        parser_move.add_argument(dest='path', metavar='path', nargs=2)  # * - all ? zero or one

        # cat
        parser_cat = subparsers.add_parser("cat", help="cat -h, --help",
                                           description='cat is a command to print file content')
        parser_cat.add_argument(dest='path', metavar='path', nargs=1)  # * - all ? zero or one
        parser_cat.add_argument('-b', '--byte', dest='byte', action='store_true', help='get data in hex stream')
        parser_cat.add_argument('-t', '--text', dest='text', action='store_true', help='get data in text stream')
        parser_cat.add_argument('-e', '--encoding', dest='encoding', action='store', help=' set data encoding')

        # rm
        parser_rm = subparsers.add_parser("rm", help="rm -h, --help",
                                          description="rm is a command to delete file in image")
        parser_rm.add_argument(dest='path', metavar='path', nargs=1)
        parser_rm.add_argument('-c', '--clear', dest="clear", action="store_true",
                               help='erase data on cluster by zeros')

        # rmdir
        parser_rmdir = subparsers.add_parser("rmdir", help="rmdir -h, --help",
                                             description="rmdir is a command to delete directories in image")
        parser_rmdir.add_argument(dest='path', metavar='path', nargs=1)
        parser_rmdir.add_argument('-c', '--clear', dest="clear", action="store_true",
                                  help='erase data on cluster by zeros')
        # rename
        parser_rename = subparsers.add_parser("rename", help="rename -h, --help",
                                              description="rename is command to rename files and directories in image")
        parser_rename.add_argument(dest='path', metavar='path', nargs=2)

        self.parser = parser_program
        self.subparsers = subparsers
