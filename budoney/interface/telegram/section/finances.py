from interface.telegram.classes import SIMPLE_FORK, TelegramConversationView
from interface.telegram.utils import keyboard_row_back


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
        keyboard_row_back()
    ])
    TelegramConversationView("transaction", [
        [
            ("transaction_type", "", SIMPLE_FORK),
        ],
        keyboard_row_back()
    ])