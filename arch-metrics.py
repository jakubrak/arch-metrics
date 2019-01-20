import os
import re
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
    clang_args = '-x c++'.split()
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

def count_class_refernces(filename, classes):
    index = clang.cindex.Index.create()
    args = "-x c++ -g -Wall -Werror --std=gnu++11 " \
        "-I/home/powerless/volar/volar/src/dbconn " \
        "-I/home/powerless/volar/volar/src/dbconn/public/include/dbconn " \
        "-I/home/powerless/volar/volar/src/base/public/include " \
        "-I/home/powerless/volar/volar/src/problem/public/include " \
        "-I/home/powerless/volar/volar/src/aircraftPerformance/public/include " \
        "-I/home/powerless/volar/volar/src/airwayNetwork/public/include " \
        "-I/home/powerless/volar/volar/src/navigation/public/include " \
        "-I/home/powerless/volar/volar/src/util/public/include " \
        "-I/home/powerless/volar/volar/src/weather/public/include " \
        "-I/home/powerless/volar/volar/src/instances/public/include " \
        "-I/home/powerless/volar/volar/src/inputReader/public/include " \
        "-I/home/powerless/volar/volar/src/tfr/public/include " \
        "-I/home/powerless/volar/volar/src/error/public/include " \
        "-isystem /usr/include/postgresql " \
        "-isystem /usr/include/postgresql/9.6/server " \
        "-I/usr/lib/gcc/x86_64-linux-gnu/6/include"
    tu = index.parse(filename, args=args.split())
    for d in tu.diagnostics:
        print(d.spelling)

    nodes = [tu.cursor]
    reference_count = 0

    while nodes:
        node = nodes.pop()

        if node.kind == clang.cindex.CursorKind.INCLUSION_DIRECTIVE:
            print(node.location.line, node.kind.name, node.spelling)

        if node.location.file and node.location.file.name == filename:
            print(node.location.file.name, node.location.line, node.kind.name, node.spelling)

        for c in node.get_children():
            nodes.append(c)

    return reference_count


def generate_class_categories(directory):
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


# class_categories = generate_class_categories(sys.argv[1])
#
# for ct in class_categories:
#     for c in class_categories[ct]:
#         class_name = get_full_name(c)
#         if c.is_abstract_record():
#             print("[ABSTRACT]\t", class_name)
#         else:
#             print("\t\t\t", class_name)

# for c in find_classes("../volar/volar/src/dbconn/DbContext.h"):
#     print(get_full_name(c))

#count_class_refernces("../volar/volar/src/dbconn/DbContext.cpp", [])
#count_class_refernces("../test.cpp", [])


class ClassCategory:
    def __init__(self, name):
        self.name = name


class TranslationUnit:
    def __init__(self, filename, compilation_flags):
        self.filename = filename
        self.compilation_flags = compilation_flags

    def get_filename(self):
        return self.filename

    def get_compilation_flags(self):
        return self.compilation_flags

    def parse(self, package_directory, root_directory):
        print("Parsing", self.filename)

        classes = set()
        class_references = set()

        index = clang.cindex.Index.create()
        tu = index.parse(self.filename, args=self.compilation_flags)
        for d in tu.diagnostics:
            print(d.severity, d.spelling)
            # if d.severity > clang.cindex.Diagnostic.Warning:
            #    raise Exception(d.spelling)

        nodes = [tu.cursor]

        while nodes:
            node = nodes.pop()
            if node.location.file and node.spelling and package_directory in node.location.file.name:
                if node.kind == clang.cindex.CursorKind.CXX_BASE_SPECIFIER:
                    print(node.spelling, node.kind.name, node.type.kind, node.type.get_declaration().location.file.name)

            if node.kind == clang.cindex.CursorKind.CLASS_DECL \
                    and node.is_definition():

                full_name = get_full_name(node)
                if package_directory in node.location.file.name:
                    classes.add(full_name)

            if (node.kind == clang.cindex.CursorKind.TYPE_REF \
                    or node.kind == clang.cindex.CursorKind.CXX_BASE_SPECIFIER) \
                    and node.type.kind == clang.cindex.TypeKind.RECORD:
                node_type_declaration = node.type.get_declaration()
                if node_type_declaration:
                    node_type_definition = node_type_declaration.get_definition()
                    if node_type_definition \
                            and node_type_definition.location.file \
                            and root_directory in node.type.get_declaration().location.file.name:
                        #print("Adding", node.spelling, node.type.get_declaration().location.file.name)
                        class_references.add(node.type.spelling)

            for c in node.get_children():
                nodes.append(c)

        return classes, class_references


class Package:
    def __init__(self, name, directory):
        self.name = name
        self.directory = directory
        self.translation_units = []
        self.classes = set()
        self.class_references = set()

    def add_translation_unit(self, translation_unit, root_directory):
        (classes, class_references) = translation_unit.parse(self.directory, root_directory)
        self.classes = self.classes.union(classes)
        self.class_references = self.class_references.union(class_references)
        self.translation_units.append(translation_unit)

    def get_name(self):
        return self.name

    def get_directory(self):
        return self.directory

    def get_translation_units(self):
        return self.translation_units

    def get_classes(self):
        return self.classes

    def get_class_references(self):
        return self.class_references


def scan_project():
    build_directory = os.path.abspath("../volar/volar/cmake-build-debug")
    compilation_db = clang.cindex.CompilationDatabase.fromDirectory(build_directory)

    source_directory = ""
    for compile_command in compilation_db.getAllCompileCommands():
        current_source_directory = os.path.dirname(compile_command.filename)
        print(current_source_directory)
        if len(current_source_directory) < len(source_directory) or not source_directory:
            source_directory = current_source_directory

    packages = dict()

    for compile_command in compilation_db.getAllCompileCommands():
        include_dirs = ["-I/usr/local/lib/clang/7.0.0/include"]
        last_arg = ""
        package_name = ""
        for arg in compile_command.arguments:
            if arg.startswith("-I"):
                include_dirs.append(arg)
            elif last_arg.startswith("-isystem"):
                include_dirs.append(last_arg)
                include_dirs.append(arg)
            elif last_arg.startswith("-o"):
                package_name = re.findall(r"/(.*).dir/", arg)[0]
            last_arg = arg
        tu = TranslationUnit(compile_command.filename, include_dirs)
        if package_name == "InputReader":
            if packages.get(package_name):
                packages[package_name].add_translation_unit(tu, source_directory)
            else:
                package = Package(package_name, os.path.relpath(compile_command.directory, build_directory))
                package.add_translation_unit(tu, source_directory)
                packages[package_name] = package

    print("Root source directory:", source_directory)
    return packages


packages = scan_project()
for package_name, package in packages.items():
    print("Package: " + package_name)
    print("Translation units:")
    for tu in package.get_translation_units():
        print(tu.get_filename())
    print("Classes:")
    print(package.get_classes())
    print("Class references:")
    print(package.get_class_references())
    print("\n")
