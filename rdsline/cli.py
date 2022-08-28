"""
The main entry point for rdsline.
"""
import logging
import argparse
import readline  # pylint: disable=unused-import
import os
import sys
from platform import python_version_tuple
from rdsline import settings


if python_version_tuple() < ("3", "7", "8"):
    raise Exception("We don't support Python < 3.7.8")


def _show_help():
    print(".quit - quits the REPL")
    print(".config <config_file> - sets new connection settings from a file")
    print(".show - displays current connection settings")
    print(".debug - toggle debugging information")


def _read(prompt: str) -> str:
    try:
        return input(f"{prompt} ")
    except EOFError:
        sys.exit(0)


def main():
    """
    The main entry point for the program.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=str, required=False, help="Config file to read settings from"
    )
    parser.add_argument(
        "--debug", required=False, action="store_true", help="Turn debugging information on."
    )
    args = parser.parse_args()
    debug = args.debug
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARN)
    connection = settings.from_args(args)
    done = False
    buffer = ""
    prompt = ">"
    print("Type .help for help")
    while not done:
        line = _read(prompt)
        if line[0] == ".":
            args = line.split(" ")
            if args[0] == ".help":
                _show_help()
            elif args[0] == ".quit":
                done = True
            elif args[0] == ".show":
                connection.print()
            elif args[0] == ".debug":
                if debug:
                    print("Debugging turned OFF")
                    logging.getLogger().setLevel(logging.WARN)
                    debug = False
                else:
                    print("Debugging turned ON")
                    logging.getLogger().setLevel(logging.DEBUG)
                    debug = True
            elif args[0] == ".config":
                if len(args) != 2:
                    print("ERROR: Expecting config file")
                else:
                    (_, config_file) = line.split(" ")
                    connection = settings.from_file(os.path.expanduser(config_file))
                    connection.print()
        elif line.endswith(";") or line == "":
            buffer += line
            if not connection.is_executable():
                connection.print()
                buffer = ""
                prompt = ">"
                continue
            try:
                connection.execute(buffer).print()
            except Exception as ex:  # pylint: disable=broad-except
                print(f"Error: {str(ex)}")
            finally:
                buffer = ""
                prompt = ">"
        else:
            buffer += line + " "
            prompt = "|"


if __name__ == "__main__":
    main()
