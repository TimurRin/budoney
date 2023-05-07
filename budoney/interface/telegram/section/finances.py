from interface.telegram.classes import (
    DefaultTelegramConversationView,
    DatabaseTelegramConversationView,
    TelegramConversationFork,
)


def init():
    DefaultTelegramConversationView(
        "finances",
        [
            [
                TelegramConversationFork("transactions"),
            ],
            [
                TelegramConversationFork("merchants"),
                TelegramConversationFork("methods"),
            ],
            [
                TelegramConversationFork("categories"),
                TelegramConversationFork("currencies"),
            ],
        ],
    )
    DatabaseTelegramConversationView("transactions")
