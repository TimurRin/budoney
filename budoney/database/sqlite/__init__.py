import sqlite3
import threading
from typing import Any
from database.classes import Database


class SQLiteDatabase(Database):
    SQLITE_DATA_TYPES = {
        "text": "TEXT",
        "int": "INTEGER",
        "boolean": "INTEGER",
        "float": "REAL",
        "date": "INTEGER",
        "data": "INTEGER",
    }

    def __init__(self, database_path):
        super().__init__()
        self.db_path = database_path
        self._local = threading.local()
        self._init_connection_and_cursor()

    def _init_connection_and_cursor(self):
        if not hasattr(self._local, "connection"):
            self._local.connection = sqlite3.connect(self.db_path)
            self._local.connection.row_factory = sqlite3.Row
        if not hasattr(self._local, "cursor"):
            self._local.cursor = self._local.connection.cursor()

    @property
    def connection(self):
        self._init_connection_and_cursor()
        return self._local.connection

    @property
    def cursor(self):
        self._init_connection_and_cursor()
        return self._local.cursor

    def get_records_query(
        self,
        table: str | None = None,
        table_select: list[str] | None = None,
        external: dict[str, Any] | None = None,
        join: list[dict[str, Any]] | None = None,
        join_select: list[dict[str, Any]] | None = None,
        search: tuple[str, list[str]] | None = None,
        search_columns: list[str] | None = None,
        order_by: list[tuple[str, bool, str | None]] | None = None,
        record_id: int | None = None,
    ) -> tuple[str, list[Any]]:
        selects = []
        selects_external = []
        joins = []
        values = []
        query: str = "SELECT"

        if external:
            for key, value in external.items():
                if key[0] != "_":
                    if isinstance(value, str):
                        selects_external.append(f"'{value}' AS {key}")
                    elif value:
                        selects_external.append(f"{value} AS {key}")
                    else:
                        selects_external.append(f"NULL AS {key}")
        if table and table_select:
            for table_selectee in table_select:
                selects.append(f"{table}.{table_selectee} AS {table_selectee}")
        elif table:
            selects.append(f"{table}.*")

        if join_select:
            for join_selectee in join_select:
                selects.append(
                    f"{join_selectee['table']}.{join_selectee['column']} AS {join_selectee['table']}__{join_selectee['column']}"
                )
        if join:
            for linked_table in join:
                joins.append(
                    f"LEFT JOIN {linked_table['name']} AS {linked_table['alias']} ON {linked_table['alias']}.id = {linked_table['parent']}.{linked_table['linkedBy']}"
                )
        if len(selects) > 0:
            query += f" {', '.join(selects)}"
        else:
            query += " *"
        if external and len(selects_external) > 0:
            query += f" FROM (SELECT {', '.join(selects_external)}) AS {table}"
        elif table:
            query += f" FROM {table}"
        if join:
            query += f" {' '.join(joins)}"
        if record_id and not external and table:
            query += f" WHERE {table}.id = ?"
            values.append(record_id)
        if search and search_columns:
            wheres = []
            for search_column in search_columns:
                for searchee in search[1]:
                    wheres.append(f'{search_column} LIKE "%{searchee}%"')
            if len(wheres) > 0:
                query += f" WHERE {' OR '.join(wheres)}"
        if order_by and not record_id and not external:
            order_by_query = []
            for orderee in order_by:
                if orderee[2]:
                    order_by_query.append(f"{orderee[0]} {orderee[2]}")
                order_by_query.append(f"{orderee[0]} {orderee[1] and 'DESC' or 'ASC'}")
            query += " ORDER BY " + ", ".join(order_by_query)
        return (str(query), values)

    def get_records(
        self,
        query: str,
        values: list,
        offset: int | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        if limit and limit > 0:
            query += " LIMIT " + str(limit)
        if offset and offset > 0:
            query += " OFFSET " + str(offset)
        print("get_records", query, values)
        self.cursor.execute(query, values)
        records = list()
        for record in self.cursor.fetchall():
            records.append(dict(record))
        return records

    def get_records_count(self, table: str, query: str, values: list):
        count_query = f"SELECT COUNT(*) FROM ({query})"
        print("get_records_count", count_query)
        self.cursor.execute(count_query, values)
        return self.cursor.fetchone()[0]

    def get_report(
        self,
        query: str,
        values: list,
        select: list[tuple[str, str | None]],
        group_by: list[str],
        order_by: list[tuple[str, bool, str | None]],
        conditions: list,
    ):
        select_query = []
        for selectee in select:
            if selectee[1]:
                select_query.append(f"{selectee[1]} AS {selectee[0]}")
            else:
                select_query.append(selectee[0])

        report_query = f"SELECT {', '.join(select_query)} FROM ({query})"

        if len(conditions) > 0:
            report_query += f" WHERE ({') AND ('.join(conditions)})"

        if len(group_by) > 0:
            report_query += f" GROUP BY {', '.join(group_by)}"

        order_by_query = []
        for orderee in order_by:
            if orderee[2]:
                order_by_query.append(f"{orderee[0]} {orderee[2]}")
            order_by_query.append(f"{orderee[0]} {orderee[1] and 'DESC' or 'ASC'}")
        report_query += " ORDER BY " + ", ".join(order_by_query)

        print("get_report", report_query)
        self.cursor.execute(report_query, values)
        records = list()
        for record in self.cursor.fetchall():
            records.append(dict(record))
        return records

    def replace_data(self, table: str, record_id, data: dict):
        placeholders = ", ".join([f"{column} = ?" for column in data.keys()])
        values = tuple(data.values()) + (record_id,)
        query = f"UPDATE {table} SET {placeholders} WHERE id = ?"
        print("replace_data", query, values)
        self.cursor.execute(query, values)
        self.connection.commit()

    def append_data(self, table: str, data: dict):
        parsed_data = {k: v for k, v in data.items() if not k.startswith("_")}
        columns = ", ".join(parsed_data.keys())
        placeholders = ", ".join(["?" for column in parsed_data.keys()])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        print("append_data", query, list(parsed_data.values()))
        hehe = self.cursor.execute(query, list(parsed_data.values()))
        self.connection.commit()

    def create_table(self, table: str, columns: list[dict]):
        column_definitions = [
            f"{column['column']} {self.SQLITE_DATA_TYPES.get(column['type'], 'TEXT')}{not ('skippable' in column and column['skippable']) and ' NOT NULL' or ''}"
            for column in columns
        ]

        for column in columns:
            if column["type"] == "data":
                column_definitions.append(
                    f"FOREIGN KEY ({column['column']}) REFERENCES {column['data_type']} (id) ON DELETE CASCADE"
                )

        query = f"CREATE TABLE IF NOT EXISTS {table} (id INTEGER PRIMARY KEY AUTOINCREMENT, {', '.join(column_definitions)});"
        print("create_table", query)

        self.cursor.execute(query)
        self.connection.commit()
