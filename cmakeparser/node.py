from enum import Enum


class NodeType(Enum):
    root = 0
    command_add_subdirectory = 1
    command_add_library = 2


class Node:
    def __init__(self, type, directory):
        self.type = type
        self.directory = directory
        self.children = []

    def get_type(self):
        return self.type

    def get_directory(self):
        return self.directory

    def get_children(self):
        return self.children

    def add_child(self, child):
        self.children.append(child)
