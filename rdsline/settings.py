"""
Settings module for the cli.
"""

import os
import logging
from typing import Dict, Callable, Any, List
import yaml
import boto3
from rdsline.connections import NoopConnection, Connection
from rdsline.connections.rds_secretsmanager import RDSSecretsManagerConnection

DEFAULT_CONFIG_FILE = os.path.expanduser("~/.rdsline")
DEFAULT_PROFILE = "default"


def create_boto3_session(profile: str) -> Any:
    """Creates a boto3 session. Separated for testing."""
    return boto3.Session(profile_name=profile)


def _default_client_provider(profile: str, region: str) -> Any:
    """Default provider that creates real AWS clients."""
    logging.debug("Setting aws credentials profile to %s - region: %s", profile, region)
    session = create_boto3_session(profile)
    return session.client("rds-data", region_name=region)


def _get_region(cluster_arn: str) -> str:
    arn_parts = cluster_arn.split(":")
    return arn_parts[3]


def _create_connection_from_profile(profile_config: Dict, client_provider: Callable) -> Connection:
    """Creates a connection from a profile configuration."""
    if profile_config.get("type") != "rds-secretsmanager":
        raise Exception(f"Unsupported database connection type: {profile_config.get('type')}")

    region = _get_region(profile_config["cluster_arn"])
    aws_profile = profile_config.get("credentials", {}).get("profile", "default")
    client = client_provider(aws_profile, region)

    return RDSSecretsManagerConnection(
        profile_config["cluster_arn"],
        profile_config["secret_arn"],
        profile_config["database"],
        client,
    )


class Settings:
    """Manages multiple connection profiles."""

    def __init__(self, client_provider: Callable = _default_client_provider):
        """
        Initialize Settings with a client provider.

        Args:
            client_provider: Function that takes (profile: str, region: str) and returns
                           an AWS client. Defaults to _default_client_provider.
        """
        self.profiles: Dict[str, Dict] = {}
        self.current_profile: str = DEFAULT_PROFILE
        self.connection: Connection = NoopConnection()
        self._client_provider = client_provider

    def load_from_file(self, file: str) -> None:
        """
        Loads settings from a file.

        Args:
            file: Path to the configuration file to load.
        """
        logging.debug("Reading configuration file from: %s", file)
        with open(file, "r", encoding="utf-8") as stream:
            config = yaml.safe_load(stream)

        # Handle both old format (single profile) and new format (multiple profiles)
        if "profiles" in config:
            self.profiles = config["profiles"]
        else:
            # Convert old format to new format
            self.profiles = {DEFAULT_PROFILE: config}
        
        # Set up initial connection
        self.switch_profile(DEFAULT_PROFILE)

    def switch_profile(self, profile_name: str) -> None:
        """
        Switches to a different profile.

        Args:
            profile_name: Name of the profile to switch to.

        Raises:
            Exception: If the profile does not exist.
        """
        if profile_name not in self.profiles:
            raise Exception(f"Profile '{profile_name}' not found in config")

        self.current_profile = profile_name
        self.connection = _create_connection_from_profile(
            self.profiles[profile_name], self._client_provider
        )

    def get_profile_names(self) -> List[str]:
        """Returns list of available profile names."""
        return list(self.profiles.keys())

    def get_current_profile(self) -> str:
        """Returns the name of the current profile."""
        return self.current_profile


def from_file(file: str, client_provider=_default_client_provider) -> Connection:
    """
    Reads settings from a file and returns the default connection.
    Maintained for backward compatibility.
    """
    settings = Settings(client_provider)
    settings.load_from_file(file)
    return settings.connection


def from_args(
    args, client_provider=_default_client_provider, default_config_file=DEFAULT_CONFIG_FILE
) -> Connection:
    """
    Reads settings from cli args.
    Maintained for backward compatibility.
    """
    if args.config is not None:
        return from_file(args.config, client_provider)
    if os.path.exists(default_config_file):
        return from_file(default_config_file, client_provider)
    logging.debug("No config. Set to null connector")
    return NoopConnection()
