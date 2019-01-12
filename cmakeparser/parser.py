import os
from cmakeparser.addlibrary import AddLibraryCommandParser
from cmakeparser.addsubdirectory import AddSubdirectoryCommandParser
from cmakeparser.lexer import TokenType
from cmakeparser.lexer import Lexer
from cmakeparser.node import Node
from cmakeparser.node import NodeType
from enum import Enum


class ParserState(Enum):
    commandname = 0
    leftparen = 1
    rightparen = 2
    commandarg = 3


class Parser:
    def __init__(self):
        self.command_map = {"add_subdirectory": AddSubdirectoryCommandParser(),
                            "add_library": AddLibraryCommandParser()}

    def parse(self, directory, lexer):
        state = ParserState.commandname
        command_name = None
        arg_list = []
        node = Node(NodeType.root)
        for token in lexer.scan(os.path.join(directory, "CMakeLists.txt")):
            if state == ParserState.commandname:
                if token[0] == TokenType.identifier:
                    command_name = token[1]
                    state = ParserState.leftparen
            elif state == ParserState.leftparen:
                if token[0] == TokenType.leftparen:
                    state = ParserState.commandarg
            elif state == ParserState.commandarg:
                if token[0] == TokenType.identifier:
                    arg_list.append(token[1])
                if token[0] == TokenType.rightparen:
                    command_parser = self.command_map.get(command_name)
                    if command_parser:
                        node.add_child(command_parser.parse(arg_list))
                    del arg_list[:]
                    state = ParserState.commandname
        return node
