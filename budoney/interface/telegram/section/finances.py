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
            ],
            ["expenses"],
            ["transfers"],
        ],
    )
    DatabaseTelegramConversationView(
        "income",
        [
            {"column": "date", "type": "date"},
            {"column": "sum", "type": "float", "aggregate": True},
            {"column": "currency", "type": "data", "data_type": "currencies"},
            {
                "column": "financial_account",
                "type": "data",
                "data_type": "financial_accounts",
            },
            {"column": "organization", "type": "data", "data_type": "organizations"},
            {"column": "description", "type": "text"},
        ],
    ),
    DatabaseTelegramConversationView(
        "expenses",
        [
            {"column": "date", "type": "date"},
            {"column": "sum", "type": "float", "aggregate": True},
            {"column": "currency", "type": "data", "data_type": "currencies"},
            {
                "column": "financial_account",
                "type": "data",
                "data_type": "financial_accounts",
            },
            {"column": "organization", "type": "data", "data_type": "organizations"},
            {"column": "description", "type": "text"},
        ],
    ),
    DatabaseTelegramConversationView(
        "transfers",
        [
            {"column": "date", "type": "date"},
            {"column": "sum", "type": "float", "aggregate": True},
            {"column": "currency", "type": "data", "data_type": "currencies"},
            {
                "column": "account_source",
                "type": "data",
                "data_type": "financial_accounts",
            },
            {
                "column": "account_target",
                "type": "data",
                "data_type": "financial_accounts",
            },
            {"column": "description", "type": "text"},
        ],
    ),
    DatabaseTelegramConversationView(
        "financial_accounts",
        [
            {"column": "name", "type": "text"},
            {"column": "number", "type": "int"},
            {"column": "operator", "type": "data", "data_type": "organizations"},
        ],
    ),
    DatabaseTelegramConversationView(
        "payment_cards",
        [
            {"column": "name", "type": "text"},
            {"column": "number", "type": "int"},
        ],
    ),
