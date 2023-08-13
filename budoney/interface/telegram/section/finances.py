from typing import Any
from datetime import datetime
from database import DATABASE_DRIVER
import configs
from interface.telegram.classes import (
    DatabaseLinkedReport,
    DatabaseReport,
    DefaultView,
    DatabaseView,
)
from loc import localization
import utils.date_utils as date_utils


financial_account_types = ["BANK", "CASH"]
select_emoji = {
    "financial_accounts": {
        "type": {
            "CASH": "💵",
            "BANK": "🏦",
        }
    }
}


def get_balance():
    query = "SELECT COALESCE(i.financial_account__type, e.financial_account__type, tf.account_source__type, tt.account_target__type) AS financial_account_type, GROUP_CONCAT(CAST((COALESCE(income__sum, 0) - COALESCE(expenses__sum, 0) - COALESCE(transfers__sum_source, 0) + COALESCE(transfers__sum_target, 0)) + COALESCE(correction__sum, 0) AS TEXT) || ' ' || c.code, ', ') AS balances FROM currencies c LEFT JOIN ( SELECT 'BANK' AS operation_type UNION ALL SELECT 'CASH' AS operation_type ) AS operation_types LEFT JOIN ( SELECT ROUND(SUM(income.sum)) AS income__sum, financial_account.type AS financial_account__type, financial_account.currency AS financial_account__currency FROM income LEFT JOIN financial_accounts AS financial_account ON financial_account.id = income.financial_account GROUP BY financial_account__currency, financial_account__type ) i ON i.financial_account__currency = c.id AND i.financial_account__type = operation_types.operation_type LEFT JOIN ( SELECT ROUND(SUM(expenses.sum)) AS expenses__sum, financial_account.type AS financial_account__type, financial_account.currency AS financial_account__currency FROM expenses LEFT JOIN financial_accounts AS financial_account ON financial_account.id = expenses.financial_account GROUP BY financial_account__currency, financial_account__type ) e ON e.financial_account__currency = c.id AND e.financial_account__type = operation_types.operation_type LEFT JOIN ( SELECT ROUND(SUM(transfers.sum_source)) AS transfers__sum_source, account_source.type AS account_source__type, account_source.currency AS account_source__currency, comission FROM transfers LEFT JOIN financial_accounts AS account_source ON account_source.id = transfers.account_source GROUP BY account_source__currency, account_source__type ) tf ON tf.account_source__currency = c.id AND tf.account_source__type = operation_types.operation_type LEFT JOIN ( SELECT ROUND(SUM(transfers.sum_target)) AS transfers__sum_target, account_target.type AS account_target__type, account_target.currency AS account_target__currency, comission FROM transfers LEFT JOIN financial_accounts AS account_target ON account_target.id = transfers.account_target GROUP BY account_target__currency, account_target__type ) tt ON tt.account_target__currency = c.id AND tt.account_target__type = operation_types.operation_type LEFT JOIN ( SELECT ROUND(SUM(sum)) AS correction__sum, corrections.account_type AS correction__account_type, corrections.currency AS correction__currency FROM corrections GROUP BY correction__currency, correction__account_type ) cor ON cor.correction__currency = c.id AND cor.correction__account_type = operation_types.operation_type WHERE financial_account_type IS NOT NULL AND (COALESCE(income__sum, 0) - COALESCE(expenses__sum, 0) - COALESCE(transfers__sum_source, 0) + COALESCE(transfers__sum_target, 0)) + COALESCE(correction__sum, 0) > 0 GROUP BY financial_account_type"
    return DATABASE_DRIVER.get_data(query, [])


def _extra_info_balance():
    balance = get_balance()
    if not balance:
        return ""
    lines = ["<b><u>Money balance</u></b>"]
    for row in balance:
        lines.append(
            f"{select_emoji['financial_accounts']['type'][row['financial_account_type']]} {row['financial_account_type']}: <b>{row['balances']}</b>"
        )
    return "\n".join(lines)


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
        return ""
    lines = ["<b>Income</b> this month:"]
    for row in data:
        lines.append(
            f"<b>{row['sum']}</b> {row['financial_account__currency__code']} ({row['financial_account__type']})"
        )
    return "\n".join(lines)


def _display_record_expense(data: list[dict[str, Any]]) -> str:
    if not data:
        return ""
    lines = ["<b>Expenses</b> this month:"]
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
            ["income", "expenses"],
            ["corrections", "transfers"],
        ],
        extra_info=[_extra_info_balance],
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
            date="date",
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
            date="date",
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
        "corrections",
        [
            {"column": "date", "type": "date"},
            {"column": "currency", "type": "data", "data_type": "currencies"},
            {
                "column": "account_type",
                "type": "select",
                "select": financial_account_types,
                "select_key": "account_type"
            },
            {"column": "sum", "type": "float"},
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
            {"column": "currency", "type": "data", "data_type": "currencies"},
            {
                "column": "type",
                "type": "select",
                "select": financial_account_types,
                "select_key": "account_type"
            },
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
