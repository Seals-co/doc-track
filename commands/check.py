from checker import get_doc_tracked_differences


def run(args):
    print(args)
    res = get_doc_tracked_differences("HEAD", None, ".", ["# doctrack", "#doctrack"])
    print(res)
