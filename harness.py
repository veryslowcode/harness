import sys
import signal
import argparse
import subprocess
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


class Style(Enum):
    Bit2 = 0  # Uses 2 bit Ansi style output
    Bit8 = 1  # Uses 8 bit Ansi style output


@dataclass
class Arguments:
    command: list  # Command is required, the rest are optional
    mode: int = Mode.LINE
    style: int = Style.Bit8
    file: str = "harness.conf"


@dataclass
class Configuration:
    keywords: list  # Indexed list of keywords to match
    colors:   list  # Indexed list of colors synchronized with keywords
    baseColor: int  # Indicates the color that non-matched output will be
    hasBase:  bool  # Flag to indicate if a base color was defined


def handled(func):
    ''' Simple error handling
    decorator to exit early '''
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Style the output for easier detection
            print(f"{ERR_PREFIX}{e}{RST_SUFFIX}")
            exit(1)
    return wrapper


def main() -> None:
    arguments = set_arguments()
    configuration = set_configuration(arguments.file)

    # I have found shell is needed to work with Windows
    # but causes problems on unix-like systems
    shell = True if sys.platform == "win32" else False
    process = subprocess.Popen(
            arguments.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=shell)

    def signal_trap(sig, frame) -> None:
        ''' Some processes may hang, this
        is to try and prevent that '''
        process.kill()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_trap)

    # Separate standard output and error output
    # Error output will default to all red
    with process.stdout:
        log_stdout(process.stdout, configuration,
                   arguments.mode, arguments.style)
    with process.stderr:
        log_stderr(process.stderr)

    process.wait()


@handled
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
                        help="Colorization method: 'line' or 'word' " +
                        "(defaults to 'line'")
    parser.add_argument("-s", "--style",
                        help="Color style: '8bit' or '8bit' " +
                        "(defaults to '8bit')")

    parsed_args = parser.parse_args()
    arguments = Arguments(parsed_args.command.split(" "))

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
            error = argparse.ArgumentTypeError("Invalid mode! " +
                                               "'word' or 'line' expected")
            parser.print_help()
            print('\n')
            raise error

    if parsed_args.style is not None:
        style = parsed_args.style.lower()

        if style == "2bit":
            arguments.style = Style.Bit2
        elif style == "8bit":
            arguments.style = Style.Bit8
        else:
            # Raising an exception is better feedback on usage
            # vs. default/silent handling
            error = argparse.ArgumentTypeError("Invalid style! " +
                                               "'2bit' or '8bit' expected")
            parser.print_help()
            print('\n')
            raise error

    return arguments


@handled
def set_configuration(file: str) -> Configuration:
    handle = open(file, "r")  # This may throw but is handled by decorator
    content = handle.readlines()
    configuration = Configuration([], [], 0, False)

    for line in content:
        line = line.strip()

        # Easy enough to handle comments
        # shouldn't be indented though
        if line == "" or line[0] == "#":
            continue

        values = line.split("=")
        if len(values) < 2:
            raise Exception("Configuration must be in the "
                            "following format [KEY]=[COLOR]")

        keyword = values[0].strip()

        try:
            # Though not necessary, if the configuration
            # is invalid, this will produce a helpful
            # indication vs. it just not working/coloring
            color = int(values[1].strip())
        except Exception:
            raise Exception("Color must be an integer")

        if keyword.lower() == "base":
            configuration.hasBase = True
            configuration.baseColor = color
        else:
            configuration.keywords.append(keyword)
            configuration.colors.append(color)

    return configuration


def log_stdout(pipe, configuration: Configuration,
               mode: Mode, style: Style) -> None:
    for line in iter(pipe.readline, ""):
        skip: bool = False  # Flag for continuation

        for index, key in enumerate(configuration.keywords):
            if str(line).__contains__(key):
                color = configuration.colors[index]
                skip = True

                if mode == Mode.LINE:
                    handle_line_mode(line, color, style)
                else:
                    # Key is needed to ensure all
                    # occurrences are colored
                    handle_word_mode(line, key, color, style)

                break

        if skip:  # Cleaner than nested conditionals
            continue

        # Handle the base color case
        if configuration.hasBase:
            print(
                f"{CSI}{configuration.baseColor}m{line}{RST_SUFFIX}",
                end="")
        else:
            print(line, end="")


def handle_line_mode(line: str, color: int, style: Style) -> None:
    prefix = f"{CSI}38;5;" if style == Style.Bit8 else f"{CSI}"
    print(
        f"{prefix}{color}m{line}{RST_SUFFIX}",
        end="")


def handle_word_mode(line: str, key: str, color: int, style: Style) -> None:
    prefix = f"{CSI}38;5;" if style == Style.Bit8 else f"{CSI}"
    print(
        line.replace(key, f"{prefix}{color}m{key}{RST_SUFFIX}"),
        end="")


def log_stderr(pipe) -> None:
    for line in iter(pipe.readline, ""):
        print(f"{ERR_PREFIX}{line}{RST_SUFFIX}", end="")


if __name__ == '__main__':
    main()
