from enum import Enum


class NodeType(Enum):
    root = 0
    command_add_subdirectory = 1
    command_add_library = 2


class Node:
    def __init__(self, type):
        self.type = type
        self.children = []

    def get_type(self):
        return self.type

    def get_children(self):
        return self.children

    def add_child(self, child):
        self.children.append(child)
