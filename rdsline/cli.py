"""
The main entry point for rdsline.
"""

import logging
import argparse
import readline  # pylint: disable=unused-import
import os
import sys
from typing import List, Optional, Any, Callable, Dict

from rdsline import settings
from rdsline.version import VERSION
from rdsline.connections import Connection


def _help() -> str:
    """
    Returns a string containing help information.
    """
    return "\n".join(
        [
            ".quit - quits the REPL",
            ".config <config_file> - sets new connection settings from a file",
            ".show - displays current connection settings",
            ".debug - toggle debugging information",
            ".profile <name> - switch to a different profile",
            ".profiles - list available profiles",
        ]
    )


def _read(prompt: str) -> str:
    """
    Reads a line from the user.

    Args:
    prompt (str): The prompt to display to the user.

    Returns:
    str: The line read from the user.
    """
    try:
        line = input(f"{prompt}")
        if line == ".quit":
            sys.exit(0)
        return line
    except EOFError:
        sys.exit(0)


def _parse_args() -> argparse.Namespace:
    """
    Parses command line arguments.

    Returns:
    argparse.Namespace: The parsed arguments.
    """
    parser = argparse.ArgumentParser(description="The RDS REPL v" + VERSION)
    parser.add_argument(
        "--config", type=str, required=False, help="Config file to read settings from"
    )
    parser.add_argument("--profile", type=str, required=False, help="Initial profile to use")
    parser.add_argument(
        "--debug", required=False, action="store_true", help="Turn debugging information on."
    )
    return parser.parse_args()


class DebugCommand:
    """
    Toggles debug logging on/off.
    """

    def __init__(self, is_debug: bool):
        """
        Initializes the DebugCommand.

        Args:
        is_debug (bool): Whether debugging is initially on.
        """
        self.is_debug = is_debug
        logging.basicConfig(level=logging.DEBUG if is_debug else logging.WARN)

    def __call__(self, _: Any) -> str:
        """
        Toggles debugging on/off.

        Args:
        _ (Any): Ignored.

        Returns:
        str: A message indicating whether debugging is on or off.
        """
        self.is_debug = not self.is_debug
        logging.getLogger().setLevel(logging.DEBUG if self.is_debug else logging.WARN)
        return "Debugging is " + ("ON" if self.is_debug else "OFF")


class ConfigCommand:
    """
    Config command.
    """

    def __init__(self):
        """
        Initializes the ConfigCommand.
        """
        self.settings = settings.Settings()

    def __call__(self, args: List[str]) -> str:
        """
        Handles the config command.

        Args:
        args (List[str]): The arguments to the command.

        Returns:
        str: A message indicating the result of the command.
        """
        if len(args) != 2:
            return "ERROR: Expecting config file"
        (_, config_file) = args
        self.settings.load_from_file(os.path.expanduser(config_file))
        return str(self.settings.connection)

    @property
    def connection(self) -> Connection:
        """
        Gets the current connection.

        Returns:
        Connection: The current connection.
        """
        return self.settings.connection


class ProfileCommand:
    """
    Profile management commands.
    """

    def __init__(self, config: ConfigCommand):
        """
        Initializes the ProfileCommand.

        Args:
        config (ConfigCommand): The ConfigCommand to use.
        """
        self.config = config

    def switch_profile(self, args: List[str]) -> str:
        """
        Switches to a different profile.

        Args:
        args (List[str]): The arguments to the command.

        Returns:
        str: A message indicating the result of the command.
        """
        if len(args) != 2:
            return "ERROR: Expecting profile name"
        profile_name = args[1]
        try:
            self.config.settings.switch_profile(profile_name)
            return f"Switched to profile: {profile_name}"
        except Exception as ex:
            return f"ERROR: {str(ex)}"

    def list_profiles(self, _: List[str]) -> str:
        """
        Lists available profiles.

        Args:
        _ (List[str]): Ignored.

        Returns:
        str: A string listing the available profiles.
        """
        profiles = self.config.settings.get_profile_names()
        current = self.config.settings.get_current_profile()

        if not profiles:
            return "No profiles configured"

        result = ["Available profiles:"]
        for profile in profiles:
            marker = "*" if profile == current else " "
            result.append(f" {marker} {profile}")
        return "\n".join(result)


def main() -> None:
    """
    The main entry point for the program.
    """
    args = _parse_args()
    config = ConfigCommand()

    # Initialize with config file
    if args.config:
        config(["config", args.config])
    elif os.path.exists(settings.DEFAULT_CONFIG_FILE):
        config(["config", settings.DEFAULT_CONFIG_FILE])

    # Switch to initial profile if specified
    if args.profile:
        config.settings.switch_profile(args.profile)

    profile_cmd = ProfileCommand(config)
    commands: Dict[str, Callable[[List[str]], str]] = {
        ".help": lambda _: _help(),
        ".show": lambda _: str(config.connection),
        ".debug": DebugCommand(args.debug),
        ".config": config,
        ".profile": profile_cmd.switch_profile,
        ".profiles": profile_cmd.list_profiles,
    }

    buffer = ""
    default_prompt = ""
    if sys.stdin.isatty():
        default_prompt = f"{config.settings.get_current_profile()}> "
        print("The RDS REPL v" + VERSION)
        print("Type .help for help")
    prompt = default_prompt

    while True:
        line = _read(prompt)
        if line and line[0] == ".":
            args = line.split(" ")
            if args[0] in commands:
                print(commands[args[0]](args))
                if args[0] == ".profile" and sys.stdin.isatty():
                    default_prompt = f"{config.settings.get_current_profile()}> "
                    prompt = default_prompt
        elif line.endswith(";") or line == "":
            buffer += line
            try:
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
