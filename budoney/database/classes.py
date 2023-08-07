import abc
from typing import Any

class Database:
    def __init__(self):
        pass

    @abc.abstractmethod
    def get_records_query(
        self,
        table: str | None = None,
        table_select: list[str] | None = None,
        external: dict[str, Any] | None = None,
        join: list[dict[str, Any]] | None = None,
        join_select: list[dict[str, Any]] | None = None,
        search: set | None = None,
        search_columns: list[str] | None = None,
        order_by: list[tuple[str, bool, str | None]] | None = None,
        record_id: int | None = None,
    ) -> tuple[str, list[Any]]:
        pass

    @abc.abstractmethod
    def get_records(
        self,
        query: str,
        values: list,
        offset: int | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        pass

    @abc.abstractmethod
    def get_records_count(self, table: str, query: str, values: list):
        pass

    @abc.abstractmethod
    def get_report(
        self,
        query: str,
        values: list,
        select: list[str],
        group_by: list[str],
        order_by: list[tuple[str, bool]],
    ):
        pass

    @abc.abstractmethod
    def replace_data(self, table: str, record_id, data: dict):
        pass

    @abc.abstractmethod
    def append_data(self, table: str, data: dict):
        pass

    @abc.abstractmethod
    def create_table(self, table: str, columns: list[dict]):
        pass
