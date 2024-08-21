import sys
import argparse
# import subprocess
from enum import Enum
from dataclasses import dataclass

# Trim stacktrace
sys.tracebacklimit = 0

ESC = "\x1b"     # Escape sequence
CSI = f"{ESC}["  # Control sequence indicator

ERR_PREFIX = f"{CSI}31m"  # Error prefix, red
RST_SUFFIX = f"{CSI}0m"   # Reset suffix


class Mode(Enum):
    LINE = 0  # Matching word will color the whole line
    WORD = 1  # Matching words will be colored separately


@dataclass
class Arguments:
    command: str  # Command is required, the rest are optional
    mode: int = Mode.LINE
    file: str = "harness.conf"


def main() -> None:
    try:
        arguments = set_arguments()
    except argparse.ArgumentError:
        exit(1)

    print(arguments)


def set_arguments() -> Arguments:
    description = "Capture and colorize log output"
    parser = argparse.ArgumentParser(description=description)

    # Required arguments
    parser.add_argument("command",
                        help="Command to spawn harnessed application")

    # Optional arguments
    parser.add_argument("-f", "--file",
                        help="Configuration file (defaults to 'harness.conf')")
    parser.add_argument("-m", "--mode",
                        help="Colorization method ('line' or 'word')")

    parsed_args = parser.parse_args()
    arguments = Arguments(parsed_args.command)

    if parsed_args.file is not None:
        # This will be checked when
        # attempting to parse the file
        arguments.file = parsed_args.file

    if parsed_args.mode is not None:
        mode = parsed_args.mode.lower()

        if mode == "word":
            arguments.mode = Mode.WORD
        elif mode == "line":
            arguments.mode = Mode.LINE
        else:
            # Raising an exception is better feedback on usage
            # vs. default/silent handling
            error = argparse.ArgumentTypeError(
                    f"{ERR_PREFIX}Invalid mode! "
                    + f"'word' or 'line' expected{RST_SUFFIX}")
            parser.print_help()
            print('\n')
            raise error

    return arguments


if __name__ == '__main__':
    main()

