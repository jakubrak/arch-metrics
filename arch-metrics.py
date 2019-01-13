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


def find_classes(filename):
    classes = []

    index = clang.cindex.Index.create()
    clang_args = '-x c++ --std=c++11'.split()
    tu = index.parse(filename, args=clang_args)

    nodes = [tu.cursor]

    while nodes:
        node = nodes.pop()
        if node.kind == clang.cindex.CursorKind.CLASS_DECL \
                and node.location.file.name == filename \
                and node.is_definition():
            classes.append(node)

        for c in node.get_children():
            nodes.append(c)

    return classes


def walk(directory):
    class_categories = dict()

    lexer = Lexer()
    parser = Parser()

    nodes = [parser.parse(directory, lexer)]

    while nodes:
        node = nodes.pop()

        if node.get_type() == NodeType.command_add_subdirectory:
            nodes.append(parser.parse(os.path.join(directory, node.get_source_dir()), lexer))
        elif node.get_type() == NodeType.command_add_library:
            if not node.is_imported():
                print(node.get_directory() + ": " + node.get_library_name())
                classes = []
                for filename in node.get_source_list():
                    if filename.endswith(".h"):
                        classes += find_classes(os.path.join(node.get_directory(), filename))
                class_categories[node] = classes

        for c in node.get_children():
            nodes.append(c)

    return class_categories


class_categories = walk(sys.argv[1])

for ct in class_categories:
    for c in class_categories[ct]:
        class_name = get_full_name(c)
        if c.is_abstract_record():
            print("[ABSTRACT]\t", class_name)
        else:
            print("\t\t\t", class_name)
