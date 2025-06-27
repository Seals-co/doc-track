from checker import GitDifference, get_file_content

def get_result_displayed(version1: str, version2: str, differences: dict[str, set[GitDifference]]):
    for filename, differences in differences:
        # If difference
        file_content = get_file_content(version1, filename)

    # Output looks like that:
    # Doctracked differences:
    # - Filename: From line .. to line .. with block doctracked
    # - Filename: From line .. to line .. with block doctracked from line .. to line ..