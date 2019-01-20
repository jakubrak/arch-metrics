import os
import re
import clang.cindex


class TranslationUnit:
    def __init__(self, filename, compilation_flags):
        self.filename = filename
        self.compilation_flags = compilation_flags
        self.class_references = set()

    def get_filename(self):
        return self.filename

    def get_compilation_flags(self):
        return self.compilation_flags

    def parse(self, package_directory, root_directory):
        print("Parsing", self.filename)

        self.class_references = set()

        index = clang.cindex.Index.create()
        tu = index.parse(self.filename, args=self.compilation_flags)
        for d in tu.diagnostics:
            print(d.severity, d.spelling)
            # if d.severity > clang.cindex.Diagnostic.Warning:
            #    raise Exception(d.spelling)

        for c in tu.cursor.walk_preorder():
            if c.kind == clang.cindex.CursorKind.CLASS_DECL and c.is_definition():
                if package_directory in c.location.file.name:
                    self.check_class_definition(c, package_directory, root_directory)

        return self.class_references

    def check_class_definition(self, root_cursor, package_directory, root_directory):
        class_name = root_cursor.type.spelling
        print(class_name)
        for cursor in root_cursor.walk_preorder():
            # if "_terminalProcedure" in cursor.spelling:
            #     for cursor in cursor.walk_preorder():
            #         print("Template! ", cursor.kind.name, cursor.type.spelling, get_full_name(cursor))

            if cursor.kind == clang.cindex.CursorKind.CXX_BASE_SPECIFIER:
                cursor_definition = self.get_cursor_definition(cursor)
                if self.is_class_from_another_project_package(cursor_definition, package_directory, root_directory):
                    self.class_references.add((class_name, cursor_definition.type.spelling))
                    print("\t", cursor.kind.name, cursor.type.spelling, get_full_name(cursor))

            elif cursor.kind == clang.cindex.CursorKind.TYPE_REF:
                cursor_definition = self.get_cursor_definition(cursor)
                if self.is_class_from_another_project_package(cursor_definition, package_directory, root_directory):
                    self.class_references.add((class_name, cursor_definition.type.spelling))
                    #print("\t", cursor.kind.name, node_type.spelling, get_full_name(cursor))

            elif cursor.kind == clang.cindex.CursorKind.CXX_METHOD \
                    or cursor.kind == clang.cindex.CursorKind.CONSTRUCTOR \
                    or cursor.kind == clang.cindex.CursorKind.DESTRUCTOR\
                    or cursor.kind == clang.cindex.CursorKind.CONVERSION_FUNCTION:
                #print("\t", cursor.kind.name, get_full_name(cursor))
                function_definition_node = cursor.get_definition()
                if function_definition_node:  # in case of 'default' keyword used for constructor/destructor
                    self.check_function_definition(function_definition_node, class_name, package_directory, root_directory)

    def check_function_definition(self, root_cursor, class_name, package_directory, root_directory):
        for cursor in root_cursor.walk_preorder():
            if cursor.kind == clang.cindex.CursorKind.TYPE_REF:
                cursor_definition = self.get_cursor_definition(cursor)
                if self.is_class_from_another_project_package(cursor_definition, package_directory, root_directory):
                    self.class_references.add((class_name, cursor_definition.type.spelling))
                    #print("\t\t", cursor.kind.name, cursor.type.spelling, cursor.spelling)

    def is_class_from_another_project_package(self, cursor, package_directory, root_directory):
        return cursor \
                and cursor.location.file \
                and root_directory in cursor.location.file.name \
                and package_directory not in cursor.location.file.name \
                and cursor.type.kind == clang.cindex.TypeKind.RECORD

    def get_cursor_definition(self, cursor):
        cursor_type = cursor.type
        if cursor_type.kind == clang.cindex.TypeKind.LVALUEREFERENCE \
                or cursor_type.kind == clang.cindex.TypeKind.MEMBERPOINTER:
            cursor_type = cursor_type.get_pointee()
        return cursor_type.get_declaration().get_definition()


class Package:
    def __init__(self, name, directory):
        self.name = name
        self.directory = directory
        self.translation_units = []
        self.classes = set()
        self.class_references = set()

    def add_translation_unit(self, translation_unit, root_directory):
        self.class_references = self.class_references.union(translation_unit.parse(self.directory, root_directory))
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
        if package_name == "Dbconn":
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
    for class_reference in sorted(package.get_class_references()):
        print(class_reference)
