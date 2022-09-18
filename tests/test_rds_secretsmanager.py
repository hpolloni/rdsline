
from rdsline.connections.rds_secretsmanager import RDSSecretsManagerConnection
from rdsline.results import DMLResult, QueryResult


CLUSTER_ARN = "the_resource_arn"
DATABASE = "the_database"
SECRET_ARN = "the_secret_arn"

class DummyClient:
    def __init__(self, expected_sql, expected_response):
        self.sql = expected_sql
        self.response = expected_response
    def execute_statement(self, resourceArn, database, secretArn, includeResultMetadata, sql):
        assert resourceArn == CLUSTER_ARN
        assert secretArn == SECRET_ARN
        assert database == DATABASE
        assert includeResultMetadata == True
        assert sql == self.sql
        return self.response


def test_can_get_dml_results():
    expected_response = {
        "numberOfRecordsUpdated": 3
    }
    sql = "UPDATE t SET i = 1"
    client = DummyClient(sql, expected_response)
    conn = RDSSecretsManagerConnection(CLUSTER_ARN, SECRET_ARN, DATABASE, client)
    results = conn.execute(sql) 
    assert type(results) == DMLResult
    assert results.number_updated == 3


def test_can_get_query_results():
    expected_response = {
        "columnMetadata": [
            {"name": "stringCol"},
            {"name": "boolCol"},
            {"name": "doubleCol"},
            {"name": "longCol"},
            {"name": "blobCol"},
            {"name": "withNulls"},
            {"name": "unknownCol"}
        ],
        "records": [
            [ # Row 1
                {"stringValue": "stringRow1"},
                {"booleanValue": True},
                {"doubleValue": 2.0},
                {"longValue": 12},
                {"blobValue": b'aa'},
                {"isNull": True},
                {"someValue": None}
            ],
            [ # Row 2
                {"stringValue": "stringRow2"},
                {"booleanValue": False},
                {"doubleValue": 1.0},
                {"longValue": 42},
                {"blobValue": b'hell'},
                {"longValue": 69},
                {"someValue": -1}
            ]
        ]
    }
    sql = "SELECT * FROM t1"
    client = DummyClient(sql, expected_response)
    conn = RDSSecretsManagerConnection(CLUSTER_ARN, SECRET_ARN, DATABASE, client)
    results = conn.execute(sql) 

    assert type(results) == QueryResult
    assert results.headers == ["stringCol", "boolCol", "doubleCol", "longCol", "blobCol", "withNulls", "unknownCol"]
    assert results.rows[0] == ["stringRow1", "True", "2.0", "12", "BLOB(6161)", "NULL", "UNKNOWN"]
    assert results.rows[1] == ["stringRow2", "False", "1.0", "42", "BLOB(68656c6c)","69", "UNKNOWN"]