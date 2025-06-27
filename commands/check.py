from checker import get_doc_tracked_differences


def run(args):
    res = get_doc_tracked_differences(args.version1, args.version2, args.path, ["# doctrack", "#doctrack"])
    print(res)
