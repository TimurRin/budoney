import sqlite3
import threading
from typing import Any
from datetime import datetime
from database.classes import Database
from utils.transliterate import russian_to_latin

print_label: str = "[budoney :: Database :: SQLite]"


class SQLiteDatabase(Database):
    SQLITE_DATA_TYPES = {
        "text": "TEXT",
        "int": "INTEGER",
        "boolean": "INTEGER",
        "float": "REAL",
        "date": "INTEGER",
        "timestamp": "INTEGER",
        "data": "INTEGER",
    }

    def __init__(self, database_path):
        super().__init__()
        self.db_path = database_path
        self._local = threading.local()
        self._init_connection_and_cursor()
        self._create_technical_tables()

    def _init_connection_and_cursor(self):
        if not hasattr(self._local, "connection"):
            self._local.connection = sqlite3.connect(self.db_path)
            self._local.connection.row_factory = sqlite3.Row
        if not hasattr(self._local, "cursor"):
            self._local.cursor = self._local.connection.cursor()

    @property
    def connection(self) -> sqlite3.Connection:
        self._init_connection_and_cursor()
        return self._local.connection

    @property
    def cursor(self) -> sqlite3.Cursor:
        self._init_connection_and_cursor()
        return self._local.cursor

    def get_records_query(
        self,
        table: str | None = None,
        table_select: list[str] | None = None,
        external: dict[str, Any] | None = None,
        join: list[dict[str, Any]] | None = None,
        join_select: list[dict[str, Any]] | None = None,
        order_by: list[tuple[str, bool, str | None]] | None = None,
        conditions: list | None = None,
        record_ids: list[int] | None = None,
    ) -> tuple[str, list[Any]]:
        selects = []
        selects_external = []
        joins = []
        wheres = []
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
                if "custom" in linked_table:
                    joins.append(linked_table["custom"])
                else:
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
        if record_ids and not external and table:
            record_ids_set = set(record_ids)
            if len(record_ids_set) > 1:
                query += f" WHERE {table}.id IN ({('?, ' * len(record_ids_set))[:-2]})"
                values.extend(record_ids_set)
            else:
                query += f" WHERE {table}.id = ?"
                values.append(record_ids[0])
        if conditions:
            for condition in conditions:
                wheres.append(condition)
        if len(wheres) > 0:
            query += f" WHERE {' OR '.join(wheres)}"
        if order_by and not record_ids and not external:
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
        print(print_label, print_label, "get_records", query, values)
        self.cursor.execute(query, values)
        records = list()
        for record in self.cursor.fetchall():
            records.append(dict(record))
        return records

    def get_records_count(self, table: str, query: str, values: list) -> int:
        count_query = f"SELECT COUNT(*) FROM ({query})"
        print(print_label, print_label, "get_records_count", count_query)
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
    ) -> list[Any]:
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

        print(print_label, "get_report", report_query)
        self.cursor.execute(report_query, values)
        records = list()
        for record in self.cursor.fetchall():
            records.append(dict(record))
        return records

    def get_data(self, query: str, values: list) -> list[dict[str, Any]]:
        print(print_label, "get_data", query, values)
        self.cursor.execute(query, values)
        records = list()
        for record in self.cursor.fetchall():
            records.append(dict(record))
        return records

    def commit(self) -> None:
        self.connection.commit()

    def replace_data(self, table: str, record_id, data: dict, commit=True):
        placeholders = ", ".join([f"{column} = ?" for column in data.keys()])
        values = tuple(data.values()) + (record_id,)
        query = f"UPDATE {table} SET {placeholders} WHERE id = ?"
        print(print_label, "replace_data", query, values)
        self.cursor.execute(query, values)
        self._revalidate_search_cache(table, record_id, data)
        if commit:
            self.connection.commit()

    def append_data(self, table: str, data: dict, commit=True) -> int | None:
        parsed_data = {
            k: v for k, v in data.items() if not k.startswith("_") and v or v == 0
        }
        columns = ", ".join(parsed_data.keys())
        placeholders = ", ".join(["?" for column in parsed_data.keys()])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        print(print_label, "append_data", query, list(parsed_data.values()))
        self.cursor.execute(query, list(parsed_data.values()))
        last_id = self.cursor.lastrowid
        self._revalidate_search_cache(table, last_id, data)
        if commit:
            self.connection.commit()
        return last_id

    def delete_data(self, table: str, record_id):
        values = (record_id,)
        query = f"DELETE FROM {table} WHERE id = ?"
        print(print_label, "delete_data", query, values)
        self.cursor.execute(query, values)
        self.connection.commit()

    def _create_technical_tables(self):
        query_search_compound = f"CREATE TABLE IF NOT EXISTS search_compound (table_name TEXT, entry_id INTEGER, entry_field TEXT, field_data TEXT, field_data_translit TEXT, PRIMARY KEY(table_name, entry_id, entry_field))"
        print(print_label, "_create_technical_tables", query_search_compound)
        self.cursor.execute(query_search_compound)

        query_entries_usage = f"CREATE TABLE IF NOT EXISTS entries_usage (table_name TEXT, entry_id INTEGER, total_usages INTEGER, last_date INTEGER, PRIMARY KEY(table_name, entry_id))"
        print(print_label, "_create_technical_tables", query_entries_usage)
        self.cursor.execute(query_entries_usage)

        self.connection.commit()

    def update_entry_usage(self, table_name, entry_id, timestamp=None):
        query = f"INSERT INTO entries_usage (table_name, entry_id, last_date) VALUES (?, ?, ?) ON CONFLICT (table_name, entry_id) DO UPDATE SET last_date=excluded.last_date"
        if not timestamp:
            timestamp = int(datetime.today().timestamp())
        values = (table_name, entry_id, timestamp)
        print(print_label, "update_entry_usage", query, values)

        self.cursor.execute(query, values)

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
        print(print_label, "create_table", query)

        self.cursor.execute(query)

        self.connection.commit()

    def search(self, tables: list[str], text_inputs: list[str]) -> list[dict]:
        search_results = []

        for table in tables:
            wheres = []
            values = [table]

            for text_input in text_inputs:
                text_input = text_input.lower()
                wheres.append(
                    "(field_data LIKE ? OR field_data_translit LIKE ? OR field_data LIKE ?)"
                )
                values.extend(
                    (
                        f"%{text_input}%",
                        f"%{russian_to_latin(text_input)}%",
                        f"%{russian_to_latin(text_input)}%",
                    )
                )

            query = f"SELECT table_name, entry_id, entry_field, field_data FROM search_compound WHERE table_name = ? AND ({' OR '.join(wheres)})"
            print(print_label, "search", table, query, values)
            self.cursor.execute(query, values)
            results = self.cursor.fetchall()

            search_results.extend(results)

        return search_results

    def _revalidate_search_cache(self, table, record_id, data):
        parsed_data_search = {
            k: v.lower()
            for k, v in data.items()
            if not k.startswith("_") and isinstance(v, str) and v
        }
        if parsed_data_search:
            values = []
            values_placeholders = []
            for key in parsed_data_search:
                text = parsed_data_search[key]
                values.append(table)
                values.append(record_id)
                values.append(key)
                values.append(parsed_data_search[key])
                text_translit = russian_to_latin(text)
                if text != text_translit:
                    values.append(text_translit)
                else:
                    values.append(None)
                values_placeholders.append("?, ?, ?, ?, ?")
            query_search = f"INSERT INTO search_compound (table_name, entry_id, entry_field, field_data, field_data_translit) VALUES ({'), ('.join(values_placeholders)}) ON CONFLICT (table_name, entry_id, entry_field) DO UPDATE SET field_data=excluded.field_data, field_data_translit=excluded.field_data_translit"
            print(print_label, "_update_search", query_search, values)
            self.cursor.execute(query_search, values)
