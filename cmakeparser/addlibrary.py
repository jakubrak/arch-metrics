from cmakeparser.node import Node
from cmakeparser.node import NodeType


class AddLibraryCommand(Node):
    def __init__(self, library_name, library_type, imported, exclude_from_all, source_list, directory):
        super(AddLibraryCommand, self).__init__(NodeType.command_add_library, directory)
        self.library_name = library_name
        self.library_type = library_type
        self.imported = imported
        self.exclude_from_all = exclude_from_all
        self.source_list = source_list

    def get_library_name(self):
        return self.library_name

    def get_library_type(self):
        return self.library_type

    def is_excluded_from_all(self):
        return self.exclude_from_all

    def is_imported(self):
        return self.imported

    def get_source_list(self):
        return self.source_list


class AddLibraryCommandParser:
    def parse(self, arg_list, directory):
        library_name = None
        library_type = None
        imported = False
        exclude_from_all = False
        source_list = list()

        if not arg_list:
            return None

        it = iter(arg_list)
        try:
            item = next(it)
            library_name = item

            item = next(it)
            if item in ["STATIC", "SHARED", "MODULE", "OBJECT", "UNKNOWN"]:
                library_type = item
                item = next(it)

            if item in "IMPORTED":
                imported = True
                item = next(it)

            if item in "EXCLUDE_FROM_ALL":
                exclude_from_all = True
                item = next(it)

            while True:
                source_list.append(item)
                item = next(it)

        except StopIteration:
            return AddLibraryCommand(library_name, library_type, imported, exclude_from_all, source_list, directory)
