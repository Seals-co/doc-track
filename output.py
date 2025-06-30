from checker import GitDifference

RESET = "\033[0m"
RED = "\033[91m"
GREEN = "\033[92m"
CYAN = "\033[96m"

def get_result_displayed(differences: dict[str, set[GitDifference]]):
    res = ""
    res += "Differences affected by documentations :\n\n"
    for key, value in differences.items():
        res += f"+++ b/{key}\n"
        value = sorted(value, key=lambda d: d.from_rm_line if d.from_rm_line != -1 else d.from_add_line)
        for diff in value:
            res += f"{CYAN}@@ -{diff.rm_start},{diff.rm_len} +{diff.add_start},{diff.add_len} @@{RESET}\n"
            for line in diff.text.splitlines():
                if line.startswith("-"):
                    res += f"{RED}{line}{RESET}\n"
                elif line.startswith("+"):
                    res += f"{GREEN}{line}{RESET}\n"
                else:
                    res += f"{line}\n"
            print()

    return res
