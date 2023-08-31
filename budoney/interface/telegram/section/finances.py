from typing import Any
from datetime import datetime
from utils.simple_math import calculate
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

finance_format = "{:,.2f}"

financial_account_types = ["BANK", "CASH", "OTHER"]
select_emoji = {
    "financial_accounts": {
        "type": {
            "CASH": "💵",
            "BANK": "🏦",
            "OTHER": "💲",
        }
    }
}


def get_balance(account_id=None):
    query = f"SELECT c.code, COALESCE(ind.financial_account__type, inc.financial_account__type, ed.financial_account__type, ec.financial_account__type, tfd.account_source__type, tfc.account_source__type, ttd.account_target__type, ttc.account_target__type) AS type, ROUND(COALESCE(income_debit__sum, 0) - COALESCE(expenses_debit__sum, 0) - COALESCE(transfers_debit__sum_source, 0) + COALESCE(transfers_debit__sum_target, 0) + COALESCE(financial_accounts_debit_correction, 0), 2) AS balance, ROUND(COALESCE(income_credit__sum, 0) - COALESCE(expenses_credit__sum, 0) - COALESCE(transfers_credit__sum_source, 0) + COALESCE(transfers_credit__sum_target, 0) + COALESCE(financial_accounts_credit_correction, 0), 2) AS credit, ROUND(income_debit__sum, 2) AS income_debit, ROUND(income_credit__sum, 2) AS income_credit, ROUND(expenses_debit__sum, 2) AS expense_debit, ROUND(expenses_credit__sum, 2) AS expense_credit, ROUND(transfers_debit__sum_source, 2) AS transfer_debit_source, ROUND(transfers_credit__sum_source, 2) AS transfer_credit_source, ROUND(transfers_debit__sum_target, 2) AS transfer_debit_target, ROUND(transfers_credit__sum_target, 2) AS transfer_credit_target, ROUND(financial_accounts_debit_correction, 2) AS correction_debit, ROUND(financial_accounts_credit_correction, 2) AS correction_credit FROM currencies c LEFT JOIN ( SELECT 'BANK' AS operation_type UNION ALL SELECT 'CASH' AS operation_type UNION ALL SELECT 'OTHER' AS operation_type ) AS operation_types LEFT JOIN ( SELECT SUM(income.sum) AS income_debit__sum, financial_account.type AS financial_account__type, financial_account.currency AS financial_account__currency FROM income LEFT JOIN financial_accounts AS financial_account ON financial_account.id = income.financial_account WHERE financial_account.credit_limit = 0{account_id and ' AND financial_account.id = ?' or ''} GROUP BY financial_account__currency, financial_account__type ) ind ON ind.financial_account__currency = c.id AND ind.financial_account__type = operation_types.operation_type LEFT JOIN ( SELECT SUM(income.sum) AS income_credit__sum, financial_account.type AS financial_account__type, financial_account.currency AS financial_account__currency FROM income LEFT JOIN financial_accounts AS financial_account ON financial_account.id = income.financial_account WHERE financial_account.credit_limit != 0{account_id and ' AND financial_account.id = ?' or ''} GROUP BY financial_account__currency, financial_account__type ) inc ON inc.financial_account__currency = c.id AND inc.financial_account__type = operation_types.operation_type LEFT JOIN ( SELECT SUM(expenses.sum) AS expenses_debit__sum, financial_account.type AS financial_account__type, financial_account.currency AS financial_account__currency FROM expenses LEFT JOIN financial_accounts AS financial_account ON financial_account.id = expenses.financial_account WHERE financial_account.credit_limit = 0{account_id and ' AND financial_account.id = ?' or ''} GROUP BY financial_account__currency, financial_account__type ) ed ON ed.financial_account__currency = c.id AND ed.financial_account__type = operation_types.operation_type LEFT JOIN ( SELECT SUM(expenses.sum) AS expenses_credit__sum, financial_account.type AS financial_account__type, financial_account.currency AS financial_account__currency FROM expenses LEFT JOIN financial_accounts AS financial_account ON financial_account.id = expenses.financial_account WHERE financial_account.credit_limit != 0{account_id and ' AND financial_account.id = ?' or ''} GROUP BY financial_account__currency, financial_account__type ) ec ON ec.financial_account__currency = c.id AND ec.financial_account__type = operation_types.operation_type LEFT JOIN ( SELECT SUM(transfers.sum_source) AS transfers_debit__sum_source, account_source.type AS account_source__type, account_source.currency AS account_source__currency FROM transfers LEFT JOIN financial_accounts AS account_source ON account_source.id = transfers.account_source WHERE account_source.credit_limit = 0{account_id and ' AND account_source.id = ?' or ''} GROUP BY account_source__currency, account_source__type ) tfd ON tfd.account_source__currency = c.id AND tfd.account_source__type = operation_types.operation_type LEFT JOIN ( SELECT SUM(transfers.sum_source) AS transfers_credit__sum_source, account_source.type AS account_source__type, account_source.currency AS account_source__currency FROM transfers LEFT JOIN financial_accounts AS account_source ON account_source.id = transfers.account_source WHERE account_source.credit_limit != 0{account_id and ' AND account_source.id = ?' or ''} GROUP BY account_source__currency, account_source__type ) tfc ON tfc.account_source__currency = c.id AND tfc.account_source__type = operation_types.operation_type LEFT JOIN ( SELECT SUM(transfers.sum_target) AS transfers_debit__sum_target, account_target.type AS account_target__type, account_target.currency AS account_target__currency FROM transfers LEFT JOIN financial_accounts AS account_target ON account_target.id = transfers.account_target WHERE account_target.credit_limit = 0{account_id and ' AND account_target.id = ?' or ''} GROUP BY account_target__currency, account_target__type ) ttd ON ttd.account_target__currency = c.id AND ttd.account_target__type = operation_types.operation_type LEFT JOIN ( SELECT SUM(transfers.sum_target) AS transfers_credit__sum_target, account_target.type AS account_target__type, account_target.currency AS account_target__currency FROM transfers LEFT JOIN financial_accounts AS account_target ON account_target.id = transfers.account_target WHERE account_target.credit_limit != 0{account_id and ' AND account_target.id = ?' or ''} GROUP BY account_target__currency, account_target__type ) ttc ON ttc.account_target__currency = c.id AND ttc.account_target__type = operation_types.operation_type LEFT JOIN ( SELECT SUM(financial_accounts.correction) AS financial_accounts_debit_correction, financial_accounts.type AS financial_accounts__type, financial_accounts.currency AS financial_accounts__currency FROM financial_accounts WHERE financial_accounts.credit_limit = 0{account_id and ' AND financial_accounts.id = ?' or ''} GROUP BY financial_accounts__currency, financial_accounts__type ) fad ON fad.financial_accounts__currency = c.id AND fad.financial_accounts__type = operation_types.operation_type LEFT JOIN ( SELECT SUM(financial_accounts.correction) AS financial_accounts_credit_correction, financial_accounts.type AS financial_accounts__type, financial_accounts.currency AS financial_accounts__currency FROM financial_accounts WHERE financial_accounts.credit_limit != 0{account_id and ' AND financial_accounts.id = ?' or ''} GROUP BY financial_accounts__currency, financial_accounts__type ) fac ON fac.financial_accounts__currency = c.id AND fac.financial_accounts__type = operation_types.operation_type WHERE type IS NOT NULL AND ((balance) != 0 OR (credit) != 0) ORDER BY type, balance DESC"
    return DATABASE_DRIVER.get_data(
        query,
        account_id and ([account_id] * 10) or [],
    )


