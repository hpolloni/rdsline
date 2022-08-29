"""
Connection for RDS with a Secrets Manager secret.
"""
import logging
from typing import Any
from rdsline.connections import Connection
from rdsline.results import DMLResult, QueryResult, StatementResult


def _to_string(val: Any) -> str:
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


def _to_result(response) -> StatementResult:
    if "columnMetadata" not in response:
        # Assumed to be a DML/DDL operation
        if "numberOfRecordsUpdated" in response:
            return DMLResult(response["numberOfRecordsUpdated"])
    headers = [col["name"] for col in response["columnMetadata"]]
    records = [[_to_string(value) for value in row] for row in response["records"]]
    return QueryResult(headers, records)


class RDSSecretsManagerConnection(Connection):
    """
    Connection for RDS with secretsmanager.
    """

    def __init__(self, cluster_arn: str, secret_arn: str, database: str, client):
        self.cluster_arn = cluster_arn
        self.secret_arn = secret_arn
        self.database = database
        self.client = client

    def execute(self, sql: str) -> StatementResult:
        logging.debug("Executing query: %s", sql)
        response = self.client.execute_statement(
            resourceArn=self.cluster_arn,
            database=self.database,
            secretArn=self.secret_arn,
            includeResultMetadata=True,
            sql=sql,
        )
        logging.debug("Got response: %s", response)
        return _to_result(response)

    def is_executable(self) -> bool:
        return (
            self.cluster_arn is not None
            and self.secret_arn is not None
            and self.database is not None
            and self.client is not None
        )

    def __str__(self):
        return "\n".join(
            [
                "Type: rds-secretsmanager",
                f"Cluster arn: {self.cluster_arn}",
                f"Secret arn: {self.secret_arn}",
                f"Database: {self.database}",
            ]
        )
