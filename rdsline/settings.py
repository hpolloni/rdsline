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


def _default_client_provider(profile: str, region: str):
    logging.debug("Setting aws credentials profile to %s - region: %s", profile, region)
    session = boto3.Session(profile_name=profile)
    return session.client("rds-data", region_name=region)


def _get_region(cluster_arn: str):
    arn_parts = cluster_arn.split(":")
    return arn_parts[3]


def from_file(file: str, client_provider=_default_client_provider):
    """
    Reads settings from a file.
    """
    logging.debug("Reading configuration file from: %s", file)
    settings = {}
    with open(file, "r", encoding="utf-8") as stream:
        settings = yaml.safe_load(stream)
    logging.debug("Settings: %s", settings)
    if settings["type"] != "rds-secretsmanager":
        raise Exception(f"Unsupported database connection type: {settings['type']}")
    region = _get_region(settings["cluster_arn"])
    profile = settings["credentials"]["profile"]
    client = client_provider(profile, region)
    return RDSSecretsManagerConnection(
        settings["cluster_arn"], settings["secret_arn"], settings["database"], client
    )


def from_args(
    args, client_provider=_default_client_provider, default_config_file=DEFAULT_CONFIG_FILE
):
    """
    Reads settings from cli args.
    """
    if args.config is not None:
        return from_file(args.config, client_provider)
    if os.path.exists(default_config_file):
        return from_file(default_config_file, client_provider)
    logging.debug("No config. Set to null connector")
    return NoopConnection()
