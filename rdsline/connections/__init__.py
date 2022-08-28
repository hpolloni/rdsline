"""
Connection abstract class.
"""
from abc import ABC, abstractmethod
from rdsline.results import StatementResult


class Connection(ABC):
    """
    Connection for a database.
    """

    @abstractmethod
    def execute(self, sql: str) -> StatementResult:
        """
        Executes a query using this connection.
        """

    @abstractmethod
    def is_executable(self) -> bool:
        """
        Returns if this connection is executable (i.e. all settings are correctly set)
        """

    @abstractmethod
    def print(self):
        """
        Print the connection settings. Intended for use in the CLI.
        """


class NoopConnection(Connection):
    """
    No op connection.
    """

    def __init__(self):
        pass

    def is_executable(self) -> bool:
        return False

    def print(self):
        print("No connection settings. Maybe you need to run .config")

    def execute(self, sql: str) -> StatementResult:
        raise NotImplementedError("Execute in No op")
