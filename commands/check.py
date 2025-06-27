from checker import get_doc_tracked_differences


def run(args):
    res = get_doc_tracked_differences("HEAD", None, ".", ["# doctrack", "#doctrack"])
    print(res)
