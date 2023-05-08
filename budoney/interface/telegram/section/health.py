from interface.telegram.classes import (
    DefaultTelegramConversationView,
)


def init():
    DefaultTelegramConversationView(
        "health",
        [
            ["pills"],
            [
                "diseases",
            ],
            [
                "body_temperature",
            ],
        ],
    )
