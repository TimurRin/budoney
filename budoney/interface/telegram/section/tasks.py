from interface.telegram.classes import SimpleTelegramConversationFork, TelegramConversationView
from interface.telegram.utils import keyboard_row_back


def init():
    TelegramConversationView("tasks", [
        [
            ("tasks_current", "🗒 Current tasks",
             SimpleTelegramConversationFork("tasks_current")),
            ("tasks_scheduled", "⏰ Scheduled tasks",
             SimpleTelegramConversationFork("tasks_scheduled")),
        ],
        keyboard_row_back()
    ])
