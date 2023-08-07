from typing import Any
from datetime import datetime

from regex import D
import configs
from interface.telegram.classes import (
    DatabaseLinkedReport,
    DatabaseReport,
    DefaultView,
    DatabaseView,
)
from loc import localization
import utils.date_utils as date_utils


select_emoji = {
    "financial_accounts": {
        "type": {
            "CASH": "💵",
            "BANK": "🏦",
            "SIM": "📱",
        }
    }
}


def _display_inline_transaction(record):
    text_parts = []

    if "date" in record and record["date"]:
        text_parts.append(date_utils.get_relative_timestamp(record["date"]))
        text_parts.append("—")

    text_parts.append(str(record.get("sum", 0)))
    text_parts.append(record.get("financial_account__currency__code", "XXX"))

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


def _display_full_income(record):
    text_parts = []

    text_parts.append(
        f"<b><u>INCOME</u></b> — <b>{str(record.get('sum', 0))}</b> {record.get('financial_account__currency__code', 'XXX')}"
    )

    organization_line = []
    if (
        "organization__category__emoji" in record
        and record["organization__category__emoji"]
    ):
        organization_line.append(record["organization__category__emoji"])

    if "organization__emoji" in record and record["organization__emoji"]:
        organization_line.append(record["organization__emoji"])

    if "organization__name" in record and record["organization__name"]:
        organization_line.append("<b>" + record["organization__name"] + "</b>")

    if "description" in record and record["description"]:
        organization_line.append("(" + record["description"] + ")")

    if len(organization_line):
        text_parts.append(" ".join(organization_line))

    method_line = []
    if (
        "financial_account__owner__emoji" in record
        and record["financial_account__owner__emoji"]
    ):
        method_line.append(record["financial_account__owner__emoji"])

    if (
        "financial_account__operator__emoji" in record
        and record["financial_account__operator__emoji"]
    ):
        method_line.append(record["financial_account__operator__emoji"])

    financial_account = []
    if "financial_account__number" in record and record["financial_account__number"]:
        financial_account.append("*" + record["financial_account__number"])

    if (
        "financial_account__operator__name" in record
        and record["financial_account__operator__name"]
    ):
        financial_account.append(record["financial_account__operator__name"])

    if record.get("financial_account__credit", 0) == 1:
        financial_account.append("Credit")

    if len(financial_account):
        method_line.append("<b>" + (" ".join(financial_account)) + "</b>")

    if len(method_line):
        text_parts.append(" ".join(method_line))

    date_line = []
    if "date" in record and record["date"]:
        date_line.append("🗓")
        date = datetime.fromtimestamp(record["date"])
        date_line.append("<b>" + date.strftime("%Y-%m-%d, %A") + "</b>")
        date_line.append("(" + date_utils.get_relative_date(date) + ")")

    if len(date_line):
        text_parts.append(" ".join(date_line))

    return "\n".join(text_parts)


