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

    config_parser = subparsers.add_parser("config", help="Vérifie les modifications")
    config_parser.add_argument("--add-git-message", choices=["yes", "no"], help="Add automatic message to git commit / merge requests")

    check_parser = subparsers.add_parser("check", help="Vérifie les modifications")
    check_parser.add_argument("diff_args", nargs=argparse.REMAINDER, help="Versions Git et path (comme: HEAD~1 HEAD -- path/)")

    check_parser.add_argument("--fail-status", type=int, help="Return code in case code documented if modified")
    check_parser.add_argument("--lang", type=str, help="Target language (ex: python, vue, javascript)")
    check_parser.add_argument("--show-result", type=bool, help="Show output of result in standard output")

    args = parser.parse_args()

    return args

args = cli_args()

fct = COMMANDS[args.command]
fct(args)
