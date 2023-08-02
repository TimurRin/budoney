from interface.telegram.classes import (
    DefaultView,
)


def init():
    DefaultView(
        "main",
        [
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
            # [
            #     "health",
            #     "food",
            #     "plants",
            # ],
            ["organizations", "people"],
        ],
    )
