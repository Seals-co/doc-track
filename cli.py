import argparse
from commands import (
    check,
    config,
)

COMMANDS = {
    "check": check.run,
    "config": config.run,
}

# doctrack
def cli_args():
    parser = argparse.ArgumentParser(prog="doc-track")

    subparsers = parser.add_subparsers(dest="command", required=True)

    config_parser = subparsers.add_parser("config", help="Configuration")
    config_parser.add_argument("--add-git-message", choices=["yes", "no"], help="Add automatic message to git commit / merge requests")

    check_parser = subparsers.add_parser("check", help="Check changes")
    check_parser.add_argument("--version-from", type=str, help="Version of comparison")
    check_parser.add_argument("--version-to", type=str, help="Version to compare the first to")
    check_parser.add_argument("--path", type=str, help="path where comparison is checked")

    check_parser.add_argument("--fail-status", type=int, help="Return code in case code documented if modified")
    check_parser.add_argument("--lang", type=str, help="Target language (ex: python, vue, javascript)")
    check_parser.add_argument("--show-result", type=bool, help="Show output of result in standard output")

    args = parser.parse_args()

    return args

args = cli_args()
fct = COMMANDS[args.command]
fct(args)
