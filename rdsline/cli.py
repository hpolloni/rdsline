"""
The main entry point for rdsline.
"""
import logging
import argparse
import readline
import atexit
import os
import sys
from typing import List
from rdsline import settings
from rdsline.version import VERSION
from rdsline.connections import Connection


HISTORY_FILENAME = os.path.expanduser("~/.rdsline_history")


def _load_history():
    if os.path.exists(HISTORY_FILENAME):
        readline.read_history_file(HISTORY_FILENAME)


def _save_history():
    readline.write_history_file(HISTORY_FILENAME)


atexit.register(_save_history)


def _help():
    return "\n".join(
        [
            ".help - shows this help",
            ".quit - quits the REPL",
            ".config <config_file> - sets new connection settings from a file",
            ".show - displays current connection settings",
            ".debug - toggle debugging information",
        ]
    )


def _read(prompt: str) -> str:
    try:
        line = input(f"{prompt}")
        if line == ".quit":
            sys.exit(0)
        return line
    except EOFError:
        sys.exit(0)
    except KeyboardInterrupt:
        return ""


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="The RDS REPL v" + VERSION)
    parser.add_argument(
        "--config", type=str, required=False, help="Config file to read settings from"
    )
    parser.add_argument(
        "--debug", required=False, action="store_true", help="Turn debugging information on."
    )
    return parser.parse_args()


class DebugCommand:
    """
    Toggles debug logging on/off.
    """

    def __init__(self, is_debug: bool):
        self.is_debug = is_debug
        logging.basicConfig(level=logging.DEBUG if is_debug else logging.WARN)

    def __call__(self, _):
        self.is_debug = not self.is_debug
        logging.getLogger().setLevel(logging.DEBUG if self.is_debug else logging.WARN)
        return "Debugging is " + ("ON" if self.is_debug else "OFF")


class ConfigCommand:
    """
    Config command.
    """

    def __init__(self, connection: Connection):
        self.connection = connection

    def __call__(self, args: List[str]) -> str:
        if len(args) != 2:
            return "ERROR: Expecting config file"
        (_, config_file) = args
        self.connection = settings.from_file(os.path.expanduser(config_file))
        return str(self.connection)


def main():
    """
    The main entry point for the program.
    """
    args = _parse_args()
    config = ConfigCommand(settings.from_args(args))
    commands = {
        ".help": lambda _: _help(),
        ".show": lambda _: str(config.connection),
        ".debug": DebugCommand(args.debug),
        ".config": config,
    }
    buffer = ""
    default_prompt = ""
    if sys.stdin.isatty():
        default_prompt = "> "
        print("The RDS REPL v" + VERSION)
        print("Type .help for help")
    _load_history()
    prompt = default_prompt
    while True:
        line = _read(prompt)
        if line and line[0] == ".":
            args = line.split(" ")
            if args[0] in commands:
                print(commands[args[0]](args))
        elif line.endswith(";") or line == "":
            buffer += line
            try:
                if buffer:
                    print(config.connection.execute(buffer))
            except Exception as ex:  # pylint: disable=broad-except
                print(f"Error: {str(ex)}")
            finally:
                buffer = ""
                prompt = default_prompt
        else:
            buffer += line + " "
            prompt = "|"


if __name__ == "__main__":
    main()
