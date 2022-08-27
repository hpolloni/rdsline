"""
The main entry point for rdsline.
"""
import readline  # pylint: disable=unused-import
import os
import sys
from platform import python_version_tuple
from typing import Any, List, Tuple
from rdsline.tabulate import tabulate
from rdsline import settings

if python_version_tuple()[0] < "3":
    raise Exception("We don't support Python < 3")


def to_string(val: Any) -> str:
    """
    Returns a string representation for a database value.
    """
    known_types = {
        "stringValue": lambda v: v["stringValue"],
        "booleanValue": lambda v: str(v["booleanValue"]),
        "doubleValue": lambda v: str(v["doubleValue"]),
        "longValue": lambda v: str(v["longValue"]),
        "blobValue": lambda v: "BLOB",
        "arrayValue": lambda v: "ARRAY",
    }
    if "isNull" in val and val["isNull"]:
        return "NULL"
    for (type_name, converter) in known_types.items():
        if type_name in val:
            return converter(val)
    return "UNKNOWN"


def execute(connection: settings.ConnectionSettings, sql: str) -> Tuple[List[str], List[List[str]]]:
    """
    Executes a query using the passed in connection settings.
    It returns the headers and records as strings.
    """
    response = connection.execute(sql)
    headers = [col["name"] for col in response["columnMetadata"]]
    records = [[to_string(value) for value in row] for row in response["records"]]
    return (headers, records)


def show_help():
    """Shows the help."""
    print(".quit - quits the REPL")
    print(".config <config_file> - sets new connection settings from a file")
    print(".show - displays current connection settings")


def read(prompt: str) -> str:
    """
    Reads from stdin. If an EOF is thrown, it exits the program
    """
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
        line = read(prompt)
        if line == ".help":
            show_help()
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
                print("Connection settings not set. Maybe you need to call .config")
                connection.print()
                buffer = ""
                prompt = ">"
                continue
            try:
                (headers, records) = execute(connection, buffer)
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
