"""
The main entry point for rdsline.
"""

import argparse
import logging
import os
import sys
import yaml

from rdsline import settings
from rdsline.ui import UI
from rdsline.version import VERSION


class HelpCommand:
    """
    Command to display help information.
    """

    def __init__(self, ui):
        self.ui = ui

    def __call__(self, _):
        """
        Displays help information.
        """
        help_text = "\n".join(
            [
                ".quit - quits the REPL",
                ".debug - toggle debugging information",
                ".profile [name] - show current connection or switch to a different profile",
                ".profiles - list available profiles",
                ".addprofile - add a new profile interactively",
            ]
        )
        self.ui.print(help_text)


class DebugCommand:
    """
    Toggles debug logging on/off.
    """

    def __init__(self, is_debug, ui):
        """
        Initializes the DebugCommand.

        Args:
        is_debug: Whether debugging is initially on.
        ui: The UI instance to use for output.
        """
        self.is_debug = is_debug
        self.ui = ui
        logging.basicConfig(level=logging.DEBUG if is_debug else logging.WARN)

    def __call__(self, _):
        """
        Toggles debugging on/off.

        Args:
        _: Ignored.
        """
        self.is_debug = not self.is_debug
        logging.getLogger().setLevel(logging.DEBUG if self.is_debug else logging.WARN)
        self.ui.print("Debugging is " + ("ON" if self.is_debug else "OFF"))


class ProfileCommand:
    """
    Profile management commands.
    """

    def __init__(self, settings_instance, ui):
        """
        Initializes the ProfileCommand.

        Args:
        settings_instance: The Settings instance to use.
        ui: The UI instance to use for output.
        """
        self.settings = settings_instance
        self.ui = ui

    def switch_profile(self, args):
        """
        Switches to a different profile.

        Args:
        args: The arguments to the command.
        """
        if len(args) == 1:
            self.ui.print(str(self.settings.connection))
            return

        if len(args) != 2:
            self.ui.display_error("Expecting profile name")
            return

        profile_name = args[1]
        try:
            self.settings.switch_profile(profile_name)
            self.ui.print(f"Switched to profile: {profile_name}")
        except Exception as ex:
            self.ui.display_error(str(ex))

    def list_profiles(self, _):
        """
        Lists available profiles.

        Args:
        _: Ignored.
        """
        profiles = self.settings.get_profile_names()
        current = self.settings.get_current_profile()

        if not profiles:
            self.ui.print("No profiles configured")
            return

        self.ui.print("Available profiles:")
        for profile in profiles:
            marker = "*" if profile == current else " "
            self.ui.print(f" {marker} {profile}")

    def add_profile(self, _):
        """
        Interactively adds a new profile to the configuration.
        """
        try:
            # Get and validate profile info
            profile_info = self._get_profile_info()
            name = profile_info["name"]

            if name in self.settings.profiles:
                self.ui.display_error(f"Profile '{name}' already exists")
                return

            # Show summary and confirm
            if not self._confirm_profile(profile_info):
                self.ui.print("Profile creation cancelled")
                return

            # Save the profile
            del profile_info["name"]  # Remove name from the profile data
            self.settings.profiles[name] = profile_info

            # Save the updated configuration
            with open(settings.DEFAULT_CONFIG_FILE, "w", encoding="utf-8") as f:
                yaml.dump({"profiles": self.settings.profiles}, f)

            self.ui.print(f"\nProfile '{name}' added successfully")

        except KeyboardInterrupt:
            self.ui.print("")  # Add a newline after ^C
            self.ui.print("Profile creation cancelled")
        except ValueError as ex:
            self.ui.display_error(str(ex))

    def _get_profile_info(self):
        """
        Interactively get profile information from the user.

        Returns:
            Profile information dictionary

        Raises:
            ValueError: If any required field is empty or invalid
        """
        self.ui.print("\nAdding a new profile. Press Ctrl+C at any time to cancel.\n")

        # Get profile details
        name = self.ui.read_input("Profile name: ").strip()
        if not name:
            raise ValueError("Profile name cannot be empty")

        self.ui.print("\nConnection type (currently only rds-secretsmanager is supported)")
        profile_type = self.ui.read_input("Connection type [rds-secretsmanager]: ").strip()
        if not profile_type:
            profile_type = "rds-secretsmanager"
        elif profile_type != "rds-secretsmanager":
            raise ValueError(f"Unsupported database connection type: {profile_type}")

        self.ui.print("\nCluster ARN")
        self.ui.print("Format: arn:aws:rds:<region>:<account>:cluster:<cluster-name>")
        cluster_arn = self.ui.read_input("Cluster ARN: ").strip()

        self.ui.print("\nSecret ARN")
        self.ui.print("Format: arn:aws:secretsmanager:<region>:<account>:secret:<secret-name>")
        secret_arn = self.ui.read_input("Secret ARN: ").strip()

        self.ui.print("\nDatabase name")
        database = self.ui.read_input("Database: ").strip()

        # Validate required fields
        required_fields = [
            ("Cluster ARN", cluster_arn),
            ("Secret ARN", secret_arn),
            ("Database", database),
        ]
        for field_name, value in required_fields:
            if not value:
                raise ValueError(f"{field_name} cannot be empty")

        self.ui.print("\nAWS credentials profile (optional)")
        aws_profile = self.ui.read_input("AWS Profile [default]: ").strip()
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

    def _confirm_profile(self, profile):
        """
        Show profile summary and get user confirmation.

        Args:
            profile: Profile information dictionary

        Returns:
            bool: True if user confirms, False otherwise
        """
        self.ui.print("\nProfile Summary:")
        self.ui.print(f"  Name: {profile['name']}")
        self.ui.print(f"  Type: {profile['type']}")
        self.ui.print(f"  Cluster ARN: {profile['cluster_arn']}")
        self.ui.print(f"  Secret ARN: {profile['secret_arn']}")
        self.ui.print(f"  Database: {profile['database']}")
        self.ui.print(f"  AWS Profile: {profile['credentials']['profile']}")

        confirm = self.ui.read_input("\nSave this profile? [y/N]: ").strip().lower()
        return confirm == "y"


