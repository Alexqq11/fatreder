import re
class CommandParser:
    def __init__(self, command_prompt = None):
        self._command_prompt  = ""
        self.command = ""
        self._flags = []
        self._paths = []
        self.other_collections = []
        if command_prompt:
            self.parse_command_prompt(command_prompt)
    @property
    def flags(self):
        return set(self._flags)
    @property
    def paths(self):
        return self._paths

    def parse_command_prompt(self, command_prompt):
        self._command_prompt = command_prompt
        command_prompt , collected = self.parse_all_path(command_prompt)
        self._paths = collected
        command_prompt, collected = self.parse_flags(command_prompt)
        self._flags = collected
        command_prompt , collected = self.parse_command(command_prompt)
        self.command = command_prompt
        self._flags.append(self.command)
        self.other_collections = collected

    def parse_all_path(self, command_prompt : str):
        path_pattern = re.compile(r'\"(?P<path>.*?)\"')
        path_collector = []
        m = path_pattern.search(command_prompt)
        while m:
            path_dict = m.groupdict()
            path_collector.append(path_dict["path"])
            command_prompt.replace('"' +path_dict["path"] +'"', '')
            m = path_pattern.search(command_prompt)
        path_collector.reverse()
        return command_prompt, path_collector

    def parse_flags(self, command_prompt):
        args_pattern = re.compile(r"--?(?P<flags>\w+)")
        flag_collector = []
        m = args_pattern.search(command_prompt)
        while m:
            flag_dict = m.groupdict()
            flag_collector.append(flag_dict["flags"])
            remove = ""
            if len(flag_dict["flags"])> 1:
                remove = "--" + flag_dict["flags"]
            else:
                remove = "-" + flag_dict["flags"]
            command_prompt.replace(remove, '')
            m = args_pattern.search(command_prompt)
        flag_collector.reverse()
        return command_prompt, flag_collector

    def parse_command(self, command_prompt):
        splited = command_prompt.split()
        return splited[0], splited

class Command:
    def __init__(self, command_name,default_function , default_args):
        self.command_name = command_name
        self.default_function = default_function
        self.function_dictionary = {set(command_name):(default_function, default_args)}
    def add_function_flags(self, flags_set, params , function = None ):
        if function:
            self.function_dictionary[flags_set] = (function, params)
        else:
            self.function_dictionary[flags_set] = (self.default_function, params)
    def execute(self, flag_set: set, dynamic_args):
        func, static_args = self.function_dictionary[flag_set]
        func(**dynamic_args, **static_args)

class CommandExecutor:
    def __init__(self, commands = None):
        self.command_dict = dict()
        self.command_parser = CommandParser()
        if commands:
            self.command_dict = {command.command_name : command for command in commands}
    def append_command(self, command : Command):
        self.command_dict[command.command_name] = command
    def execute_command(self, command_prompt):
        self.command_parser.parse_command_prompt(command_prompt)
        self.command_dict[self.command_parser.command].execute(self.command_parser.flags, self.command_parser.paths)

