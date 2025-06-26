import checker
from checker import (
    PY_LANGUAGE,
    CodeNode,
    Difference,
    find_first_comment,
    get_doc_tracked_differences,
    get_last_comment_line_before_index,
    get_structure_code_nodes,
    line_is_comment,
    line_is_tag,
    line_is_tagged,
    retrieve_end_point
)
import io
import builtins
import pytest
from tree_sitter import Parser

LANGUAGE = "python"

@pytest.mark.parametrize("line, expected", [
    ("# comment", True),
    ("#       comment", True),
    ("#comment", True),
    ("print(22)", False),
    ("print(22) # comment", False),
    ("", False),
])
def test_line_is_comment(line, expected):
    assert line_is_comment(line, LANGUAGE) == expected


@pytest.mark.parametrize("line, tags, expected", [
    ("# comment", ["# comment"], True),             # Simple one comment line
    ("#       comment", ["# comment"], False),      # Simple line not having specific tag
    ("# comment 2 # comment", ["# comment"], True), # Two comments with one that is the good tag
    ("print(22) # comment", ["# comment"], False),  # Tag on line of code but its not a tag on its own
    ("", ["# comment"], False),                     # Empty line
])
def test_line_is_tag(line, tags, expected):
    assert line_is_tag(line, tags, LANGUAGE) == expected


@pytest.mark.parametrize("line, tags, expected", [
    ("# comment", ["# comment"], True),             # Simple one comment line
    ("#       comment", ["# comment"], False),      # Simple line not having specific tag
    ("# comment 2 # comment", ["# comment"], True), # Two comments with one that is the good tag
    ("print(22) # comment", ["# comment"], True),   # Tag on line of code
    ("", ["# comment"], False),                     # Empty line
])
def test_line_is_tagged(line, tags, expected):
    assert line_is_tagged(line, tags, LANGUAGE) == expected


@pytest.mark.parametrize("line, is_none, text", [
    ("# comment", False, b"# comment"),                         # Simple one comment line
    ("print(22)", True, b""),                                   # No comment on line
    ("def fct(): # comment", False, b"# comment"),              # Comment on line with code
    ("# comment # comment 2", False, b"# comment # comment 2"), # 2 comments
    ("str = '# comment'", True, b""),                           # String containing comment
])
def test_find_first_comment(line, is_none, text):
    parser = Parser(PY_LANGUAGE)
    tree = parser.parse(bytes(line, 'utf8'))
    root = tree.root_node
    res = find_first_comment(root)
    if is_none:
        assert res is None
    else:
        assert res is not None
        assert res.type == "comment"
        assert res.text == text

@pytest.mark.parametrize("lines, index, res", [
    ([
        "print(22)\n",
        "# comment\n",
        "# comment2\n",
        "\n",
        "\n",
        "print(23)\n",
    ], 5, 1),
    ([
        "print(22)\n",
        "# comment\n",
        "print(23)",
    ], 2, 1),
    ([
        "print(22) # comment\n",
        "# comment\n",
        "print(23)",
    ], 2, 1),
])
def test_get_last_comment_line_before_index(lines, index, res):
    assert get_last_comment_line_before_index(lines, index, LANGUAGE) == res


@pytest.mark.parametrize("content, is_none, result", [
    (
"""def fct():
    print(22)
""", False, (0, 10)
    ),
    (
"""class Class():
    nb = 22
""", False, (0, 14)
    ),
    ("print(22)", True, (0, 10)),
])
def test_retrieve_end_point(content, is_none, result):
    parser = Parser(PY_LANGUAGE)
    tree = parser.parse(bytes(content, 'utf8'))
    root = tree.root_node
    res = retrieve_end_point(root.children[0], LANGUAGE)
    if is_none:
        assert res is None
    else:
        assert res is not None
        assert res[0] == result[0]
        assert res[1] == result[1]


def test_get_structure_code_nodes():
    file_content = \
