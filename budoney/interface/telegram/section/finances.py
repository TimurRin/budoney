from interface.telegram.classes import (
    DefaultTelegramConversationView,
    DatabaseTelegramConversationView,
)
from loc import localization


def _display_inline_financial_account(record):
    text_parts = []

    owner_emoji = record.get("owner_emoji", "")
    if owner_emoji:
        text_parts.append(owner_emoji)

    operator_emoji = record.get("operator_emoji", "")
    if operator_emoji:
        text_parts.append(operator_emoji)

    text_parts.append(record.get("operator_name", "XXX"))

    text_parts.append(record.get("currency_code", "XXX"))

    text_parts.append("*" + record.get("number", "????"))

    if record.get("credit", "0") == "1":
        text_parts.append("Credit")

    name = record.get("name", "")
    if name:
        text_parts.append("(" + name + ")")

    print(" ".join(text_parts))

    return " ".join(text_parts)


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
        lambda record: f"{record.get('code', '???')}: {record.get('name', 'Unnamed currency')}",
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
            {"column": "name", "type": "text", "skippable": True},
            {"column": "number", "type": "text"},
            {
                "column": "operator",
                "type": "data",
                "data_type": "organizations",
            },
            {
                "column": "type",
                "type": "select",
                "select": ["BANK", "SIM"],
            },
            {"column": "currency", "type": "data", "data_type": "currencies"},
            {"column": "credit", "type": "boolean"},
            {"column": "owner", "type": "data", "data_type": "people"},
        ],
        _display_inline_financial_account,
    ),
    DatabaseTelegramConversationView(
        "payment_cards",
        [
            {"column": "number", "type": "int"},
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
            },
        ],
        lambda record: f"*{record.get('number', '????')} {record.get('payment_system', '???')}",
    ),
