from interface.telegram.classes import (
    DefaultTelegramConversationView,
)


def init():
    DatabaseTelegramConversationView(
        "organizations",
        [
            ["name", "text"],
        ],
    )
