import os
from enum import Enum


class TokenType(Enum):
    newline = 0
    space = 1
    identifier = 2
    leftparen = 3
    rightparen = 4
    comment = 5


class Lexer:
    def scan(self, filename):
        if not os.path.exists(filename):
            return
        file = open(filename, "r")
        c = file.read(1)
        identifier = ""
        comment = ""
        while c:
            if '\n' in c:
                if comment:
                    yield TokenType.comment, comment
                    comment = ""
                elif identifier:
                    yield TokenType.identifier, identifier
                    identifier = ""
                yield TokenType.newline, c
            elif c.isspace():
                if identifier:
                    yield TokenType.identifier, identifier
                    identifier = ""
                yield TokenType.space, c
            elif '#' in c:
                if identifier:
                    yield TokenType.identifier, identifier
                    identifier = ""
                comment = c
                yield TokenType.comment, c
            elif '(' in c:
                if identifier:
                    yield TokenType.identifier, identifier
                    identifier = ""
                yield TokenType.leftparen, c
            elif ')' in c:
                if identifier:
                    yield TokenType.identifier, identifier
                    identifier = ""
                yield TokenType.rightparen, c
            elif comment:
                comment += c
            else:
                identifier += c

            c = file.read(1)