def _finances_balance_extra_info(record=None):
    balance = get_balance(
        account_id=(record and "id" in record and record["id"] or None)
    )
    if not balance:
        return ""
    lines = ["<b>Money balance</b>:"]
    last_type = ""

    money = []

    for row in balance:
        if row["type"] != last_type:
            if money:
                lines[-1] += (not record and ": " or "") + ", ".join(money)
            last_type = row["type"]
            lines.append(
                not record
                and f"{select_emoji['financial_accounts']['type'][row['type']]} {row['type']}"
                or ""
            )
            money = []

        if row["credit"] > 0:
            money.append(
                _sub_currency_display(
                    finance_format.format(row["balance"] + row["credit"]), row["code"]
                )
            )
        elif row["credit"] < 0:
            money.append(
                f"{_sub_currency_display(finance_format.format(row['balance']), row['code'])} and <b><u>{_sub_currency_display(finance_format.format(abs(row['credit'])), row['code'])} debt</u></b>"
            )
        else:
            money.append(
                _sub_currency_display(
                    finance_format.format(row["balance"]), row["code"]
                )
            )
    if money:
        lines[-1] += (not record and ": " or "") + ", ".join(money)

    return "\n".join(lines)


def _sub_currency_display(sum, currency_code):
    if currency_code == "USD":
        return f"${sum}"
    elif currency_code == "EUR":
        return f"€{sum}"
    elif currency_code == "GBP":
        return f"£{sum}"
    elif currency_code == "RUB":
        return f"{sum} ₽"
    elif currency_code == "KZT":
        return f"₸{sum}"
    return f"{sum} {currency_code}"


