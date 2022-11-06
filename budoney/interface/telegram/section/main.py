from interface.telegram.classes import SimpleTelegramConversationFork, TelegramConversationView
from interface.telegram.utils import keyboard_row_back


def init():
    TelegramConversationView("main", [
        [
            ("transaction_add_fast_type", "✍️💸 Transaction", SimpleTelegramConversationFork("transaction")),
            ("task_current", "✍️🗒 Task",
             SimpleTelegramConversationFork("task_current"))
        ],
        [
            ("finances", "💰 Finances", SimpleTelegramConversationFork("finances")),
        ],
        [
            ("tasks", "🗒 Tasks", SimpleTelegramConversationFork("tasks")),
            ("reminders", "⏰ Reminders", SimpleTelegramConversationFork("reminders")),

        ],
        [
            ("utilities", "🚰 Utilities", SimpleTelegramConversationFork("utilities")),
            ("storage", "📦 Storage", SimpleTelegramConversationFork("storage")),
        ],
        [
            ("food", "🥘 Food", SimpleTelegramConversationFork("food")),
            ("pills", "💊 Pills", SimpleTelegramConversationFork("pills")),
            ("plants", "🌱 Plants", SimpleTelegramConversationFork("plants")),
        ],
        [("users", "👫 Users", SimpleTelegramConversationFork("users"))]
    ])
    TelegramConversationView("users", [
        keyboard_row_back()
    ])
