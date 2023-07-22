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

    def get_record(self, table, record_id):
        query = f"SELECT * FROM {table} WHERE id=?", (record_id,)
        print("get_record", query)
        self.cursor.execute(query)
        return dict(self.cursor.fetchone())

    def get_records(self, table):
        query = f"SELECT * FROM {table}"
        print("get_records", query)
        self.cursor.execute(query)
        records = list()
        for record in self.cursor.fetchall():
            records.append(dict(record))
        return records

    def replace_data(self, table, record_id, data):
        placeholders = ", ".join([f"{column} = ?" for column in data.keys()])
        values = tuple(data.values()) + (record_id,)
        query = f"UPDATE {table} SET {placeholders} WHERE id = ?"
        print("replace_data", query)
        self.cursor.execute(query, values)
        self.connection.commit()

    def append_data(self, table, data):
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for column in data.keys()])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        print("append_data", query, data.values())
        hehe = self.cursor.execute(query, list(data.values()))
        print(hehe)
        self.connection.commit()

    def create_table(self, table_name, columns):
        column_definitions = [
            f"{column['column']} {self.SQLITE_DATA_TYPES.get(column['type'], 'TEXT')}{not ('skippable' in column and column['skippable']) and ' NOT NULL' or ''}"
            for column in columns
        ]

        query = f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, {', '.join(column_definitions)});"
        print("create_table", query)

        self.cursor.execute(query)
        self.connection.commit()
