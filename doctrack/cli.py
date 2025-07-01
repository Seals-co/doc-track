import argparse

from doctrack.commands import (
    check,
)

COMMANDS = {
    "check": check.run,
}


def parse_tags(tags_str: str):
    parts = tags_str.split(',')
    if len(parts) != 2:
        raise argparse.ArgumentTypeError(f"Each element must be a pair 'a,b'. Bad format : {tags_str}")
    return tuple(parts)


def str_to_bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    if v.lower() in ("no", "false", "f", "n", "0"):
        return False
    raise argparse.ArgumentTypeError("Boolean value expected (true/false)")


def cli_args():
    parser = argparse.ArgumentParser(prog="doc-track")

    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="Check changes")
    check_parser.add_argument("--version-from", type=str, help="Version of comparison", default="HEAD")
    check_parser.add_argument("--version-to", type=str, help="Version to compare the first to")
    check_parser.add_argument("--path", type=str, help="path where comparison is checked")
    check_parser.add_argument('--tags', type=parse_tags, nargs='+', help='Pair list of start / end tag')

    check_parser.add_argument("--config", help="Path to config file", default=".doctrack.yml")
    check_parser.add_argument("--fail-status", type=int, help="Return code in case code documented is modified")
    check_parser.add_argument("--show-result", type=str_to_bool, help="Show output of in error output", default=True)
    check_parser.add_argument("--skip-blank-lines", type=str_to_bool, help="Skip blank lines changes", default=True)

    return parser.parse_args()


def main():
    args = cli_args()
    fct = COMMANDS[args.command]
    fct(args)


if __name__ == "__main__":
    main()
