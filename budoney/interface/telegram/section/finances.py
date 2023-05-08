from interface.telegram.classes import (
    DefaultTelegramConversationView,
    DatabaseTelegramConversationView,
)


def init():
    DefaultTelegramConversationView(
        "finances",
        [
            [
                "transactions",
            ],
            [
                "financial_accounts",
                "payment_cards",
            ],
            [
                "categories",
                "currencies",
            ],
        ],
    ),
    DefaultTelegramConversationView(
        "transactions",
        [
            [
                "income",
                "expense",
            ],
            ["transfer"],
        ],
    )
    DatabaseTelegramConversationView(
        "income",
        [
            ["date", "date"],
            ["sum", "float"],
            ["currency", "data", "currencies"],
            ["financial_account", "data", "financial_accounts"],
            ["organization", "data", "organizations"],
            ["description", "text"],
        ],
    ),
    DatabaseTelegramConversationView(
        "expenses",
        [
            ["date", "date"],
            ["sum", "float"],
            ["currency", "data", "currencies"],
            ["financial_account", "data", "financial_accounts"],
            ["organization", "data", "organizations"],
            ["description", "text"],
        ],
    ),
    DatabaseTelegramConversationView(
        "transfers",
        [
            ["date", "date"],
            ["sum", "float"],
            ["currency", "data", "currencies"],
            ["account_source", "data", "financial_accounts"],
            ["faccount_target", "data", "financial_accounts"],
            ["description", "text"],
        ],
    ),
    DatabaseTelegramConversationView(
        "financial_accounts",
        [
            ["name", "text"],
            ["number", "int"],
            ["operator", "data", "organizations"],
        ],
    ),
    DatabaseTelegramConversationView(
        "payment_cards",
        [
            ["name", "text"],
            ["number", "int"],
        ],
    ),
