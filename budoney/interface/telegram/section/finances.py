from interface.telegram.classes import SIMPLE_FORK, TelegramConversationView
from interface.telegram.utils import keyboard_back_button


def init():
    TelegramConversationView("finances", [
        [
            ("transaction", "➕💸 Transaction", SIMPLE_FORK),
        ],
        [
            ("transactions", "👛 Transactions", SIMPLE_FORK),
        ],
        [
            ("merchants", "🏪 Merchants", SIMPLE_FORK),
            ("methods", "💳 Methods", SIMPLE_FORK),
        ],
        [
            ("categories", "🏷 Categories", SIMPLE_FORK),
            ("currencies", "💱 Currencies", SIMPLE_FORK),
        ],
        [keyboard_back_button()]
    ])
    TelegramConversationView("transaction", [
        [
            ("transaction_type", "", SIMPLE_FORK),
        ],
        [keyboard_back_button()]
    ], )
    TelegramConversationView("transaction_type", [
        [
            ("expense", "", SIMPLE_FORK),
            ("income", "", SIMPLE_FORK),
        ],
        [keyboard_back_button()]
    ])
