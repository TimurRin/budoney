import sqlite3
import threading
from database.classes import Database


class SQLiteDatabase(Database):
    SQLITE_DATA_TYPES = {
        "text": "TEXT",
        "int": "INTEGER",
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

    def get_records(
        self,
        table=None,
        external=None,
        join=None,
        join_select=None,
        offset=None,
        limit=None,
        record_id=None,
    ):
        selects = []
        selects_external = []
        joins = []
        values = []
        query = "SELECT"

        if external:
            for key, value in external.items():
                if key[0] != "_":
                    selects_external.append(f"'{value}' AS {key}")
        if table:
            selects.append(f"{table}.*")

        if (not external and len(selects) == 0) or (external and len(selects_external) == 0):
            return external and [external] or []

        for join_selectee in join_select:
            selects.append(
                f"{join_selectee['table']}.{join_selectee['column']} AS {join_selectee['table']}_{join_selectee['column']}"
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
            query += f" {table}.id = ?"
            values.append(record_id)
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

    def get_records_count(self, table):
        query = f"SELECT COUNT(*) FROM {table}"
        print("get_records_count", query)
        self.cursor.execute(query)
        return self.cursor.fetchone()[0]

    def replace_data(self, table, record_id, data):
        placeholders = ", ".join([f"{column} = ?" for column in data.keys()])
        values = tuple(data.values()) + (record_id,)
        query = f"UPDATE {table} SET {placeholders} WHERE id = ?"
        print("replace_data", query, values)
        self.cursor.execute(query, values)
        self.connection.commit()

    def append_data(self, table, data):
        parsed_data = {k: v for k, v in data.items() if not k.startswith('_')}
        columns = ", ".join(parsed_data.keys())
        placeholders = ", ".join(["?" for column in parsed_data.keys()])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        print("append_data", query, list(parsed_data.values()))
        hehe = self.cursor.execute(query, list(parsed_data.values()))
        print(hehe)
        self.connection.commit()

    def create_table(self, table_name, columns):
        column_definitions = [
            f"{column['column']} {self.SQLITE_DATA_TYPES.get(column['type'], 'TEXT')}{not ('skippable' in column and column['skippable']) and ' NOT NULL' or ''}"
            for column in columns
        ]

        for column in columns:
            if column["type"] == "data":
                column_definitions.append(
                    f"FOREIGN KEY ({column['column']}) REFERENCES {column['data_type']} (id) ON DELETE CASCADE"
                )

        query = f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, {', '.join(column_definitions)});"
        print("create_table", query)

        self.cursor.execute(query)
        self.connection.commit()
