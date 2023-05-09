from database.memory import MemoryDatabase
import configs

print_label: str = "[budoney :: Database]"

DATABASE_ENGINE = "memory"
DATABASE_DRIVER = None
print(print_label, "DATABASE_ENGINE", DATABASE_ENGINE)
if DATABASE_ENGINE == "memory":
    DATABASE_DRIVER = MemoryDatabase()
