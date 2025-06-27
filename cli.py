import argparse
from commands import (
    check,
    config,
)

COMMANDS = {
    "check": check.run,
    "config": config.run,
}

def cli_args():
    parser = argparse.ArgumentParser(prog="doc-track")

    subparsers = parser.add_subparsers(dest="command", required=True)

    config_parser = subparsers.add_parser("config", help="Configuration")
    config_parser.add_argument("--add-git-message", choices=["yes", "no"], help="Add automatic message to git commit / merge requests")

    check_parser = subparsers.add_parser("check", help="Check changes")
    check_parser.add_argument("version1", nargs="?", default=None, help="Version of comparison")
    check_parser.add_argument("version2", nargs="?", default=None, help="Version to cmopare the first to")
    check_parser.add_argument("splitter", nargs="?", default=None, help="Versions and path splitter, value is '--'")
    check_parser.add_argument("path", nargs="?", help="path")

    check_parser.add_argument("--fail-status", type=int, help="Return code in case code documented if modified")
    check_parser.add_argument("--lang", type=str, help="Target language (ex: python, vue, javascript)")
    check_parser.add_argument("--show-result", type=bool, help="Show output of result in standard output")

    args = parser.parse_args()

    if args.command == "check":
        if args.version1 == "--":
            args.path = args.version2
            args.splitter = "--"
        elif args.version2 == "--":
            args.path = args.splitter
            args.splitter = "--"

    return args

args = cli_args()
fct = COMMANDS[args.command]
fct(args)
