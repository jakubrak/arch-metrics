import os
import sys
import clang.cindex
from cmakeparser.parser import Parser
from cmakeparser.lexer import Lexer
from cmakeparser.node import NodeType


def get_full_name(c):
    if c is None:
        return ''
    elif c.kind == clang.cindex.CursorKind.TRANSLATION_UNIT:
        return ''
    else:
        res = get_full_name(c.semantic_parent)
        if res != '':
            return res + '::' + c.spelling
    return c.spelling


def find_classes(node, filename):
    if node.kind == clang.cindex.CursorKind.CLASS_DECL and node.location.file.name == filename and node.is_definition():
        print("\t", get_full_name(node))

    for c in node.get_children():
        find_classes(c, filename)


def walk(node, directory):
    if node.get_type() == NodeType.command_add_subdirectory:
        lexer = Lexer()
        parser = Parser()
        subdirectory = os.path.join(directory, node.get_source_dir())
        walk(parser.parse(subdirectory, lexer), subdirectory)
    elif node.get_type() == NodeType.command_add_library:
        if not node.is_imported():
            print(directory + ": " + node.get_library_name())
            for filename in node.get_source_list():
                if filename.endswith(".h"):
                    index = clang.cindex.Index.create()
                    clang_args = '-x c++ --std=c++11'.split()
                    file_path = os.path.join(directory, filename)
                    tu = index.parse(file_path, args=clang_args)
                    find_classes(tu.cursor, file_path);
    for c in node.get_children():
        walk(c, directory)


lexer = Lexer()
parser = Parser()
node = parser.parse(sys.argv[1], lexer)
walk(node, sys.argv[1])
