from interface.telegram.classes import (
    DefaultView,
)


def init():
    DefaultView(
        "main",
        [
            ["tasks_current_ADD", "expenses_ADD"],
            [
                "finances",
            ],
            [
                "tasks",
                # "reminders",
            ],
            # [
            #     "utilities",
            #     "clothes",
            #     "storage",
            # ],
            [
                # "health",
                # "food",
                "plants",
            ],
            ["organizations", "people"],
        ],
    )
