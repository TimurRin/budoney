from interface.telegram.classes import SimpleTelegramConversationFork, TelegramConversationView


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

        [
            ("main", "gosbacc", SimpleTelegramConversationFork("main"))
        ],

    ])
