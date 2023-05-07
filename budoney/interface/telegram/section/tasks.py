from interface.telegram.classes import (
    DefaultTelegramConversationView,
    TelegramConversationFork,
)


def init():
    DefaultTelegramConversationView(
        "tasks",
        [
            [
                TelegramConversationFork("tasks_current"),
                TelegramConversationFork("tasks_scheduled"),
            ],
        ],
    )
