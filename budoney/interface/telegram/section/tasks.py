from interface.telegram.classes import SIMPLE_FORK, TelegramConversationView
from interface.telegram.utils import keyboard_row_back


def init():
    TelegramConversationView("tasks", [
        [
            ("tasks_current", "🗒 Current tasks", SIMPLE_FORK),
            ("tasks_scheduled", "⏰ Scheduled tasks", SIMPLE_FORK),
        ],
        keyboard_row_back()
    ])
