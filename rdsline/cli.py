"""
The main entry point for rdsline.
"""
import readline  # pylint: disable=unused-import
import os
import sys
from platform import python_version_tuple
from rdsline.tabulate import tabulate
from rdsline import settings

if python_version_tuple() < ("3", "7", "8"):
    raise Exception("We don't support Python < 3.7.8")


def _show_help():
    print(".quit - quits the REPL")
    print(".config <config_file> - sets new connection settings from a file")
    print(".show - displays current connection settings")


def _read(prompt: str) -> str:
    try:
        return input(f"{prompt} ")
    except EOFError:
        sys.exit(0)


def main():
    """
    The main entry point for the program.
    """
    connection = settings.from_args()
    done = False
    buffer = ""
    prompt = ">"
    print("Type .help for help")
    while not done:
        line = _read(prompt)
        if line == ".help":
            _show_help()
        elif line == ".quit":
            done = True
        elif line.startswith(".config"):
            (_, config_file) = line.split(" ")
            connection = settings.from_file(os.path.expanduser(config_file))
            connection.print()
        elif line.startswith(".show"):
            connection.print()
        elif line.endswith(";") or line == "":
            buffer += line
            if not connection.is_executable():
                connection.print()
                buffer = ""
                prompt = ">"
                continue
            try:
                (headers, records) = connection.execute(buffer)
                print(tabulate(records, headers=headers, tablefmt="psql"))
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