def _parse_args():
    """
    Parses command line arguments.

    Returns:
        The parsed arguments.
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


def _handle_sql_command(line, buffer, ui, settings_instance):
    """Handle SQL command input.

    Args:
        line: The input line
        buffer: The current SQL buffer
        ui: The UI instance
        settings_instance: The settings instance

    Returns:
        tuple: Updated buffer and prompt
    """
    if line.endswith(";") or line == "":
        buffer += line
        try:
            result = settings_instance.connection.execute(buffer)
            ui.print(str(result))
        except Exception as ex:  # pylint: disable=broad-except
            ui.display_error(str(ex))
        finally:
            buffer = ""
            prompt = f"{settings_instance.get_current_profile()}> "
    else:
        buffer += line + " "
        prompt = "|"
    return buffer, prompt


def main():
    """
    The main entry point for the program.
    """
    args = _parse_args()
    ui = UI(is_interactive=sys.stdin.isatty())
    settings_instance = settings.Settings(initial_profile=args.profile)

    # Initialize with config file
    if args.config:
        settings_instance.load_from_file(args.config)
    elif os.path.exists(settings.DEFAULT_CONFIG_FILE):
        settings_instance.load_from_file(settings.DEFAULT_CONFIG_FILE)

    profile_cmd = ProfileCommand(settings_instance, ui)
    commands = {
        ".help": HelpCommand(ui),
        ".debug": DebugCommand(args.debug, ui),
        ".profile": profile_cmd.switch_profile,
        ".profiles": profile_cmd.list_profiles,
        ".addprofile": profile_cmd.add_profile,
    }

    buffer = ""
    prompt = f"{settings_instance.get_current_profile()}> "

    while True:
        try:
            line = ui.get_command_input(prompt)
            if not line:
                continue

            if line[0] == ".":
                cmd_args = line.split(" ")
                if cmd_args[0] in commands:
                    commands[cmd_args[0]](cmd_args)
                    if cmd_args[0] == ".profile" and ui.is_interactive:
                        prompt = f"{settings_instance.get_current_profile()}> "
            else:
                buffer, prompt = _handle_sql_command(line, buffer, ui, settings_instance)
        except EOFError:
            sys.exit(0)
        except KeyboardInterrupt:
            ui.print("")
            sys.exit(0)


if __name__ == "__main__":
    main()
