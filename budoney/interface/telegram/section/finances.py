from interface.telegram.classes import SimpleTelegramConversationFork, TelegramConversationView
from interface.telegram.utils import keyboard_row_back


def init():
    TelegramConversationView("finances", [
        [
            ("transactions", "👛 Transactions",
             SimpleTelegramConversationFork("transactions")),
            ("transaction_add_fast_type", "💸 Add transaction",
             SimpleTelegramConversationFork("transaction_add_fast_type")),
        ],
        [
            ("merchants", "🏪 Merchants", SimpleTelegramConversationFork("merchants")),
            ("methods", "💳 Methods", SimpleTelegramConversationFork("methods")),
        ],
        [
            ("categories", "🏷 Categories",
             SimpleTelegramConversationFork("categories")),
            ("currencies", "💱 Currencies",
             SimpleTelegramConversationFork("currencies")),
        ],

        keyboard_row_back()

    ])