"""\
class Test:
    class A:
        def test(
            lol
        ): # yes
            def haha(jj): # doc-track
                print(22)
            print(3)
        print(3)
    print(3)
print(3)
"""

    res = get_structure_code_nodes(file_content, 0, LANGUAGE)
    assert res == [
        CodeNode(type="class_definition", name="Test", from_line=0, to_line=0),
    ]

    res = get_structure_code_nodes(file_content, 1, LANGUAGE)
    assert res == [
        CodeNode(type="class_definition", name="Test", from_line=0, to_line=0),
    ]

    res = get_structure_code_nodes(file_content, 2, LANGUAGE)
    assert res == [
        CodeNode(type="class_definition", name="Test", from_line=0, to_line=0),
        CodeNode(type="class_definition", name="A", from_line=1, to_line=1),
    ]

    res = get_structure_code_nodes(file_content, 3, LANGUAGE)
    assert res == [
        CodeNode(type="class_definition", name="Test", from_line=0, to_line=0),
        CodeNode(type="class_definition", name="A", from_line=1, to_line=1),
        CodeNode(type="function_definition", name="test", from_line=2, to_line=4),
    ]

    res = get_structure_code_nodes(file_content, 4, LANGUAGE)
    assert res == [
        CodeNode(type="class_definition", name="Test", from_line=0, to_line=0),
        CodeNode(type="class_definition", name="A", from_line=1, to_line=1),
        CodeNode(type="function_definition", name="test", from_line=2, to_line=4),
    ]

    res = get_structure_code_nodes(file_content, 5, LANGUAGE)
    assert res == [
        CodeNode(type="class_definition", name="Test", from_line=0, to_line=0),
        CodeNode(type="class_definition", name="A", from_line=1, to_line=1),
        CodeNode(type="function_definition", name="test", from_line=2, to_line=4),
    ]

    res = get_structure_code_nodes(file_content, 6, LANGUAGE)
    assert res == [
        CodeNode(type="class_definition", name="Test", from_line=0, to_line=0),
        CodeNode(type="class_definition", name="A", from_line=1, to_line=1),
        CodeNode(type="function_definition", name="test", from_line=2, to_line=4),
        CodeNode(type="function_definition", name="haha", from_line=5, to_line=5),
    ]

    res = get_structure_code_nodes(file_content, 7, LANGUAGE)
    assert res == [
        CodeNode(type="class_definition", name="Test", from_line=0, to_line=0),
        CodeNode(type="class_definition", name="A", from_line=1, to_line=1),
        CodeNode(type="function_definition", name="test", from_line=2, to_line=4),
    ]

    res = get_structure_code_nodes(file_content, 8, LANGUAGE)
    assert res == [
        CodeNode(type="class_definition", name="Test", from_line=0, to_line=0),
        CodeNode(type="class_definition", name="A", from_line=1, to_line=1),
    ]

    res = get_structure_code_nodes(file_content, 9, LANGUAGE)
    assert res == [
        CodeNode(type="class_definition", name="Test", from_line=0, to_line=0),
    ]

    res = get_structure_code_nodes(file_content, 10, LANGUAGE)
    assert res == []


class TestGetDocTrackedDifferences:
    differences_data = {
        "file1.py": [
            Difference(0, 2),
            Difference(5, 6),
            Difference(9, 9),
            Difference(14, 14),
        ]
    }

    file1_content = io.StringIO(
"""\
print(22) # new line but not tagged
print(23) # new line but not tagged
print(24) # new line but not tagged
print(25) # old line but not tagged
# test
def fct(): # new line tagged with abod tag
    return 22 # new line tagged with abod tag

def fct(): # old line tagged # test
    return 22

class Test:
    class SubTest: # old line with tag # test
        def fct():
            return 22 # line updated
"""
    )

    def test_no_differences(self, monkeypatch):
        monkeypatch.setattr(checker, "get_differences", lambda: {})

        res = get_doc_tracked_differences(["# test", "#test"])

        assert res == {}

    def test_some_differences(self, monkeypatch):
        monkeypatch.setattr(builtins, "open", lambda path, mode='r': self.file1_content)
        monkeypatch.setattr(checker, "get_differences", lambda: self.differences_data)


        res = get_doc_tracked_differences(["# test", "#test"])

        assert res == {
            "file1.py":
                {
                    Difference(from_line=5, to_line=6),
                    Difference(from_line=9, to_line=9),
                    Difference(from_line=14, to_line=14),
                }
        }