def _sub_organization_extended_display(record):
    organization_line = []
    if (
        "organization__category__emoji" in record
        and record["organization__category__emoji"]
    ):
        organization_line.append(record["organization__category__emoji"])

    if "organization__emoji" in record and record["organization__emoji"]:
        organization_line.append(record["organization__emoji"])

    if "organization__name" in record and record["organization__name"]:
        organization_line.append(record["organization__name"])

    if "description" in record and record["description"]:
        organization_line.append("(" + record["description"] + ")")

    if len(organization_line):
        return " ".join(organization_line)


def _sub_method_inline_display(record, account_prefix="", payment_card_prefix=""):
    if account_prefix:
        account_prefix = account_prefix + "__"

    method_line = []
    if (
        f"{account_prefix}owner__emoji" in record
        and record[f"{account_prefix}owner__emoji"]
    ):
        method_line.append(record[f"{account_prefix}owner__emoji"])

    if (
        f"{account_prefix}operator__emoji" in record
        and record[f"{account_prefix}operator__emoji"]
    ):
        method_line.append(record[f"{account_prefix}operator__emoji"])

    financial_account = []
    if f"{account_prefix}number" in record and record[f"{account_prefix}number"]:
        financial_account.append("*" + record[f"{account_prefix}number"])

    if f"{account_prefix}type" in record and record[f"{account_prefix}type"] == "CASH":
        financial_account.append("💵")
        financial_account.append(
            localization["states"].get(f"SELECT_account_type_CASH", "CASH")
        )

    if record.get(f"{account_prefix}credit_limit", 0) > 0:
        financial_account.append("Credit")

    if payment_card_prefix and (
        payment_card_prefix in record and record[payment_card_prefix]
    ):
        if payment_card_prefix:
            payment_card_prefix = payment_card_prefix + "__"
        method_line.append("💳")
        method_line.append("*" + record.get(f"{payment_card_prefix}number", "????"))

        method_line.append(record.get(f"{payment_card_prefix}payment_system", "????"))

        if record.get(f"{payment_card_prefix}credit_limit", 0) > 0:
            method_line.append("Credit")
    elif len(financial_account):
        method_line.append((" ".join(financial_account)))

    if len(method_line):
        return " ".join(method_line)


def _sub_method_extended_display(record, account_prefix="", payment_card_prefix=""):
    if account_prefix:
        account_prefix = account_prefix + "__"

    method_line = []
    if (
        f"{account_prefix}owner__emoji" in record
        and record[f"{account_prefix}owner__emoji"]
    ):
        method_line.append(record[f"{account_prefix}owner__emoji"])

    if (
        f"{account_prefix}operator__emoji" in record
        and record[f"{account_prefix}operator__emoji"]
    ):
        method_line.append(record[f"{account_prefix}operator__emoji"])

    if f"{account_prefix}type" in record and record[f"{account_prefix}type"] == "CASH":
        method_line.append("💵")

    financial_account = []
    if f"{account_prefix}number" in record and record[f"{account_prefix}number"]:
        financial_account.append("*" + record[f"{account_prefix}number"])

    if (
        f"{account_prefix}operator__name" in record
        and record[f"{account_prefix}operator__name"]
    ):
        financial_account.append(record[f"{account_prefix}operator__name"])

    if not len(financial_account):
        financial_account.append(
            localization["states"].get(f"SELECT_account_type_CASH", "CASH")
        )

    if record.get(f"{account_prefix}credit_limit", 0) > 0:
        financial_account.append("Credit")

    if payment_card_prefix and (
        payment_card_prefix in record and record[payment_card_prefix]
    ):
        if payment_card_prefix:
            payment_card_prefix = payment_card_prefix + "__"
        method_line.append("💳")
        method_line.append(
            "*" + record.get(f"{payment_card_prefix}number", "????")
        )

        method_line.append(
            record.get(f"{payment_card_prefix}payment_system", "????")
        )

        if record.get(f"{payment_card_prefix}credit_limit", 0) > 0:
            method_line.append("<b>Credit</b>")

        if len(financial_account):
            method_line.append("(" + (" ".join(financial_account)) + ")")
    elif len(financial_account):
        method_line.append(" ".join(financial_account))

    if len(method_line):
        return " ".join(method_line)


