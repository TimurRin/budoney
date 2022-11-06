from interface.telegram.classes import SimpleTelegramConversationFork, TelegramConversationView
from interface.telegram.utils import keyboard_row_back


def init():
    TelegramConversationView("main", [
        [
            ("transaction_add_fast_type", "💸 Add transaction", SimpleTelegramConversationFork("transaction_add_fast_type"))], [
            ("task_current", "✍️🗒 New task",
             SimpleTelegramConversationFork("task_current"))
        ],
        [("finances", "💰 Finances", SimpleTelegramConversationFork("finances")), ("tasks", "🗒⏰ Tasks",
                                                                                  SimpleTelegramConversationFork("tasks")), ("plants", "🌱 Plants", SimpleTelegramConversationFork("plants"))],
        [("users", "👫 Users", SimpleTelegramConversationFork("users"))]
    ])
    TelegramConversationView("users", [
        keyboard_row_back()
    ])
