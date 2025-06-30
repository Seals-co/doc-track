from checker import get_doc_tracked_differences
from config import load_config, update_args
from output import get_result_displayed
import sys

def run(args):
    config = load_config(args.config)
    args = update_args(args, config)
    res = get_doc_tracked_differences(
        args.version_from,
        args.version_to,
        args.path,
        args.tags,
        args.skip_blank_lines,
    )

    if args.show_result:
        print(get_result_displayed(res), file=sys.stderr)
    if res != {} and args.fail_status:
        exit(args.fail_status)

