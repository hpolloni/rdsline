"""
Settings module for the cli.
"""
from abc import ABC, abstractmethod
import argparse
from typing import Any
import yaml
import boto3


class ConnectionSettings(ABC):
    """
    Connection settings for a database.
    """

    @abstractmethod
    def execute(self, sql: str) -> Any:
        """
        Executes a query using this connection settings.
        """

    @abstractmethod
    def is_executable(self) -> bool:
        """
        Returns if this connection settings is executable (i.e. all settings are correctly set)
        """

    @abstractmethod
    def print(self):
        """
        Print these settings. Intended for use in the CLI.
        """


class NoopConnectionSettings(ConnectionSettings):
    """
    No op connection settings.
    """

    def __init__(self):
        pass

    def is_executable(self) -> bool:
        return False

    def print(self):
        print("No connection settings. Maybe you need to run .config")

    def execute(self, sql: str) -> Any:
        raise NotImplementedError("Execute in No op")


class RDSSecretsManagerSettings(ConnectionSettings):
    """
    Connection settings for RDS with secretsmanager.
    """

    def __init__(self, cluster_arn: str, secret_arn: str, database: str, client):
        self.cluster_arn = cluster_arn
        self.secret_arn = secret_arn
        self.database = database
        self.client = client

    def execute(self, sql: str) -> Any:
        response = self.client.execute_statement(
            resourceArn=self.cluster_arn,
            database=self.database,
            secretArn=self.secret_arn,
            includeResultMetadata=True,
            sql=sql,
        )
        return response

    def is_executable(self) -> bool:
        return (
            self.cluster_arn is not None
            and self.secret_arn is not None
            and self.database is not None
            and self.client is not None
        )

    def print(self):
        print("Type: rds-secretsmanager")
        print(f"Cluster arn: {self.cluster_arn}")
        print(f"Secret arn: {self.secret_arn}")
        print(f"Database: {self.database}")


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
    return RDSSecretsManagerSettings(
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
    return NoopConnectionSettings()
