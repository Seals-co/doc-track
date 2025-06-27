from collections import namedtuple
import checker
from checker import (
    PY_LANGUAGE,
    CodeNode,
    Difference,
    GitDifference,
    find_first_comment,
    line_is_comment,
    line_is_tag,
    line_is_tagged,
    retrieve_end_point,
    get_structure_code_nodes,
    get_git_difference,
    parse_differences,
    get_git_differences,
    get_last_comment_line_before_index,
    content_difference_is_tagged,
    get_doc_tracked_differences,


)
import io
import builtins
import subprocess
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


class TestContentDifferenceIsTagged:
    file_content = """\
print(22) # new line but not tagged
print(23) # new line but not tagged
print(24) # new line but not tagged
print(25) # old line but not tagged
# test
def fct(): # new line tagged with above tag
    return 22 # new line tagged with above tag

def fct(): # old line tagged # test
    return 22

class Test:
    class SubTest: # old line with tag # test
        def fct():
            return 22 # line updated
"""


    def test_not_tagged(self):
        assert not content_difference_is_tagged(self.file_content, Difference(0, 2), ["# test", "#test"])

    def test_tagged(self):
        assert content_difference_is_tagged(self.file_content, Difference(5, 6), ["# test", "#test"])

    def test_tagged_with_above_comment(self):
        assert content_difference_is_tagged(self.file_content, Difference(9, 9), ["# test", "#test"])

    def test_tagged_with_parents(self):
        assert content_difference_is_tagged(self.file_content, Difference(14, 14), ["# test", "#test"])


class TestGetDifference:
    def test_get_git_difference(self):
        assert get_git_difference(10, 2, 10, 3) == GitDifference(from_rm_line=9, to_rm_line=10, from_add_line=9, to_add_line=11)

    def test_get_git_difference_new_content(self):
        assert get_git_difference(0, 0, 1, 3) == GitDifference(from_rm_line=-1, to_rm_line=-1, from_add_line=0, to_add_line=2)

    def test_get_git_difference_no_rm(self):
        assert get_git_difference(5, 0, 6, 2) == GitDifference(from_rm_line=-1, to_rm_line=-1, from_add_line=5, to_add_line=6)

    def test_get_git_difference_no_add(self):
        assert get_git_difference(25, 1, 27, 0) == GitDifference(from_rm_line=24, to_rm_line=24, from_add_line=-1, to_add_line=-1)


class TestParseDifferences:

    def test_parse_differences(self):
        output = """\
diff --git a/foo.py b/foo.py
index e69de29..b123abc 100644
--- a/foo.py
+++ b/foo.py
@@ -0,0 +1,3 @@
+def hello():
+    print("Hello, world!")
+

diff --git a/bar.py b/bar.py
index aabbcc1..ddeeff2 100644
--- a/bar.py
+++ b/bar.py
@@ -10,2 +10,3 @@ def do_something():
-    x = 1
-    y = 2
+    x = 42
+    y = 99
+    z = x + y

@@ -25 +27,0 @@ def remove_me():
-    print("This will be removed")

@@ -42,0 +43,2 @@ def do_something():
+    x = 42
+    y = 99


diff --git a/baz.py b/baz.py
index 1234567..89abcde 100644
--- a/baz.py
+++ b/baz.py
@@ -3 +3,2 @@ def unchanged():
-    pass
+    print("Was empty")
+    return True
"""
        res = parse_differences(output)

        assert res == {
            'foo.py': [
                GitDifference(from_rm_line=-1, to_rm_line=-1, from_add_line=0, to_add_line=2),
            ],
            'bar.py': [
                GitDifference(from_rm_line=9, to_rm_line=10, from_add_line=9, to_add_line=11),
                GitDifference(from_rm_line=24, to_rm_line=24, from_add_line=-1, to_add_line=-1),
                GitDifference(from_rm_line=-1, to_rm_line=-1, from_add_line=42, to_add_line=43),
            ],
            'baz.py': [
                GitDifference(from_rm_line=2, to_rm_line=2, from_add_line=2, to_add_line=3),
            ],
        }


class TestGetDocTrackedDifferences:
    diff_content = """\
diff --git a/bar.py b/bar.py
index f0c897e..ee730b2 100644
--- a/bar.py
+++ b/bar.py
@@ -2,2 +2,3 @@ def do_something(): # test
-    x = 1
-    y = 2
+    x = 42
+    y = 99
+    z = x + y
@@ -7 +7,0 @@ def remove_me():
-    print("This will be removed")
@@ -13 +12,0 @@ def remove_me():
-    print("This will be removed")
@@ -20,0 +20,2 @@ class Test:
+                self.x2 = 42
+                self.y = 99
"""

    file_content_version1 = """\
def do_something(): # test
    x = 1
    y = 2

def remove_me():
    # test
    print("This will be removed")
    print("This will not be removed")

def remove_me():
    # test
    print("This will not be removed")
    print("This will be removed")

# test
class Test:
    class Test2:
        def fct(self):
            def do_something2(self):
                self.x = 1
"""

    file_content_version2 = """\
def do_something(): # test
    x = 42
    y = 99
    z = x + y

def remove_me():
    # test
    print("This will not be removed")

def remove_me():
    # test
    print("This will not be removed")

# test
class Test:
    class Test2:
        def fct(self):
            def do_something2(self):
                self.x = 1
                self.x2 = 42
                self.y = 99
"""

    mock_results = []
    call_counter = {}
    fct_called = ""

    MockCompletedProcess = namedtuple("CompletedProcess", ["stdout", "stderr"])

    def git_show_mock(self):
        self.call_counter.setdefault(self.fct_called, 0)

        res = self.MockCompletedProcess(stdout=self.mock_results[self.call_counter[self.fct_called]], stderr="")
        self.call_counter[self.fct_called] += 1
        return res

    def test_no_differences(self, monkeypatch):
        self.fct_called = "test_no_differences"
        monkeypatch.setattr(checker, "get_git_differences", lambda version1, version2, path: {})

        res = get_doc_tracked_differences(None, None, None, ["# test", "#test"])

        assert res == {}

    def test_some_differences(self, monkeypatch):
        """
        going to return 3 differences because they are in a tagged scope
        but not the difference of -13 +12,0 because it's not tagged
        """
        self.fct_called = "test_some_differences"

        self.mock_results = [
            self.diff_content,
            self.file_content_version1,
            self.file_content_version2,
        ]
        monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: self.git_show_mock())

        res = get_doc_tracked_differences(None, None, None, ["# test", "#test"])

        assert res == {
            "bar.py": set([
                GitDifference(from_rm_line=1, to_rm_line=2, from_add_line=1, to_add_line=3),
                GitDifference(from_rm_line=6, to_rm_line=6, from_add_line=-1, to_add_line=-1),
                GitDifference(from_rm_line=-1, to_rm_line=-1, from_add_line=19, to_add_line=20),
            ])
        }