def _sub_date_extended_display(record):
    date_line = []
    if "date" in record and record["date"]:
        date_line.append("🗓")
        date = datetime.fromtimestamp(record["date"])
        date_line.append(date.strftime("%Y-%m-%d, %A"))
        date_line.append("(" + date_utils.get_relative_date_text(date) + ")")

    if len(date_line):
        return " ".join(date_line)


def _db_transactions_inline_display(record):
    text_parts = []

    if "date" in record and record["date"]:
        text_parts.append(date_utils.get_relative_timestamp_text(record["date"]))
        text_parts.append("—")

    text_parts.append(
        _sub_currency_display(
            finance_format.format(record.get("sum", 0)),
            record.get("financial_account__currency__code", "XXX"),
        )
    )

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

    method_part = _sub_method_inline_display(
        record, "financial_account", "payment_card"
    )
    if method_part:
        text_parts.append(method_part)

    return " ".join(text_parts)


def _db_income_extended_display(record):
    text_parts = []

    text_parts.append(
        f"<b><u>INCOME</u></b> — <b>{_sub_currency_display(finance_format.format(record.get('sum', 0)), record.get('financial_account__currency__code', 'XXX'))}</b>"
    )

    organization_line = _sub_organization_extended_display(record)
    if organization_line:
        text_parts.append(organization_line)

    method_line = _sub_method_extended_display(record, "financial_account")
    if method_line:
        text_parts.append(method_line)

    date_line = _sub_date_extended_display(record)
    if date_line:
        text_parts.append(date_line)

    return "\n".join(text_parts)


def _db_income_report_display(text, data: list[dict[str, Any]]) -> str:
    if not data:
        return ""
    lines = [text]
    for row in data:
        line_text = f"<b>{_sub_currency_display(finance_format.format(row['received']), row['financial_account__currency__code'])}</b>"
        if row["proxy"]:
            line_text = f"{line_text} + {_sub_currency_display(finance_format.format(row['proxy']), row['financial_account__currency__code'])} proxy"
        lines.append(line_text)
    return "\n".join(lines)


def _db_income_report_local_display(data: list[dict[str, Any]]) -> str:
    return _db_income_report_display("<b>Income</b> in this query:", data)


def _db_income_report_foreign_display(data: list[dict[str, Any]]) -> str:
    return _db_income_report_display("<b>Income</b> this month:", data)


def _db_expenses_extended_display(record):
    text_parts = []

    text_parts.append(
        f"<b><u>EXPENSE</u></b> — <b>{_sub_currency_display(finance_format.format(record.get('sum', 0)), record.get('financial_account__currency__code', 'XXX'))}</b>"
    )

    organization_line = _sub_organization_extended_display(record)
    if organization_line:
        text_parts.append(organization_line)

    method_line = _sub_method_extended_display(
        record, "financial_account", "payment_card"
    )
    if method_line:
        text_parts.append(method_line)

    date_line = _sub_date_extended_display(record)
    if date_line:
        text_parts.append(date_line)

    return "\n".join(text_parts)


