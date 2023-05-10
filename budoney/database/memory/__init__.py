from database.classes import Database
import utils.yaml_manager as yaml_manager
import configs


class MemoryDatabase(Database):
    db = {"data": {}, "internal": {"record_ids": 0}}

    def __init__(self):
        saved = yaml_manager.load("data/memory")
        if saved:
            self.db = saved
        else:
            self.db["data"] = yaml_manager.load("data/memory-original")

    def get_record(self, table, record_id):
        self._check_table(table)
        return record_id in self.db["data"][table] and self.db["data"][table] or None

    def get_records(self, table):
        self._check_table(table)
        return list(self.db["data"][table].values())

    def replace_data(self, table, data):
        self._check_table(table)
        data = self._check_data(dict(data))
        self.db["data"][table][data["id"]] = data
        yaml_manager.save("data/memory", self.db)

    def append_data(self, table, data):
        self._check_table(table)
        data = self._check_data(dict(data))
        self.db["data"][table][data["id"]] = data
        yaml_manager.save("data/memory", self.db)

    def _check_table(self, table):
        if table not in self.db["data"]:
            self.db["data"][table] = {}

    def _check_data(self, data):
        if "id" not in data:
            data["id"] = f"ID_{self.db['internal']['record_ids']}"
            self.db["internal"]["record_ids"] = self.db["internal"]["record_ids"] + 1
        return data
