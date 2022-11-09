from interface.telegram.classes import SIMPLE_FORK, TelegramConversationView


def init():
    TelegramConversationView(
        "main",
        [
            [
                ("transaction", "➕💸 Transaction", SIMPLE_FORK),
                ("task_current", "➕🗒 Task", SIMPLE_FORK),
            ],
            [
                ("finances", "💸 Finances", SIMPLE_FORK),
            ],
            [
                ("tasks", "🗒 Tasks", SIMPLE_FORK),
                ("reminders", "⏰ Reminders", SIMPLE_FORK),
            ],
            [
                ("utilities", "🚰 Utilities", SIMPLE_FORK),
                ("clothes", "👚 Clothes", SIMPLE_FORK),
                ("storage", "📦 Storage", SIMPLE_FORK),
            ],
            [
                ("food", "🥘 Food", SIMPLE_FORK),
                ("pills", "💊 Pills", SIMPLE_FORK),
                ("plants", "🌱 Plants", SIMPLE_FORK),
            ],
            [("users", "👫 Users", SIMPLE_FORK)],
        ],
    )
