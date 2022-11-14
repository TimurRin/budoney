from interface.telegram.classes import (
    TelegramConversationView,
    TelegramConversationFork,
)
from interface.telegram.utils import keyboard_back_button


def init():
    TelegramConversationView(
        "tasks",
        [
            [
                TelegramConversationFork("tasks_current"),
                TelegramConversationFork("tasks_scheduled"),
            ],
            [keyboard_back_button()],
        ],
    )
