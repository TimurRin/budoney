class Database:
    def __init__(self):
        pass

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
        pass

    def get_records_count(self, table):
        pass

    def replace_data(self, table, record_id, data):
        pass

    def append_data(self, table, data):
        pass

    def create_table(self, table_name, columns):
        pass
