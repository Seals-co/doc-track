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

    check_parser = subparsers.add_parser("check", help="Check changes")
    check_parser.add_argument("--version-from", type=str, help="Version of comparison")
    check_parser.add_argument("--version-to", type=str, help="Version to compare the first to")
    check_parser.add_argument("--path", type=str, help="path where comparison is checked")

    check_parser.add_argument("--config", help="Path to config file", default=".doctrack.yml")
    check_parser.add_argument("--fail-status", type=int, help="Return code in case code documented if modified")
    check_parser.add_argument("--show-result", type=bool, help="Show output of result in standard output")
    check_parser.add_argument("--skip-blank-lines", type=bool, help="Skip blank lines changes", default=True)

    args = parser.parse_args()

    return args

args = cli_args()
fct = COMMANDS[args.command]
fct(args)