def _db_expenses_fast_type_processor(
    data: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    record = {}
    record_filters_pre: dict[str, list[str]] = {}
    record_filters: dict[str, str] = {}

    pairs = {
        "organizations": "organization",
        "payment_cards": "payment_card",
        "financial_accounts": "financial_account",
    }

    splitted_data = data.split(", ")
    record["sum"] = calculate(splitted_data[0])
    record["proxy"] = 0

    if len(splitted_data) > 1:
        splitted_data = splitted_data[1:]
        rows = DATABASE_DRIVER.search(
            ["organizations", "payment_cards", "financial_accounts"], splitted_data
        )
        for row in rows:
            if row["table_name"] not in record_filters_pre:
                record_filters_pre[pairs[row["table_name"]]] = []
            record_filters_pre[pairs[row["table_name"]]].append(row["entry_id"])

        for record_filter in record_filters_pre:
            if len(record_filters_pre[record_filter]) > 1:
                record_filters[
                    record_filter
                ] = f"{record_filter} IN ({', '.join(record_filters_pre[record_filter])})"
                print(record_filter, record_filters[record_filter])
            else:
                record[record_filter] = int(record_filters_pre[record_filter][0])

    return (record, record_filters)


def _db_expenses_report_display(text, data: list[dict[str, Any]]) -> str:
    if not data:
        return ""
    lines = [text]
    for row in data:
        line_text = f"<b>{_sub_currency_display(finance_format.format(row['spent']), row['financial_account__currency__code'])}</b>"
        if row["proxy"]:
            line_text = f"{line_text} + {_sub_currency_display(finance_format.format(row['proxy']), row['financial_account__currency__code'])} proxy"
        lines.append(line_text)
    return "\n".join(lines)


def _db_expenses_report_local_display(data: list[dict[str, Any]]) -> str:
    return _db_expenses_report_display("<b>Expenses</b> in this query:", data)


def _db_expenses_report_foreign_display(data: list[dict[str, Any]]) -> str:
    return _db_expenses_report_display("<b>Expenses</b> this month:", data)


def _db_transfers_inline_display(record):
    text_parts = []

    if "date" in record and record["date"]:
        text_parts.append(date_utils.get_relative_timestamp_text(record["date"]))
        text_parts.append("—")

    sum_present = (
        "sum_source" in record
        and record["sum_source"]
        and "sum_target" in record
        and record["sum_target"]
    )
    account_present = (
        "account_source" in record
        and record["account_source"]
        and "account_target" in record
        and record["account_target"]
    )

    if sum_present and record["sum_source"] == record["sum_target"]:
        text_parts.append(
            _sub_currency_display(
                record["sum_source"], record["account_source__currency__code"]
            )
        )
        text_parts.append("—")

    for account in ["source", "target"]:
        if (
            account_present
            and sum_present
            and record["sum_source"] != record["sum_target"]
        ):
            text_parts.append(
                _sub_currency_display(
                    record["sum_" + account],
                    record["account_" + account + "__currency__code"],
                )
            )
        if account_present:
            text_parts.append(_sub_method_inline_display(record, "account_" + account))
        if account == "source":
            text_parts.append(">")

    return " ".join(text_parts)


def _db_transfers_extended_display(record):
    text_parts = []

    text_parts.append(f"<b><u>TRANSFER</u></b>")

    sum_present = (
        "sum_source" in record
        and record["sum_source"]
        and "sum_target" in record
        and record["sum_target"]
    )
    account_present = (
        "account_source" in record
        and record["account_source"]
        and "account_target" in record
        and record["account_target"]
    )

    if account_present and sum_present:
        for account in ["source", "target"]:
            method_line = f"{account == 'source' and '⬅️' or '➡️'} [{record['sum_' + account]} {record['account_' + account + '__currency__code']}] {_sub_method_extended_display(record, 'account_' + account)}"
            if method_line:
                text_parts.append(method_line)

        if record["account_source__currency"] != record["account_target__currency"]:
            conversion_text = "💱 "
            if record["sum_source"] > record["sum_target"]:
                conversion_text += f"{round(record['sum_source'] / record['sum_target'], 2)} {record['account_source__currency__code']}/{record['account_target__currency__code']}"
            elif record["sum_source"] < record["sum_target"]:
                conversion_text += f"{round(record['sum_target'] / record['sum_source'], 2)} {record['account_target__currency__code']}/{record['account_source__currency__code']}"
            else:
                conversion_text += "Par"
            text_parts.append(conversion_text)
        elif record["sum_source"] != record["sum_target"]:
            if record["sum_source"] > record["sum_target"]:
                text_parts.append(
                    f"🤑 {_sub_currency_display(round(record['sum_source']-record['sum_target'], 2), record['account_source__currency__code'])} ({round((record['sum_source'] / record['sum_target'] - 1)*100, 2)}%)"
                )

    date_line = _sub_date_extended_display(record)
    if date_line:
        text_parts.append(date_line)

    if "description" in record and record["description"]:
        text_parts.append("🗒 " + record["description"])

    return "\n".join(text_parts)


def _db_financial_accounts_inline_display(record):
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

    if record.get("credit_limit", 0) > 0:
        text_parts_account.append("Credit")

    text_parts_account.append(record.get("currency__code", "XXX"))

    if name:
        text_parts.append(name)
        text_parts.append("(" + (" ".join(text_parts_account)) + ")")
    else:
        text_parts += text_parts_account

    return " ".join(text_parts)


def _db_payment_cards_inline_display(record):
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

    if record.get("financial_account__credit_limit", 0) > 0:
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
            ["transfers"],
        ],
        extra_info=[_finances_balance_extra_info],
    )
    DatabaseView(
        "currencies",
        [
            {"column": "name", "type": "text"},
            {"column": "code", "type": "text"},
            {"column": "emoji", "type": "text"},
        ],
        inline_display=lambda record: f"{record.get('emoji', '') or ''}{record.get('code', '???')}: {record.get('name', 'Unnamed currency')}",
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
            },
            {"column": "sum", "type": "float"},
            {"column": "proxy", "type": "float", "skippable": True},
            {"column": "description", "type": "text", "skippable": True},
        ],
        inline_display=_db_transactions_inline_display,
        extended_display=_db_income_extended_display,
        fast_type_processor=_db_expenses_fast_type_processor,
        order_by=[("date", True, None)],
        report=DatabaseReport(
            select=[
                ("received", "SUM(sum)-COALESCE(SUM(proxy), 0)"),
                ("proxy", "COALESCE(SUM(proxy), 0)"),
                ("financial_account__currency__code", None),
            ],
            group_by=["financial_account__currency"],
            order_by=[
                ("financial_account__currency", False, None),
                ("received", True, None),
            ],
            local_display=_db_income_report_local_display,
            foreign_display=_db_income_report_foreign_display,
            layer_display=lambda x: x,
            foreign_date="date",
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
            },
            {"column": "sum", "type": "float"},
            {"column": "proxy", "type": "float", "skippable": True},
            {"column": "description", "type": "text", "skippable": True},
        ],
        inline_display=_db_transactions_inline_display,
        extended_display=_db_expenses_extended_display,
        fast_type_processor=_db_expenses_fast_type_processor,
        order_by=[("date", True, None)],
        report=DatabaseReport(
            select=[
                ("spent", "SUM(sum)-COALESCE(SUM(proxy), 0)"),
                ("proxy", "COALESCE(SUM(proxy), 0)"),
                ("financial_account__currency__code", None),
            ],
            group_by=["financial_account__currency"],
            order_by=[
                ("financial_account__currency", False, None),
                ("spent", True, None),
            ],
            local_display=_db_expenses_report_local_display,
            foreign_display=_db_expenses_report_foreign_display,
            layer_display=lambda x: x,
            foreign_date="date",
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
            {"column": "description", "type": "text", "skippable": True},
        ],
        order_by=[("date", True, None)],
        inline_display=_db_transfers_inline_display,
        extended_display=_db_transfers_extended_display,
    )
    DatabaseView(
        "financial_categories",
        [
            {"column": "name", "type": "text"},
            {"column": "emoji", "type": "text", "skippable": True},
        ],
        inline_display=lambda record: f"{record.get('emoji', '') or ''}{record.get('name', 'Unnamed category')}",
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
                "select_key": "account_type",
            },
            {"column": "credit_limit", "type": "float"},
            {
                "column": "owner",
                "type": "data",
                "data_type": "people",
                "skippable": True,
            },
            {
                "column": "correction",
                "type": "float",
                "skippable": True,
            },
        ],
        inline_display=_db_financial_accounts_inline_display,
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
        extra_info=[_finances_balance_extra_info],
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
        inline_display=_db_payment_cards_inline_display,
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
