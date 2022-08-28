"""
Statement result types.
"""
from abc import ABC, abstractmethod
from typing import List
from tabulate import tabulate


# pylint: disable=too-few-public-methods
class StatementResult(ABC):
    """
    A statement result.
    """

    @abstractmethod
    def print(self):
        """
        Print this query result.
        """


# pylint: disable=too-few-public-methods
class DMLResult(StatementResult):
    """
    A DML/DDL result.
    """

    def __init__(self, number_updated: int):
        self.number_updated = number_updated

    def print(self):
        print(f"Number of record updated: {self.number_updated}")


# pylint: disable=too-few-public-methods
class QueryResult(StatementResult):
    """
    A query result.
    """

    def __init__(self, headers: List[str], rows: List[List[str]]):
        self.headers = headers
        self.rows = rows

    def print(self):
        print(tabulate(self.rows, headers=self.headers, tablefmt="psql"))
