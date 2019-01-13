from cmakeparser.node import Node
from cmakeparser.node import NodeType


class AddSubdirectoryCommand(Node):
    def __init__(self, source_dir, binary_dir, exclude_from_all, directory):
        super(AddSubdirectoryCommand, self).__init__(NodeType.command_add_subdirectory, directory)
        self.source_dir = source_dir
        self.binary_dir = binary_dir
        self.exclude_from_all = exclude_from_all

    def get_source_dir(self):
        return self.source_dir

    def get_binary_dir(self):
        return self.binary_dir

    def is_excluded_from_all(self):
        return self.exclude_from_all


class AddSubdirectoryCommandParser:
    def parse(self, arg_list, directory):
        source_dir = None
        binary_dir = None
        exclude_from_all = False

        if len(arg_list) > 0:
            source_dir = arg_list[0]
        if len(arg_list) > 1:
            binary_dir = arg_list[1]
        if len(arg_list) > 2 and arg_list[2] == "EXCLUDE_FROM_ALL":
            exclude_from_all = True

        return AddSubdirectoryCommand(source_dir, binary_dir, exclude_from_all, directory)
