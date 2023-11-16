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
        order_by: list[tuple[str, bool, str | None]] | None = None,
        conditions: tuple[list[str], list[Any]] | None = None,
        record_ids: list[int] | None = None,
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
    def get_records_count(self, table: str, query: str, values: list) -> int:
        pass

    @abc.abstractmethod
    def get_report(
        self,
        query: str,
        values: list,
        select: list[tuple[str, str | None]],
        group_by: list[str],
        order_by: list[tuple[str, bool, str | None]],
        conditions: list,
    ) -> list[Any]:
        pass

    @abc.abstractmethod
    def commit(self) -> None:
        pass

    @abc.abstractmethod
    def get_data(self, query: str, values: list) -> list[dict[str, Any]]:
        pass

    @abc.abstractmethod
    def replace_data(self, table: str, record_id, data: dict):
        pass

    @abc.abstractmethod
    def append_data(self, table: str, data: dict, commit=True) -> int | None:
        pass

    @abc.abstractmethod
    def delete_data(self, table: str, record_id):
        pass

    @abc.abstractmethod
    def create_table(self, table: str, columns: list[dict]):
        pass

    @abc.abstractmethod
    def search(self, tables: list[str], text_inputs: list[str]) -> list[dict]:
        pass

    @abc.abstractmethod
    def update_entry_usage(self, table_name, entry_id):
        pass

    @abc.abstractmethod
    def _revalidate_search_cache(self, table, record_id, data):
        pass
