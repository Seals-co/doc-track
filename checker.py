from dataclasses import dataclass
from tree_sitter import Parser

import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Node, Point

PY_LANGUAGE = Language(tspython.language())
MAX_U_LONG = 1 << 64
MAX_LINE_SIZE = MAX_U_LONG # Big value, not supposed to be overflown

@dataclass
class CodeNode:
    type: str = ""
    name: str = ""
    from_line: int = 0
    to_line: int = 0


@dataclass
class Difference(frozen=True):
    from_line: int = 0
    to_line: int = 0

def find_first_comment(node: Node):
    if node.type == 'comment':
        return node
    for child in node.children:
        result = find_first_comment(child)
        if result:
            return result
    return None

def line_is_comment(line: str, language: str = "python"):
    parser = Parser(PY_LANGUAGE)

    tree = parser.parse(bytes(line, 'utf8'))
    root = tree.root_node

    children = root.children

    return len(children) == 1 and children[0].type == "comment"

def line_is_tag(line: str, tags: list[str], language: str = "python"):
    parser = Parser(PY_LANGUAGE)

    tree = parser.parse(bytes(line, 'utf8'))
    root = tree.root_node

    children = root.children

    if len(children) == 1 and children[0].type == "comment":
        for tag in tags:
            if tag in line[children[0].start_byte:children[0].end_byte]:
                return True
    return False

def line_is_tagged(line: str, tags: list[str], language: str = "python"):
    parser = Parser(PY_LANGUAGE)

    tree = parser.parse(bytes(line, 'utf8'))
    root = tree.root_node

    comment = find_first_comment(root)
    if comment is None:
        return False

    for tag in tags:
        if tag in line[comment.start_byte:comment.end_byte]:
            return True

    return False


def retrieve_end_point(node: Node, language: str = "python") -> Point | None:
    """
    retrieve endpoint of class_definition or funcion_definition
    """
    for child in node.children:
        if child.type == ":":
            return child.end_point
    return None

def get_structure_code_nodes(file_content: str, target_line: int, language: str) -> list[CodeNode]:
    """
    Retrieve list of CodeNode that represents list of classes / functions where a line is in
    """
    parser = Parser(PY_LANGUAGE)


    tree = parser.parse(file_content.encode())
    root = tree.root_node

    row = target_line
    point = (row, MAX_LINE_SIZE)
    node = root.named_descendant_for_point_range(point, point)

    contexts = []
    while node:
        typ = node.type
        if language == 'python' and typ in ('function_definition', 'class_definition'):
            name = node.child_by_field_name('name')
            contexts.append(CodeNode(type=typ, name=name.text.decode(), from_line=node.start_point[0], to_line=retrieve_end_point(node, language)[0]))
        elif language == 'javascript' and typ in ('function_declaration', 'method_definition', 'class_declaration'):
            name = node.child_by_field_name('name')
            contexts.append(CodeNode(type=typ, name=name.text.decode(), from_line=node.start_point[0], to_line=retrieve_end_point(node, language)[0]))
        elif language == 'html' and typ == 'element':
            start_tag = node.child_by_field_name('start_tag') or node.child(0)
            tagname = start_tag.child_by_field_name('tag_name')
            contexts.append(CodeNode(type="balise", name=tagname.text.decode(), from_line=node.start_point[0], to_line=node.end_point[0]))
        node = node.parent

    return contexts[::-1]

def get_differences() -> dict[str, Difference]:
    """
    returns list of differenteces
    """
    ...

def get_last_comment_line_before_index(lines: list[str], ind: int, language: str = "python"):
    i = ind - 1
    while i > -1 and line_is_comment(lines[i], language) or lines[i].strip() == "":
        i -= 1
    return i + 1

def get_doc_tracked_differences(tags: list[str]) -> dict[str, Difference]:
    result = {}
    differences = get_differences()
    # Retrieve if one of the line contained in differences ends with doc-tag
    # or is precedeed by a line that contains doc-tag

    for file_path, differences in differences.items():
        file = open(file_path, "r")
        lines = file.readlines()
        content = "".join(lines)
        for difference in differences:
            add = False
            line_before_index = get_last_comment_line_before_index(lines, difference.from_line)
            for i in range(line_before_index, difference.from_line):
                if line_is_tag(lines[i], tags):
                    add = True
                    break
            if not add:
                # Check if one of the added / removed lines contains doc
                for i in range(difference.from_line, difference.to_line + 1):
                    if line_is_tagged(lines[i], tags):
                        add = True
                        break
            if add:
                result[file_path] = set([*result.get(file_path, set([])), difference])

        for difference in differences:
            add = False
            code_nodes = get_structure_code_nodes(content, difference.from_line, "python")
            for code_node in code_nodes:
                add = False
                line_before_index = get_last_comment_line_before_index(lines, code_node.from_line)
                for i in range(line_before_index, code_node.from_line):
                    if line_is_tag(lines[i], tags):
                        add = True
                        break
                if not add:
                    for i in range(code_node.from_line, code_node.to_line + 1):
                        if line_is_tagged(lines[i], tags):
                            add = True
                            break
                if add:
                    result[file_path] = set([*result.get(file_path, set([])), difference])

    return result


def run():
    return 22