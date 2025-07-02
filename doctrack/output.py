from doctrack.checker import GitDifference

RESET = "\033[0m"
RED = "\033[91m"
GREEN = "\033[92m"
CYAN = "\033[96m"


def get_result_displayed(differences: dict[str, set[GitDifference]]):
    if not differences:
        return "No differences affected by documentation found !"

    res = "Differences affected by documentations :\n"
    for file_path, diffs in differences.items():
        res += "\n"
        res += f"--- a/{file_path}\n"
        res += f"+++ b/{file_path}\n"
        diffs = sorted(diffs, key=lambda d: d.from_rm_line if d.from_rm_line != -1 else d.from_add_line)
        for diff in diffs:
            for line in diff.text.splitlines():
                if line.startswith("@@"):
                    splitted = line.split("@@")
                    res += f"{CYAN}@@{splitted[1]}@@{RESET}{splitted[2]}\n"
                elif line.startswith("-"):
                    res += f"{RED}{line}{RESET}\n"
                elif line.startswith("+"):
                    res += f"{GREEN}{line}{RESET}\n"
                else:
                    res += f"{line}\n"
    return res
