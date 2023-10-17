from interface.telegram.classes import (
    DefaultView
)

def init():
    DefaultView(
        "main",
        [
            ["transfer_ADD", "tasks_current_ADD"],
            ["income_ADD", "expenses_ADD"],
            [
                "tasks",
                "finances",
            ],
            [
                # "tasks",
                # "reminders",
            ],
            # [
            #     "utilities",
            #     "clothes",
            #     "storage",
            # ],
            # [
            # "health",
            # "food",
            # "plants",
            # ],
            ["organizations", "people"],
            ["settings"]
        ],
    )
