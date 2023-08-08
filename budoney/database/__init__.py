from database.classes import Database
from database.memory import MemoryDatabase
from database.sqlite import SQLiteDatabase
import configs

print_label: str = "[budoney :: Database]"

DATABASE_ENGINE = "sqlite"
DATABASE_DRIVER: Database
if DATABASE_ENGINE == "memory":
    DATABASE_DRIVER = MemoryDatabase("data/memory")
elif DATABASE_ENGINE == "sqlite":
    DATABASE_DRIVER = SQLiteDatabase("data/budoney.sqlite")


def init():
    print(print_label, "DATABASE_ENGINE", DATABASE_ENGINE)
