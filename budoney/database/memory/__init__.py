from database.classes import Database


class MemoryDatabase(Database):
    data: dict[dict] = {}

    def __init__(self):
        pass

    def get_record(self, table, record_id):
        self.check_table(table)
        return record_id in self.data[table] and self.data[table] or None

    def get_records(self, table):
        self.check_table(table)
        return list(self.data[table].values())

    def replace_data(self, table, record_id, data):
        self.check_table(table)
        self.data[table][record_id] = data

    def append_data(self, table, data):
        self.check_table(table)
        self.data[table][data["id"]] = data

    def check_table(self, table):
        if table not in self.data:
            self.data[table] = {}
