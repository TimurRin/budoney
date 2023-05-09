from database.classes import Database


class MemoryDatabase(Database):
    data: dict[dict] = {}
    record_ids = 0

    def __init__(self):
        pass

    def get_record(self, table, record_id):
        self._check_table(table)
        return record_id in self.data[table] and self.data[table] or None

    def get_records(self, table):
        self._check_table(table)
        return list(self.data[table].values())

    def replace_data(self, table, data):
        self._check_table(table)
        self._check_data(data)
        self.data[table][data["id"]] = data

    def append_data(self, table, data):
        self._check_table(table)
        self._check_data(data)
        self.data[table][data["id"]] = data

    def _check_table(self, table):
        if table not in self.data:
            self.data[table] = {}

    def _check_data(self, data):
        if "id" not in data:
            data["id"] = self.record_ids
            self.record_ids = self.record_ids + 1
