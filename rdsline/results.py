"""
Statement result types.
"""

import sys
from abc import ABC, abstractmethod
from typing import List
from tabulate import tabulate


class StatementResult(ABC):
    """
    A statement result.
    """

    @abstractmethod
    def __str__(self):
        """
        This query result as a string. Used for printing it.
        """


class NullResult(StatementResult):
    """
    A Null result is used to signal that whatever connection is not ready or that is not set.
    """

    def __init__(self):
        pass

    def __str__(self):
        return "No connection set."


class DMLResult(StatementResult):
    """
    A DML/DDL result.
    """

    def __init__(self, number_updated: int):
        self.number_updated = number_updated

    def __str__(self):
        return f"Number of record updated: {self.number_updated}"


class QueryResult(StatementResult):
    """
    A query result.
    """

    def __init__(self, headers: List[str], rows: List[List[str]]):
        self.headers = headers
        self.rows = rows

    def __str__(self):
        tablefmt = "psql"
        headers = self.headers
        if not sys.stdin.isatty():
            tablefmt = "tsv"
            headers = []
        return tabulate(self.rows, headers=headers, tablefmt=tablefmt)
