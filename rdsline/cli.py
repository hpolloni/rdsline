"""
The main entry point for rdsline.
"""

import logging
import argparse
import readline  # pylint: disable=unused-import
import os
import sys
from typing import List, Any, Callable, Dict, Union
import yaml

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
            ".profile [name] - show current connection or switch to a different profile",
            ".profiles - list available profiles",
            ".addprofile - add a new profile interactively",
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
    Handles configuration file loading and display.
    """

    def __init__(self):
        """Initialize with empty settings."""
        self.settings = settings.Settings()
        self.config_file = None

    def load_config(self, args: List[str]) -> str:
        """
        Load configuration from a file.

        Args:
        args (List[str]): The arguments to the command.

        Returns:
        str: A message indicating the result of the command.
        """
        if len(args) < 2:
            return "ERROR: Expecting config file"

        config_file = args[1]
        self.config_file = os.path.expanduser(config_file)
        self.settings.load_from_file(self.config_file)
        return f"Loaded configuration from {config_file}"

    def show_config(self, _: List[str]) -> str:
        """
        Show current configuration.

        Args:
        _ (List[str]): Ignored.

        Returns:
        str: A string showing the current configuration.
        """
        return yaml.dump({"profiles": self.settings.profiles})

    def __call__(self, args: List[str]) -> str:
        """
        Handle configuration commands.

        Args:
        args (List[str]): The arguments to the command.

        Returns:
        str: A message indicating the result of the command.
        """
        return self.load_config(args)

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
        if len(args) == 1:
            return str(self.config.connection)

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

    def add_profile(self, _: List[str]) -> str:
        """
        Interactively adds a new profile to the configuration.

        Returns:
        str: A message indicating the result of the command.
        """
        print("\nAdding a new profile. Press Ctrl+C at any time to cancel.\n")

        try:
            # Get and validate profile name
            profile_info = self._get_profile_info()
            if isinstance(profile_info, str):
                return profile_info  # Return error message if validation failed

            # Show summary and confirm
            if not self._show_and_confirm_profile(profile_info):
                return "Profile creation cancelled"

            # Save the profile
            name = profile_info["name"]
            del profile_info["name"]  # Remove name from the profile data
            self.config.settings.profiles[name] = profile_info

            # Save the updated configuration
            with open(self.config.config_file, "w", encoding="utf-8") as f:
                yaml.dump({"profiles": self.config.settings.profiles}, f)

            return f"\nProfile '{name}' added successfully"

        except KeyboardInterrupt:
            print()  # Add a newline after ^C
            return "Profile creation cancelled"

    def _get_profile_info(self) -> Union[Dict[str, Any], str]:
        """
        Get profile information from user input.

        Returns:
        Union[Dict[str, Any], str]: Profile information dictionary if successful,
                                  error message string if validation fails.
        """
        # Validate profile name
        name = input("Profile name: ").strip()
        if not name:
            return "Profile name cannot be empty"
        if name in self.config.settings.profiles:
            return f"Profile '{name}' already exists"

        # Get and validate connection type
        print("\nConnection type (currently only rds-secretsmanager is supported)")
        profile_type = input("Connection type [rds-secretsmanager]: ").strip()
        if not profile_type:
            profile_type = "rds-secretsmanager"
        elif profile_type != "rds-secretsmanager":
            return f"Unsupported database connection type: {profile_type}"

        # Get and validate required fields
        print("\nCluster ARN")
        print("Format: arn:aws:rds:<region>:<account>:cluster:<cluster-name>")
        cluster_arn = input("Cluster ARN: ").strip()

        print("\nSecret ARN")
        print("Format: arn:aws:secretsmanager:<region>:<account>:secret:<secret-name>")
        secret_arn = input("Secret ARN: ").strip()

        print("\nDatabase name")
        database = input("Database: ").strip()

        # Validate required fields
        required_fields = [
            ("Cluster ARN", cluster_arn),
            ("Secret ARN", secret_arn),
            ("Database", database),
        ]
        for field_name, value in required_fields:
            if not value:
                return f"{field_name} cannot be empty"

        # Get optional AWS profile
        print("\nAWS credentials profile (optional)")
        aws_profile = input("AWS Profile [default]: ").strip()
        if not aws_profile:
            aws_profile = "default"

        return {
            "name": name,
            "type": profile_type,
            "cluster_arn": cluster_arn,
            "secret_arn": secret_arn,
            "database": database,
            "credentials": {"profile": aws_profile},
        }

    def _show_and_confirm_profile(self, profile: Dict[str, Any]) -> bool:
        """
        Show profile summary and get user confirmation.

        Args:
        profile: Profile information dictionary.

        Returns:
        bool: True if user confirms, False otherwise.
        """
        print("\nProfile Summary:")
        print(f"  Name: {profile['name']}")
        print(f"  Type: {profile['type']}")
        print(f"  Cluster ARN: {profile['cluster_arn']}")
        print(f"  Secret ARN: {profile['secret_arn']}")
        print(f"  Database: {profile['database']}")
        print(f"  AWS Profile: {profile['credentials']['profile']}")

        confirm = input("\nSave this profile? [y/N]: ").strip().lower()
        return confirm == "y"


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
        ".addprofile": profile_cmd.add_profile,
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
            cmd_args: List[str] = line.split(" ")
            if cmd_args[0] in commands:
                print(commands[cmd_args[0]](cmd_args))
                if cmd_args[0] == ".profile" and sys.stdin.isatty():
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
