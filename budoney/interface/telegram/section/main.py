from interface.telegram.classes import (
    TelegramConversationView,
    TelegramConversationFork,
)


def init():
    TelegramConversationView(
        "main",
        [
            [
                TelegramConversationFork("transaction"),
                TelegramConversationFork("task_current"),
            ],
            [
                TelegramConversationFork("finances"),
            ],
            [
                TelegramConversationFork("tasks"),
                TelegramConversationFork("reminders"),
            ],
            [
                TelegramConversationFork("utilities"),
                TelegramConversationFork("clothes"),
                TelegramConversationFork("storage"),
            ],
            [
                TelegramConversationFork("health"),
                TelegramConversationFork("food"),
                TelegramConversationFork("plants"),
            ],
            [TelegramConversationFork("users")],
        ],
    )
