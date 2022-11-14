from interface.telegram.classes import (
    TelegramConversationFork,
    TelegramConversationView,
)
from interface.telegram.utils import keyboard_back_button


def init():
    TelegramConversationView(
        "health",
        [
            [TelegramConversationFork("pills")],
            [
                TelegramConversationFork("diseases"),
            ],
            [
                TelegramConversationFork("body_temperature"),
            ],
            [keyboard_back_button()],
        ],
    )