def _display_full_expense(record):
    text_parts = []

    text_parts.append(
        f"<b><u>EXPENSE</u></b> — <b>{str(record.get('sum', 0))}</b> {record.get('financial_account__currency__code', 'XXX')}"
    )

    organization_line = []
    if (
        "organization__category__emoji" in record
        and record["organization__category__emoji"]
    ):
        organization_line.append(record["organization__category__emoji"])

    if "organization__emoji" in record and record["organization__emoji"]:
        organization_line.append(record["organization__emoji"])

    if "organization__name" in record and record["organization__name"]:
        organization_line.append("<b>" + record["organization__name"] + "</b>")

    if "description" in record and record["description"]:
        organization_line.append("(" + record["description"] + ")")

    if len(organization_line):
        text_parts.append(" ".join(organization_line))

    method_line = []
    if (
        "financial_account__owner__emoji" in record
        and record["financial_account__owner__emoji"]
    ):
        method_line.append(record["financial_account__owner__emoji"])

    if (
        "payment_card__financial_account__operator__emoji" in record
        and record["payment_card__financial_account__operator__emoji"]
    ):
        method_line.append(record["payment_card__financial_account__operator__emoji"])

    financial_account = []
    if "financial_account__number" in record and record["financial_account__number"]:
        financial_account.append("*" + record["financial_account__number"])

    if (
        "financial_account__operator__name" in record
        and record["financial_account__operator__name"]
    ):
        financial_account.append(record["financial_account__operator__name"])

    if record.get("financial_account__credit", 0) == 1:
        financial_account.append("Credit")

    if "payment_card" in record and record["payment_card"]:
        method_line.append("💳")
        method_line.append("<b>*" + record.get("payment_card__number", "????") + "</b>")

        method_line.append(
            "<b>" + record.get("payment_card__payment_system", "????") + "</b>"
        )

        if record.get("payment_card__financial_account__credit", 0) == 1:
            method_line.append("<b>Credit</b>")

        if len(financial_account):
            method_line.append("(" + (" ".join(financial_account)) + ")")
    elif len(financial_account):
        method_line.append("<b>" + (" ".join(financial_account)) + "</b>")

    if len(method_line):
        text_parts.append(" ".join(method_line))

    date_line = []
    if "date" in record and record["date"]:
        date_line.append("🗓")
        date = datetime.fromtimestamp(record["date"])
        date_line.append("<b>" + date.strftime("%Y-%m-%d, %A") + "</b>")
        date_line.append("(" + date_utils.get_relative_date(date) + ")")

    if len(date_line):
        text_parts.append(" ".join(date_line))

    return "\n".join(text_parts)


def _fast_type_expense(data: str) -> tuple[dict[str, Any], dict[str, Any]]:
    record = {}
    record_extra = {}
    record["sum"] = float(data)
    record_extra["currency"] = configs.general["main_currency"]
    return (record, record_extra)


def _display_record_income(data: list[dict[str, Any]]) -> str:
    if not data:
        return "No income to show"
    lines = ["<b>Income report</b>"]
    for row in data:
        lines.append(
            f"<b>{row['sum']}</b> {row['financial_account__currency__code']} ({row['financial_account__type']})"
        )
    return "\n".join(lines)


def _display_record_expense(data: list[dict[str, Any]]) -> str:
    if not data:
        return "No expenses to show"
    lines = ["<b>Expenses report</b>"]
    for row in data:
        lines.append(
            f"<b>{row['sum']}</b> {row['financial_account__currency__code']} ({row['financial_account__type']})"
        )
    return "\n".join(lines)


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

    if name:
        text_parts.append(name)
        text_parts.append("(" + (" ".join(text_parts_account)) + ")")
    else:
        text_parts += text_parts_account

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

    if record.get("financial_account__credit", 0) == 1:
        text_parts.append("Credit")

    if "financial_account__name" in record and record["financial_account__name"]:
        text_parts.append("(" + record["financial_account__name"] + ")")
    elif (
        "financial_account__number" in record
        and record["financial_account__number"]
        and "financial_account__operator__name" in record
        and record["financial_account__operator__name"]
    ):
        text_parts.append(
            "(*"
            + record["financial_account__number"]
            + " "
            + record["financial_account__operator__name"]
            + ")"
        )
    elif "financial_account__number" in record and record["financial_account__number"]:
        text_parts.append("(*" + record["financial_account__number"] + ")")
    elif (
        "financial_account__operator__name" in record
        and record["financial_account__operator__name"]
    ):
        text_parts.append("(" + record["financial_account__operator__name"] + ")")

    return " ".join(text_parts)


