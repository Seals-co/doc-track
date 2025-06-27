from dataclasses import dataclass
from tree_sitter import Parser

import tree_sitter_python as tspython
import subprocess
import re
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


@dataclass(frozen=True)
class GitDifference:
    from_rm_line: int = -1
    to_rm_line: int = -1
    from_add_line: int = -1
    to_add_line: int = -1

@dataclass(frozen=True)
class Difference:
    from_line: int = -1
    to_line: int = -1

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

def get_git_difference(
    rm_start: int,
    rm_len: int,
    add_start: int,
    add_len: int,
) -> GitDifference:
    if add_len:
        from_add_line = add_start - 1
        to_add_line = from_add_line + add_len - 1
    else:
        from_add_line = -1
        to_add_line = -1

    if rm_len:
        from_rm_line = rm_start - 1
        to_rm_line = from_rm_line + rm_len - 1
    else:
        from_rm_line = -1
        to_rm_line = -1


    return GitDifference(
        from_add_line=from_add_line,
        to_add_line=to_add_line,
        from_rm_line=from_rm_line,
        to_rm_line=to_rm_line,
    )


def parse_differences(output: str) -> dict[str, list[GitDifference]]:
    """
    Parse `git diff` output to
    return a dict mapping each changed file to a list of GitDifference objects,
    """
    differences = {}
    current_file = None

    for line in output.splitlines():
        if line.startswith('diff --git'):
            current_file = None  # Reset on new diff block
        elif line.startswith('+++ b/'):
            current_file = line[6:]
            differences.setdefault(current_file, [])
        elif line.startswith('@@'):
            match = re.match(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))?', line)
            if match and current_file:
                rm_start = int(match.group(1))
                rm_len = int(match.group(2) or 1)
                add_start = int(match.group(3))
                add_len = int(match.group(4) or 1)

                difference = get_git_difference(rm_start, rm_len, add_start, add_len)
                differences[current_file].append(difference)

    return differences

def get_git_differences(
    version1: str | None,
    version2: str | None,
    path: str | None,
) -> dict[str, list[GitDifference]]:
    """
    Returns a dict mapping each changed file to a list of GitDifference objects,
    each representing a hunk of differences as reported by `git diff`.
    """

    args = [a for a in (version1, version2, "--", path) if a]

    result = subprocess.run(['git', 'diff', '--unified=0', *args], capture_output=True, text=True)
    output = result.stdout
    return parse_differences(output)

def get_last_comment_line_before_index(lines: list[str], ind: int, language: str = "python"):
    i = ind - 1
    while i > -1 and line_is_comment(lines[i], language) or lines[i].strip() == "":
        i -= 1
    return i + 1

def content_difference_is_tagged(content: str, difference: Difference, tags: list[str]):
    lines = content.splitlines()

    line_before_index = get_last_comment_line_before_index(lines, difference.from_line)
    for i in range(line_before_index, difference.from_line):
        if line_is_tag(lines[i], tags):
            return True

    # Check if one of the added / removed lines contains doc
    for i in range(difference.from_line, difference.to_line + 1):
        if line_is_tagged(lines[i], tags):
            return True

    code_nodes = get_structure_code_nodes(content, difference.from_line, "python")
    for code_node in code_nodes:
        line_before_index = get_last_comment_line_before_index(lines, code_node.from_line)
        for i in range(line_before_index, code_node.from_line):
            if line_is_tag(lines[i], tags):
                return True

        for i in range(code_node.from_line, code_node.to_line + 1):
            if line_is_tagged(lines[i], tags):
                return True

    return False

def get_file_content(version: str | None, path: str):
    result = ""

    if version:
        show_result = subprocess.run(
            ["git", "show", f"{version}:{path}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True
        )

        result = show_result.stdout
    else:
        cat_result = subprocess.run(
            ["cat", f"{path}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True
        )

        result = cat_result.stdout

    return result

def get_doc_tracked_differences(
    version1: str | None,
    version2: str | None,
    path: str | None,
    tags: list[str]
) -> dict[str, GitDifference]:
    result = {}
    git_differences = get_git_differences(version1, version2, path)
    # Retrieve if one of the line contained in git_differences ends with doc-tag
    # or is precedeed by a line that contains doc-tag

    version1 = version1 or ""
    version2 = version2 or ""
    for file_path, git_differences in git_differences.items():
        content_version_1 = get_file_content(version1, file_path)
        content_version_2 = get_file_content(version2, file_path)

        for git_difference in git_differences:
            difference = Difference(from_line=git_difference.from_rm_line, to_line=git_difference.to_rm_line)
            if difference.from_line != -1:
                if content_difference_is_tagged(content_version_1, difference, tags):
                    result[file_path] = set([*result.get(file_path, set([])), git_difference])
                    continue

            difference = Difference(from_line=git_difference.from_add_line, to_line=git_difference.to_add_line)
            if difference.from_line != -1:
                if content_difference_is_tagged(content_version_2, difference, tags):
                    result[file_path] = set([*result.get(file_path, set([])), git_difference])

    return result
