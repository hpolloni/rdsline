"""
Settings module for the cli.
"""

import os
import logging
import yaml
import boto3
from rdsline.connections import NoopConnection
from rdsline.connections.rds_secretsmanager import RDSSecretsManagerConnection

DEFAULT_CONFIG_FILE = os.path.expanduser("~/.rdsline")
DEFAULT_PROFILE = "default"


def create_boto3_session(profile):
    """Creates a boto3 session. Separated for testing."""
    if profile is None:
        return boto3.Session()
    return boto3.Session(profile_name=profile)


def default_client_provider(profile, region):
    """Default provider that creates real AWS clients."""
    logging.debug("Setting aws credentials profile to %s - region: %s", profile, region)
    session = create_boto3_session(profile)
    return session.client("rds-data", region_name=region)


def _get_region(cluster_arn):
    arn_parts = cluster_arn.split(":")
    return arn_parts[3]


def _create_connection_from_profile(profile_config, client_provider):
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

    def __init__(self, client_provider, initial_profile):
        """
        Initialize Settings with a client provider.

        Args:
            client_provider: Function that takes (profile: str, region: str) and returns
                           an AWS client. Defaults to _default_client_provider.
            initial_profile: Initial profile to use. Defaults to DEFAULT_PROFILE.
        """
        self.profiles = {}
        self.current_profile = initial_profile
        self.connection = NoopConnection()
        self._client_provider = client_provider

    def load_from_file(self, file):
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
        if self.current_profile in self.profiles:
            self.switch_profile(self.current_profile)
        elif self.profiles:
            # If specified profile is not available, use the first available profile
            self.switch_profile(next(iter(self.profiles)))

    def switch_profile(self, profile_name):
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

    def get_profile_names(self):
        """Returns list of available profile names."""
        return list(self.profiles.keys())

    def get_current_profile(self):
        """Returns the name of the current profile."""
        return self.current_profile

    def add_profile(self, profile_name, config):
        """
        Adds a new profile to the configuration.

        Args:
            profile_name: Name of the profile to add
            config: Profile configuration dictionary containing:
                   - type: Connection type (e.g., 'rds-secretsmanager')
                   - cluster_arn: ARN of the RDS cluster
                   - secret_arn: ARN of the Secrets Manager secret
                   - database: Database name
                   - credentials: Optional credentials configuration

        Raises:
            Exception: If the profile already exists or if required fields are missing
        """
        if profile_name in self.profiles:
            raise Exception(f"Profile '{profile_name}' already exists")

        required_fields = ["type", "cluster_arn", "secret_arn", "database"]
        missing_fields = [field for field in required_fields if field not in config]
        if missing_fields:
            raise Exception(f"Missing required fields for profile: {', '.join(missing_fields)}")

        if config["type"] != "rds-secretsmanager":
            raise Exception(f"Unsupported database connection type: {config['type']}")

        self.profiles[profile_name] = config

    def save_to_file(self, file=DEFAULT_CONFIG_FILE):
        """
        Saves the current configuration to a file.

        Args:
            file: Path to save the configuration to. Defaults to ~/.rdsline
        """
        config = {"profiles": self.profiles}
        os.makedirs(os.path.dirname(os.path.abspath(file)), exist_ok=True)
        with open(file, "w", encoding="utf-8") as stream:
            yaml.safe_dump(config, stream, default_flow_style=False)
