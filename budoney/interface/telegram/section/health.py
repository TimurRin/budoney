from interface.telegram.classes import (
    TelegramConversationFork,
    DefaultTelegramConversationView,
)


def init():
    DefaultTelegramConversationView(
        "health",
        [
            [TelegramConversationFork("pills")],
            [
                TelegramConversationFork("diseases"),
            ],
            [
                TelegramConversationFork("body_temperature"),
            ],
        ],
    )
