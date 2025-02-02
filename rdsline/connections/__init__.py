"""
Connection abstract class.
"""

from abc import ABC, abstractmethod
from rdsline.results import StatementResult, NullResult


class Connection(ABC):
    """
    Connection for a database.
    """

    @abstractmethod
    def execute(self, sql: str) -> StatementResult:
        """
        Executes a query using this connection.
        """


class NoopConnection(Connection):
    """
    No op connection.
    """

    def __init__(self):
        pass

    def execute(self, _: str) -> StatementResult:
        return NullResult()

    def __str__(self) -> str:
        return "NoopConnection"
