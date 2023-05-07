from interface.telegram.classes import (
    DefaultTelegramConversationView,
    TelegramConversationFork,
)


def init():
    DefaultTelegramConversationView(
        "main",
        [
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
