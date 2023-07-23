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
            {"column": "currency", "type": "data", "data_type": "currencies"},
            {"column": "sum", "type": "float", "aggregate": True},
            {
                "column": "financial_account",
                "type": "data",
                "data_type": "financial_accounts",
                "conditions": [
                    {
                        "type": "equals",
                        "our_column": "currency",
                        "their_column": "currency",
                    }
                ],
            },
            {"column": "organization", "type": "data", "data_type": "organizations"},
            {"column": "description", "type": "text", "skippable": True},
        ],
    ),
    DatabaseTelegramConversationView(
        "expenses",
        [
            {"column": "date", "type": "date"},
            {"column": "currency", "type": "data", "data_type": "currencies"},
            {"column": "sum", "type": "float", "aggregate": True},
            {
                "column": "financial_account",
                "type": "data",
                "data_type": "financial_accounts",
                "conditions": [
                    {
                        "type": "equals",
                        "our_column": "currency",
                        "their_column": "currency",
                    }
                ],
            },
            {
                "column": "payment_card",
                "type": "data",
                "data_type": "payment_cards",
                "conditions": [
                    {
                        "type": "equals",
                        "our_column": "financial_account",
                        "their_column": "financial_account",
                    }
                ],
                "skippable": True,
            },
            {"column": "organization", "type": "data", "data_type": "organizations"},
            {"column": "description", "type": "text", "skippable": True},
        ],
    ),
    DatabaseTelegramConversationView(
        "transfers",
        [
            {"column": "date", "type": "date"},
            {"column": "currency_source", "type": "data", "data_type": "currencies"},
            {"column": "sum_source", "type": "float", "aggregate": True},
            {
                "column": "account_source",
                "type": "data",
                "data_type": "financial_accounts",
            },
            {
                "column": "currency_target",
                "type": "data",
                "data_type": "currencies",
                "skippable": True,
                "if_skipped": "currency_source",
            },
            {"column": "sum_target", "type": "float", "aggregate": True},
            {
                "column": "account_target",
                "type": "data",
                "data_type": "financial_accounts",
            },
            {"column": "description", "type": "text", "skippable": True},
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
            }
        ],
    ),
