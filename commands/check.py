from checker import get_doc_tracked_differences

def run(args):
    res = get_doc_tracked_differences(args.version_from, args.version_to, args.path, ["# doctrack", "#doctrack"])
    print(res)
