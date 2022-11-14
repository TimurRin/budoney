from interface.telegram.classes import (
    TelegramConversationView,
    TelegramConversationFork,
    EnumTelegramConversationFork,
)
from interface.telegram.utils import keyboard_back_button

transaction_types: "list[str]" = ["INCOME", "EXPENSE"]
transaction_types_fork: EnumTelegramConversationFork = EnumTelegramConversationFork(
    "transaction_type", transaction_types
)


def init():
    TelegramConversationView(
        "finances",
        [
            [
                TelegramConversationFork("transaction"),
            ],
            [
                TelegramConversationFork("transactions"),
            ],
            [
                TelegramConversationFork("merchants"),
                TelegramConversationFork("methods"),
            ],
            [
                TelegramConversationFork("categories"),
                TelegramConversationFork("currencies"),
            ],
            [keyboard_back_button()],
        ],
    )
    TelegramConversationView(
        "transaction",
        [
            [transaction_types_fork],
            [keyboard_back_button()],
        ],
    )