def init():
    DefaultView(
        "finances",
        [
            [
                "financial_categories",
                "currencies",
            ],
            [
                "financial_accounts",
                "payment_cards",
            ],
            ["income", "expenses", "transfers"],
        ],
    )
    DatabaseView(
        "currencies",
        [
            {"column": "name", "type": "text"},
            {"column": "code", "type": "text"},
            {"column": "emoji", "type": "text"},
        ],
        display_inline_func=lambda record: f"{record.get('emoji', '') or ''}{record.get('code', '???')}: {record.get('name', 'Unnamed currency')}",
        report_links=[
            DatabaseLinkedReport("income", "financial_account__currency"),
            DatabaseLinkedReport("expenses", "financial_account__currency"),
        ],
    )
    DatabaseView(
        "income",
        [
            {"column": "date", "type": "date"},
            {"column": "organization", "type": "data", "data_type": "organizations"},
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
            {"column": "sum", "type": "float"},
            {"column": "description", "type": "text", "skippable": True},
        ],
        display_inline_func=_display_inline_transaction,
        display_full_func=_display_full_income,
        fast_type_processor=_fast_type_expense,
        order_by=[("date", True, None), ("organization__name", False, None)],
        report=DatabaseReport(
            select=[
                ("sum", "ROUND(SUM(sum))"),
                ("financial_account__type", None),
                ("financial_account__currency__code", None),
            ],
            group_by=["financial_account__currency", "financial_account__type"],
            order_by=[
                ("financial_account__currency", False, None),
                ("sum", True, None),
            ],
            display_record_func=_display_record_income,
            display_layer_func=lambda x: x,
            # date="date",
        ),
    )
    DatabaseView(
        "expenses",
        [
            {"column": "date", "type": "date"},
            {"column": "organization", "type": "data", "data_type": "organizations"},
            {
                "column": "payment_card",
                "type": "data",
                "data_type": "payment_cards",
                "set": [
                    {
                        "column": "financial_account",
                        "from": "payment_card__financial_account",
                    }
                ],
                "skippable": "checking",
            },
            {
                "column": "financial_account",
                "type": "data",
                "data_type": "financial_accounts",
                "conditions": [
                    {
                        "type": "equals_if_set",
                        "column": "currency",
                        "extra": "currency",
                    }
                ],
            },
            {"column": "sum", "type": "float"},
            {"column": "description", "type": "text", "skippable": True},
        ],
        display_inline_func=_display_inline_transaction,
        display_full_func=_display_full_expense,
        fast_type_processor=_fast_type_expense,
        order_by=[("date", True, None), ("organization__name", False, None)],
        report=DatabaseReport(
            select=[
                ("sum", "ROUND(SUM(sum))"),
                ("financial_account__type", None),
                ("financial_account__currency__code", None),
            ],
            group_by=["financial_account__currency", "financial_account__type"],
            order_by=[
                ("financial_account__currency", False, None),
                ("sum", True, None),
            ],
            display_record_func=_display_record_expense,
            display_layer_func=lambda x: x,
            # date="date",
        ),
    )
    DatabaseView(
        "transfers",
        [
            {"column": "date", "type": "date"},
            {
                "column": "account_source",
                "type": "data",
                "data_type": "financial_accounts",
            },
            {"column": "sum_source", "type": "float"},
            {
                "column": "account_target",
                "type": "data",
                "data_type": "financial_accounts",
            },
            {"column": "sum_target", "type": "float"},
            {"column": "comission", "type": "float"},
            {"column": "description", "type": "text", "skippable": True},
        ],
        order_by=[("date", True, None)],
    )
    DatabaseView(
        "financial_categories",
        [
            {"column": "name", "type": "text"},
            {"column": "emoji", "type": "text", "skippable": True},
        ],
        display_inline_func=lambda record: f"{record.get('emoji', '') or ''}{record.get('name', 'Unnamed category')}",
        order_by=[("name", False, None)],
        report_links=[
            DatabaseLinkedReport("income", "organization__category"),
            DatabaseLinkedReport("expenses", "organization__category"),
        ],
    )
    DatabaseView(
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
                "select": ["CASH", "BANK", "SIM"],
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
        display_inline_func=_display_inline_financial_account,
        order_by=[
            ("type", False, None),
            ("operator__name", False, None),
            ("owner__name", False, None),
            ("name", False, None),
            ("number", False, None),
        ],
        report_links=[
            DatabaseLinkedReport("income", "financial_account"),
            DatabaseLinkedReport("expenses", "financial_account"),
        ],
    )
    DatabaseView(
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
        display_inline_func=_display_inline_payment_card,
        order_by=[
            ("financial_account__operator__name", False, None),
            ("financial_account__owner__name", False, None),
            ("financial_account", False, None),
            ("financial_account__name", False, None),
            ("number", False, None),
        ],
        report_links=[
            DatabaseLinkedReport("expenses", "payment_card"),
        ],
    )
