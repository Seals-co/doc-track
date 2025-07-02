import re
import subprocess
import sys
from dataclasses import dataclass


@dataclass(eq=True, unsafe_hash=True)
class GitDifference:
    from_rm_line: int = -1
    to_rm_line: int = -1
    from_add_line: int = -1
    to_add_line: int = -1

    text: str = ""


@dataclass(frozen=True)
class Difference:
    from_line: int = -1
    to_line: int = -1


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
                difference.text += line + "\n"
                differences[current_file].append(difference)
        elif len(differences.get(current_file, [])):
            differences[current_file][-1].text += line + "\n"
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

    result = subprocess.run(['git', 'diff', '--unified=0', *args], capture_output=True, text=True)  # noqa S603 Input variables are safe
    output = result.stdout
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="") # noqa T201 print authorized
        exit(result.returncode)
    return parse_differences(output)


def get_differences_tagged(
    content: str,
    differences: list[Difference],
    tags: list[tuple[str]],
    skip_blank_lines: bool = True,
) -> list[int]:
    differences_sort = sorted(differences, key=lambda d: d.from_line)
    diff_ind = 0
    while Difference(from_line=-1, to_line=-1) in differences_sort:
        differences_sort.pop(0)

    if not len(differences_sort):
        return []

    if not tags:
        return []

    tag_stack = []
    open_tags = [tag[0] for tag in tags]
    close_tags = [tag[1] for tag in tags]

    res = []
    lines = content.splitlines()
    i = 0
    while i <= differences_sort[-1].to_line and i < len(lines):
        line = lines[i].strip()
        if line in open_tags:
            tag_stack.append(line)

        while (
            diff_ind < len(differences_sort)
            and differences_sort[diff_ind].from_line <= i <= differences_sort[diff_ind].to_line
            and len(tag_stack)
            and (line != "" or not skip_blank_lines)
        ):
            res.append(differences.index(differences_sort[diff_ind]))
            diff_ind += 1

        while (
            diff_ind < len(differences_sort)
            and differences_sort[diff_ind].to_line < i
        ):
            diff_ind += 1

        if line in close_tags and len(tag_stack) and open_tags.index(tag_stack[-1]) == close_tags.index(line):
            tag_stack.pop()

        i += 1

    return res


def get_file_content(version: str | None, path: str):
    result = ""

    if version:
        show_result = subprocess.run( # noqa S603 Input variables are safe
            ["/usr/bin/git", "show", f"{version}:{path}"],
            capture_output=True,
            check=True,
            text=True
        )

        result = show_result.stdout
        if show_result.stderr:
            print(show_result.stderr, file=sys.stderr, end="") # noqa T201 print authorized
            exit(show_result.returncode)
    else:
        cat_result = subprocess.run( # noqa S603 Input variables are safe
            ["/usr/bin/cat", f"{path}"],
            capture_output=True,
            check=True,
            text=True
        )

        result = cat_result.stdout
        if cat_result.stderr:
            print(cat_result.stderr, file=sys.stderr, end="") # noqa T201 print authorized
            exit(cat_result.returncode)

    return result


def get_doc_tracked_differences(
    version_from: str | None,
    version_to: str | None,
    path: str | None,
    tags: list[tuple[str]],
    skip_blank_lines: bool,
) -> dict[str, set[GitDifference]]:
    version1 = version_from or "HEAD"
    version2 = version_to

    result = {}
    git_differences = get_git_differences(version1, version2, path)
    # Retrieve if one of the line contained in git_differences ends with doc-tag
    # or is precedeed by a line that contains doc-tag

    version1 = version1 or ""
    version2 = version2 or ""
    for file_path, git_diffs in git_differences.items():
        content_version_1 = get_file_content(version1, file_path)
        content_version_2 = get_file_content(version2, file_path)

        rm_differences = [Difference(from_line=git_difference.from_rm_line, to_line=git_difference.to_rm_line)
                            for git_difference in git_diffs]
        add_differences = [Difference(from_line=git_difference.from_add_line, to_line=git_difference.to_add_line)
                            for git_difference in git_diffs]

        rm_differences_ind = get_differences_tagged(content_version_1, rm_differences, tags, skip_blank_lines)
        add_differences_ind = get_differences_tagged(content_version_2, add_differences, tags, skip_blank_lines)

        all_differences_ind = {*add_differences_ind, *rm_differences_ind}

        if len(all_differences_ind):
            result[file_path] = {git_diffs[i] for i in all_differences_ind}

    return result
