from interface.telegram.classes import (
    DefaultTelegramConversationView,
    DatabaseTelegramConversationView,
)
from loc import localization
import utils.date_utils as date_utils


select_emoji = {
    "financial_accounts": {
        "type": {
            "CASH": "💵",
            "BANK": "🏦",
            "SIM": "📱",
            "WALLET": "👛",
        }
    }
}


def _display_inline_transaction(record):
    text_parts = []

    if "date" in record and record["date"]:
        text_parts.append(date_utils.get_relative_timestamp(record["date"]))
        text_parts.append("—")

    text_parts.append(str(record.get("sum", 0)))
    text_parts.append(record.get("currency__code", "XXX"))

    text_parts.append("—")

    if (
        "organization__category__emoji" in record
        and record["organization__category__emoji"]
    ):
        text_parts.append(record["organization__category__emoji"])

    if "organization__emoji" in record and record["organization__emoji"]:
        text_parts.append(record["organization__emoji"])

    if "organization__name" in record and record["organization__name"]:
        text_parts.append(record["organization__name"])

    text_parts.append("—")

    if (
        "financial_account__owner__emoji" in record
        and record["financial_account__owner__emoji"]
    ):
        text_parts.append(record["financial_account__owner__emoji"])

    if (
        "payment_card__financial_account__operator__emoji" in record
        and record["payment_card__financial_account__operator__emoji"]
    ):
        text_parts.append(record["payment_card__financial_account__operator__emoji"])

    if "payment_card" in record and record["payment_card"]:
        text_parts.append("💳")
        if "payment_card__number" in record and record["payment_card__number"]:
            text_parts.append("*" + record.get("payment_card__number", "????"))
    elif "financial_account__number" in record and record["financial_account__number"]:
        text_parts.append("*" + record.get("financial_account__number", "????"))

    return " ".join(text_parts)


def _display_inline_financial_account(record):
    text_parts = []

    name = "name" in record and record["name"]

    if "owner__emoji" in record and record["owner__emoji"]:
        text_parts.append(record["owner__emoji"])

    if "operator__emoji" in record and record["operator__emoji"]:
        text_parts.append(record["operator__emoji"])

    if (
        "type" in record
        and record["type"]
        and record["type"] in select_emoji["financial_accounts"]["type"]
    ):
        text_parts.append(select_emoji["financial_accounts"]["type"][record["type"]])

    text_parts_account = []

    if "number" in record and record["number"]:
        text_parts_account.append("*" + record["number"])

    if "operator__name" in record and record["operator__name"]:
        text_parts_account.append(record["operator__name"])

    if record.get("credit", 0) == 1:
        text_parts_account.append("Credit")

    text_parts_account.append(record.get("currency__code", "XXX"))

    if "name" in record and record["name"]:
        text_parts.append(record["name"])
        text_parts.append("(" + (" ".join(text_parts_account)) + ")")
    else:
        text_parts = text_parts_account

    return " ".join(text_parts)


def _display_inline_payment_card(record):
    text_parts = []

    if (
        "financial_account__owner__emoji" in record
        and record["financial_account__owner__emoji"]
    ):
        text_parts.append(record["financial_account__owner__emoji"])

    if (
        "financial_account__operator__emoji" in record
        and record["financial_account__operator__emoji"]
    ):
        text_parts.append(record["financial_account__operator__emoji"])

    text_parts.append("💳")

    text_parts.append("*" + record.get("number", "????"))

    text_parts.append(record.get("payment_system", "???"))

    if record.get("financial_account__credit", "0") == "1":
        text_parts.append("Credit")

    if "financial_account__name" in record and record["financial_account__name"]:
        text_parts.append("(" + record["financial_account__name"] + ")")
    elif "financial_account__number" in record and record["financial_account__number"]:
        text_parts.append("*" + record["financial_account__number"])
    elif (
        "financial_account__operator__name" in record
        and record["financial_account__operator__name"]
    ):
        text_parts.append(record["financial_account__operator__name"])

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
                "financial_categories",
                "financial_accounts",
                "payment_cards",
            ],
        ],
    )
    DatabaseTelegramConversationView(
        "currencies",
        [
            {"column": "name", "type": "text"},
            {"column": "code", "type": "text"},
            {"column": "emoji", "type": "text"},
        ],
        display_func=lambda record: f"{record.get('emoji', '') or ''}{record.get('code', '???')}: {record.get('name', 'Unnamed currency')}",
    )
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
        display_func=_display_inline_transaction,
        order_by=["date", "organization__name"],
    )
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
        display_func=_display_inline_transaction,
        order_by=["date", "organization__name"],
    )
    DatabaseTelegramConversationView(
        "transfers",
        [
            {"column": "date", "type": "date"},
            {"column": "sum_source", "type": "float", "aggregate": True},
            {
                "column": "account_source",
                "type": "data",
                "data_type": "financial_accounts",
            },
            {"column": "sum_target", "type": "float", "aggregate": True},
            {
                "column": "account_target",
                "type": "data",
                "data_type": "financial_accounts",
            },
            {"column": "comission", "type": "float"},
            {"column": "description", "type": "text", "skippable": True},
        ],
        order_by=["date"],
    )
    DatabaseTelegramConversationView(
        "financial_categories",
        [
            {"column": "name", "type": "text"},
            {"column": "emoji", "type": "text", "skippable": True},
        ],
        display_func=lambda record: f"{record.get('emoji', '') or ''}{record.get('name', 'Unnamed category')}",
        order_by=["Name"],
    )
    DatabaseTelegramConversationView(
        "financial_accounts",
        [
            {"column": "name", "type": "text", "skippable": True},
            {"column": "number", "type": "text", "skippable": True},
            {
                "column": "operator",
                "type": "data",
                "data_type": "organizations",
                "skippable": True,
            },
            {
                "column": "type",
                "type": "select",
                "select": ["CASH", "BANK", "SIM", "WALLET"],
            },
            {"column": "currency", "type": "data", "data_type": "currencies"},
            {"column": "credit", "type": "boolean"},
            {
                "column": "owner",
                "type": "data",
                "data_type": "people",
                "skippable": True,
            },
        ],
        display_func=_display_inline_financial_account,
        order_by=["type", "operator__name", "owner__name", "name", "number"],
    )
    DatabaseTelegramConversationView(
        "payment_cards",
        [
            {"column": "number", "type": "text"},
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
                    "AMEX",
                    "MIR",
                    "UNIONPAY",
                    "DINERS",
                ],
            },
        ],
        display_func=_display_inline_payment_card,
        order_by=[
            "financial_account__operator__name",
            "financial_account__owner__name",
            "payment_system",
            "number",
        ],
    )
