from interface.telegram.classes import (
    DefaultTelegramConversationView,
    DatabaseTelegramConversationView,
)


def init():
    DefaultTelegramConversationView(
        "finances",
        [
            [
                "currencies",
                "transactions",
            ],
            [
                "financial_accounts",
                "payment_cards",
            ],
        ],
    ),
    DatabaseTelegramConversationView(
        "currencies",
        [
            {"column": "name", "type": "text"},
            {"column": "code", "type": "text"},
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
            {
                "column": "payment_card",
                "type": "data",
                "data_type": "payment_cards",
                "conditions": [("specified", "financial_account")],
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
            {"column": "number", "type": "text", "id_composition": True},
            {
                "column": "operator",
                "type": "data",
                "data_type": "organizations",
                "id_composition": True,
            },
            {
                "column": "type",
                "type": "select",
                "select": ["BANK", "PHONE"],
            },
            {"column": "currency", "type": "data", "data_type": "currencies"},
            {"column": "credit", "type": "boolean"},
            {"column": "owner", "type": "data", "data_type": "people"},
        ],
    ),
    DatabaseTelegramConversationView(
        "payment_cards",
        [
            {"column": "name", "type": "text", "id_composition": True},
            {"column": "number", "type": "int", "id_composition": True},
            {
                "column": "financial_account",
                "type": "data",
                "data_type": "financial_accounts",
            },
            {
                "column": "payment_system",
                "type": "select",
                "select": [
                    "VISA",
                    "MASTERCARD",
                    "MAESTRO",
                    "AMERICAEXPRESS",
                    "MIR",
                    "UNIONPAY",
                ],
                "id_composition": True,
            },
            {"column": "owner", "type": "data", "data_type": "people"},
        ],
    ),
