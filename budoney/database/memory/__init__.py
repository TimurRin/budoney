from typing import Any
from database.classes import Database
import utils.yaml_manager as yaml_manager
import configs


class MemoryDatabase(Database):
    db = {"data": {}, "internal": {"record_ids": 0}}

    def __init__(self, yaml_file):
        self.yaml_file = yaml_file
        saved = yaml_manager.load(self.yaml_file)
        if saved:
            self.db = saved
        else:
            self.db["data"] = yaml_manager.load(f"{self.yaml_file}-original")

    def get_records(
        self,
        table: str | None = None,
        table_select: list[str] | None = None,
        external: dict[str, Any] | None = None,
        join: list[dict[str, Any]] | None = None,
        join_select: list[dict[str, Any]] | None = None,
        search: set | None = None,
        search_columns: list[str] | None = None,
        order_by: list[tuple[str, bool, str | None]] | None = None,
        offset: int | None = None,
        limit: int | None = None,
        record_id: int | None = None,
    ) -> list[dict[str, Any]]:
        self._check_table(table)
        return list(self.db["data"][table].values())

    def get_records_count(self, table: str, query: str, values: list):
        self._check_table(table)
        return len(list(self.db["data"][table].values()))

    def replace_data(self, table: str, record_id, data: dict):
        self._check_table(table)
        data = self._check_data(dict(data))
        self.db["data"][table][data["id"]] = data
        yaml_manager.save(self.yaml_file, self.db)

    def append_data(self, table: str, data: dict):
        self._check_table(table)
        data = self._check_data(dict(data))
        self.db["data"][table][data["id"]] = data
        yaml_manager.save(self.yaml_file, self.db)

    def _check_table(self, table):
        if table not in self.db["data"]:
            self.db["data"][table] = {}

    def _check_data(self, data):
        if "id" not in data:
            data["id"] = f"ID_{self.db['internal']['record_ids']}"
            self.db["internal"]["record_ids"] = self.db["internal"]["record_ids"] + 1
        return data

    def create_table(self, table: str, columns: list[dict]):
        self._check_table(table)
        self.db["data"][table] = {}
        self._create_columns(table, columns)
        yaml_manager.save(self.yaml_file, self.db)

    def _create_columns(self, table_name, columns):
        for column in columns:
            self.db["data"][table_name][column["column"]] = column.get(
                "default_value", None
            )
