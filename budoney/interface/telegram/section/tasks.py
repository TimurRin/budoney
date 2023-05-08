from interface.telegram.classes import (
    DefaultTelegramConversationView,
)


def init():
    DefaultTelegramConversationView(
        "tasks",
        [
            [
                "tasks_current",
                "tasks_scheduled",
            ],
        ],
    )
