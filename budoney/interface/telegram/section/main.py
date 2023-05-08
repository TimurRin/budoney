from interface.telegram.classes import (
    DefaultTelegramConversationView,
)


def init():
    DefaultTelegramConversationView(
        "main",
        [
            [
                "finances",
            ],
            [
                "tasks",
                "reminders",
            ],
            [
                "utilities",
                "clothes",
                "storage",
            ],
            [
                "health",
                "food",
                "plants",
            ],
            ["organizations", "people"],
        ],
    )
