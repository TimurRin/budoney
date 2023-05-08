from interface.telegram.classes import (
    DatabaseTelegramConversationView,
)


def init():
    DatabaseTelegramConversationView(
        "people",
        [
            {"column": "name", "type": "text"},
            {"column": "emoji", "type": "text"},
        ],
    )
