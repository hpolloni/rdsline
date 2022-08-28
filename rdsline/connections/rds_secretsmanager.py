"""
Connection for RDS with a Secrets Manager secret.
"""
from typing import Any, List, Tuple
from rdsline.connections import Connection


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


def _to_table(response) -> Tuple[List[str], List[List[str]]]:
    headers = [col["name"] for col in response["columnMetadata"]]
    records = [[_to_string(value) for value in row] for row in response["records"]]
    return (headers, records)


class RDSSecretsManagerConnection(Connection):
    """
    Connection for RDS with secretsmanager.
    """

    def __init__(self, cluster_arn: str, secret_arn: str, database: str, client):
        self.cluster_arn = cluster_arn
        self.secret_arn = secret_arn
        self.database = database
        self.client = client

    def execute(self, sql: str) -> Tuple[List[str], List[List[str]]]:
        response = self.client.execute_statement(
            resourceArn=self.cluster_arn,
            database=self.database,
            secretArn=self.secret_arn,
            includeResultMetadata=True,
            sql=sql,
        )
        return _to_table(response)

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
