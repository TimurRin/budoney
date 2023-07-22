from interface.telegram.classes import (
    DatabaseTelegramConversationView,
)


def init():
    DatabaseTelegramConversationView(
        "organizations",
        [
            {"column": "name", "type": "text"},
            {"column": "emoji", "type": "text", "skippable": True},
        ],
    )
