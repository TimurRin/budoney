from interface.telegram.classes import SimpleTelegramConversationFork, TelegramConversationView


def init():
    TelegramConversationView("wip", [
        [("main", "Back", SimpleTelegramConversationFork("main"))]
    ])
    TelegramConversationView("main", [
        [
            ("transaction_add_fast_type", "💸 Add transaction", SimpleTelegramConversationFork("transaction_add_fast_type"))], [
            ("task_current", "✍️🗒 New task", SimpleTelegramConversationFork("task_current"))
        ],
        [("finances", "💰 Finances", SimpleTelegramConversationFork("finances")), ("tasks", "🗒⏰ Tasks", SimpleTelegramConversationFork("tasks")), ("plants", "🌱 Plants", SimpleTelegramConversationFork("plants"))],
        [("users", "👫 Users", SimpleTelegramConversationFork("users"))]
    ])
    TelegramConversationView("users", [
        [("main", "go bacc", SimpleTelegramConversationFork("main"))]
    ])
