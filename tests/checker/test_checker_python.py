import subprocess
import typing

import doctrack.checker
from doctrack.checker import (
    Difference,
    GitDifference,
    get_differences_tagged,
    get_doc_tracked_differences,
    get_git_difference,
    parse_differences,
)


def overwrite_git_diff_eq_hash():
    GitDifference.__eq__ = lambda self, obj: (
        self.from_rm_line == obj.from_rm_line
        and self.to_rm_line == obj.to_rm_line
        and self.from_add_line == obj.from_add_line
        and self.to_add_line == obj.to_add_line
    )

    GitDifference.__hash__ = lambda self: hash((
        self.from_rm_line,
        self.to_rm_line,
        self.from_add_line,
        self.to_add_line,
    ))


class TestGetDifference:
    def test_get_git_difference(self):
        assert (get_git_difference(10, 2, 10, 3)
            == GitDifference(from_rm_line=9, to_rm_line=10, from_add_line=9, to_add_line=11))

    def test_get_git_difference_new_content(self):
        assert (get_git_difference(0, 0, 1, 3)
            == GitDifference(from_rm_line=-1, to_rm_line=-1, from_add_line=0, to_add_line=2))

    def test_get_git_difference_no_rm(self):
        assert (get_git_difference(5, 0, 6, 2)
            == GitDifference(from_rm_line=-1, to_rm_line=-1, from_add_line=5, to_add_line=6))

    def test_get_git_difference_no_add(self):
        assert (get_git_difference(25, 1, 27, 0)
            == GitDifference(from_rm_line=24, to_rm_line=24, from_add_line=-1, to_add_line=-1))


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
        overwrite_git_diff_eq_hash()
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
index 225fd2e..d65e857 100644
--- a/bar.py
+++ b/bar.py
@@ -3,2 +3,3 @@ def do_something():
-    x = 1
-    y = 2
+    x = 42
+    y = 99
+    z = x + y
@@ -8,3 +8,0 @@ def remove_me():
-    # test
-    print("This will be removed")
-    # endtest
@@ -17 +14,0 @@ def remove_me():
-    print("This will be removed")
@@ -24,0 +22,2 @@ class Test:
+                self.x2 = 42
+                self.y = 99
"""

    file_content_version1 = """\
# not-test
def do_something():
    x = 1
    y = 2
# endtest

def remove_me():
    # test
    print("This will be removed")
    # endtest
    print("This will not be removed")

def remove_me():
    # test
    print("This will not be removed")
    # endtest
    print("This will be removed")

# test
class Test:
    class Test2:
        def fct(self):
            def do_something2(self):
                self.x = 1
# endtest
"""

    file_content_version2 = """\
# not-test
def do_something():
    x = 42
    y = 99
    z = x + y
# endtest

def remove_me():
    print("This will not be removed")

def remove_me():
    # test
    print("This will not be removed")
    # endtest

# test
class Test:
    class Test2:
        def fct(self):
            def do_something2(self):
                self.x = 1
                self.x2 = 42
                self.y = 99
# endtest
"""

    mock_results = []
    call_counter = {}
    fct_called = ""

    MockCompletedProcess = typing.NamedTuple("CompletedProcess", [("stdout", str), ("stderr", str)])  # noqa: UP014

    def git_show_mock(self):
        self.call_counter.setdefault(self.fct_called, 0)

        res = self.MockCompletedProcess(stdout=self.mock_results[self.call_counter[self.fct_called]], stderr="")
        self.call_counter[self.fct_called] += 1
        return res

    def test_no_differences(self, monkeypatch):
        self.fct_called = "test_no_differences"
        monkeypatch.setattr(doctrack.checker, "get_git_differences", lambda version1, version2, path: {})

        res = get_doc_tracked_differences(None, None, None, ["# test", "#test"], skip_blank_lines=True)

        assert res == {}

    def test_some_differences(self, monkeypatch):
        """
        going to return 3 differences because they are in a tagged scope
        but not the difference of -13 +12,0 because it's not tagged
        """
        overwrite_git_diff_eq_hash()
        self.fct_called = "test_some_differences"

        self.mock_results = [
            self.diff_content,
            self.file_content_version1,
            self.file_content_version2,
        ]
        monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: self.git_show_mock())

        res = get_doc_tracked_differences(None, None, None, [("# test", "# endtest")], skip_blank_lines=True)

        assert res == {
            "bar.py": {
                GitDifference(from_rm_line=7, to_rm_line=9, from_add_line=-1, to_add_line=-1),
                GitDifference(from_rm_line=-1, to_rm_line=-1, from_add_line=21, to_add_line=22),
            }
        }


class TestGetDifferencesTagged:
    def test_get_differences_tagged_rm(self):
        file_content = """\
# test
def do_something():
    x = 1
    y = 2
# endtest

def remove_me():
    # test
    print("This will be removed")
    # endtest
    print("This will not be removed")

def remove_me():
    # test
    print("This will not be removed")
    # endtest
    print("This will be removed")

# test
class Test:
    class Test2:
        def fct(self):
            def do_something2(self):
                self.x = 1
# endtest
"""
        tags = [("# test", "# endtest")]
        differences = [
            Difference(from_line=16, to_line=16),
            Difference(from_line=2, to_line=3),
            Difference(from_line=7, to_line=9),
            Difference(from_line=-1, to_line=-1),
        ]
        res = get_differences_tagged(file_content, differences, tags)

        assert res == [1, 2]

    def test_get_differences_tagged_add(self):
        file_content = """\
# test
def do_something():
    x = 42
    y = 99
    z = x + y
# endtest

def remove_me():
    print("This will not be removed")

def remove_me():
    # test
    print("This will not be removed")
    # endtest

# test
class Test:
    class Test2:
        def fct(self):
            def do_something2(self):
                self.x = 1
                self.x2 = 42
                self.y = 99
# endtest
"""
        tags = [("# test", "# endtest")]
        differences = [
            Difference(from_line=-1, to_line=-1),
            Difference(from_line=21, to_line=22),
            Difference(from_line=-1, to_line=-1),
            Difference(from_line=2, to_line=4),
        ]
        res = get_differences_tagged(file_content, differences, tags)

        assert res == [3, 1]
