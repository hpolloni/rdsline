"""
Settings module for the cli.
"""
import argparse
import yaml
import boto3
from rdsline.connections import NoopConnection
from rdsline.connections.rds_secretsmanager import RDSSecretsManagerConnection


def _get_region(cluster_arn: str):
    arn_parts = cluster_arn.split(":")
    return arn_parts[3]


def _client_provider(profile: str, region: str):
    session = boto3.Session(profile_name=profile)
    return session.client("rds-data", region_name=region)


def from_file(file: str, client_provider=_client_provider):
    """
    Reads settings from a file.
    """
    settings = {}
    with open(file, "r", encoding="utf-8") as stream:
        settings = yaml.safe_load(stream)
    if settings["type"] != "rds-secretsmanager":
        raise Exception(f"Unsupported database connection type: {settings['type']}")
    region = _get_region(settings["cluster_arn"])
    profile = settings["credentials"]["profile"]
    client = client_provider(profile, region)
    return RDSSecretsManagerConnection(
        settings["cluster_arn"], settings["secret_arn"], settings["database"], client
    )


def from_args():
    """
    Reads settings from cli args.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=str, required=False, help="Config file to read settings from"
    )
    args = parser.parse_args()
    if args.config is not None:
        return from_file(args.config)
    return NoopConnection()
