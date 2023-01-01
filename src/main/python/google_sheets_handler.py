import string
from datetime import datetime

import gspread
import utils.date_utils as date_utils
import utils.transliterate as transliterate
import utils.yaml_manager as yaml_manager
from gspread import Client, Spreadsheet, Worksheet
from oauth2client.service_account import ServiceAccountCredentials

print_label = "[google_sheets_handler]"

sheet_types = [
    "users",
    "categories",
    "methods",
    "merchants",
    "currencies",
    "tasks_current",
    "tasks_scheduled",
]

print(print_label, "Loading configs")
general_config = yaml_manager.load("config/local/general")
google_sheets_config = yaml_manager.load("config/local/google-sheets")

print(print_label, "Setting scope to use when authenticating")
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

print(print_label, "Authenticating using credentials, saved in JSON")
google_sheets_credentials = ServiceAccountCredentials.from_json_keyfile_name(
    "../../../config/local/google-api.json", scope
)

gspread_client = None
book_cache = {}
books_by_sheet = {}
sheets = {"transactions": {}}
data = {"transactions": {}}

cached_data = {}


def check_authorization(gspread_client: Client):
    if gspread_client:
        return gspread_client
    else:
        print(print_label, "Authorizing Google client")
        return gspread.authorize(google_sheets_credentials)


def fetch_sheet(name: string):
    global gspread_client
    gspread_client = check_authorization(gspread_client)
    print(print_label, "Opening the sheet '" + name + "'")
    sheet_credentials = google_sheets_config["sheets"][name]
    if sheet_credentials["bookKey"] not in book_cache:
        book_cache[sheet_credentials["bookKey"]] = gspread_client.open_by_key(
            sheet_credentials["bookKey"]
        )
    books_by_sheet[name] = book_cache[sheet_credentials["bookKey"]]
    return books_by_sheet[name].get_worksheet_by_id(sheet_credentials["sheetId"])


def fetch_transaction_sheet(transaction_code: str):
    global gspread_client
    gspread_client = check_authorization(gspread_client)
    print(print_label, "Opening the transaction sheet '" + transaction_code + "'")
    sheet_credentials = google_sheets_config["sheets"]["transactions"]
    sheet_name = sheet_credentials["sheetPrefix"] + transaction_code
    if sheet_credentials["bookKey"] not in book_cache:
        book_cache[sheet_credentials["bookKey"]] = gspread_client.open_by_key(
            sheet_credentials["bookKey"]
        )
    books_by_sheet[transaction_code] = book_cache[sheet_credentials["bookKey"]]
    return books_by_sheet[transaction_code].worksheet(sheet_name)


def fetch_data(name: str, sheet: Worksheet):
    print(
        print_label,
        "Getting data from the sheet '"
        + name
        + "' ("
        + str(sheet.title)
        + ", "
        + str(sheet.id)
        + ")",
    )

    if name == "categories":
        data = {"dict": {}, "list": []}
        for value in sheet.get_values()[1:]:
            entry = {"id": value[0], "name": value[1], "emoji": value[2]}
            data["dict"][value[0]] = entry
            data["list"].append(value[0])
        return data
    elif name == "merchants":
        data = {
            "dict": {},
            "list": [],
            "keywords": {
                "dict": {},
                "list": [],
            },
            "by_category": {},
        }
        for value in sheet.get_values()[1:]:
            category: str = value[3]

            entry = {
                "id": value[0],
                "name": value[1],
                "category": category,
                "emoji": value[4],
            }
            data["dict"][value[0]] = entry
            data["list"].append(value[0])

            if not category in data["by_category"]:
                data["by_category"][category] = []
            data["by_category"][category].append(value[0])

            keywords_to_add = [
                value[0].casefold(),
                value[1].casefold(),
                transliterate.russian_to_latin(value[1].casefold()),
            ]

            for keyword in value[2].split(","):
                keywords_to_add.append(keyword.casefold())
                keywords_to_add.append(
                    transliterate.russian_to_latin(keyword.casefold())
                )

            for keyword in keywords_to_add:
                if keyword and keyword not in data["keywords"]["dict"]:
                    data["keywords"]["list"].append(keyword)
                    data["keywords"]["dict"][keyword] = value[0]
        return data
    elif name == "methods":
        data = {"dict": {}, "list": []}
        for value in sheet.get_values()[1:]:
            entry = {
                "id": value[0],
                "name": value[1],
                "emoji": value[2],
                "is_account": value[3] == "TRUE" and True or False,
                "is_mir": value[4] == "TRUE" and True or False,
                "is_credit": value[5] == "TRUE" and True or False,
                "is_cashback": value[6] == "TRUE" and True or False,
                "owner": value[7],
            }
            data["dict"][value[0]] = entry
            data["list"].append(value[0])
        return data
    elif name == "currencies" or name == "users":
        data = {"dict": {}, "list": []}
        for value in sheet.get_values()[1:]:
            entry = {
                "id": value[0],
                "name": value[1],
                "emoji": value[2],
            }
            data["dict"][value[0]] = entry
            data["list"].append(value[0])
        return data
    elif name == "tasks_current":
        data = {"dict": {}, "list": []}
        for value in sheet.get_values()[1:]:
            entry = {
                "id": value[0],
                "name": value[1],
                "priority": value[2],
                "scheduled_id": value[3],
                "created": value[4],
                "due_to": value[5],
                "days_before": value[6],
                "done": value[7],
            }
            data["dict"][value[0]] = entry
            data["list"].append(value[0])
        return data
    elif name == "tasks_scheduled":
        data = {"dict": {}, "list": []}
        for value in sheet.get_values()[1:]:
            entry = {
                "id": value[0],
                "name": value[1],
                "priority": value[2],
                "recurring_type": value[3],
                "recurring_value": value[4],
                "recurring_stage": value[5],
                "recurring_timestamp": value[6],
                "times_done": value[7],
                "times_missed": value[8],
                "paused": value[9],
            }
            data["dict"][value[0]] = entry
            data["list"].append(value[0])
        return data
    elif name == "tasks_current":
        data = {"dict": {}, "list": []}
        for value in sheet.get_values()[1:]:
            entry = {
                "id": value[0],
                "name": value[1],
                "priority": value[2],
                "scheduled_id": value[3],
                "created": value[4],
                "due_to": value[5],
                "days_before": value[6],
                "done": value[7],
            }
            data["dict"][value[0]] = entry
            data["list"].append(value[0])
        return data
    elif name == "tasks_scheduled":
        data = {"dict": {}, "list": []}
        for value in sheet.get_values()[1:]:
            entry = {
                "id": value[0],
                "name": value[1],
                "priority": value[2],
                "recurring_type": value[3],
                "recurring_value": value[4],
                "recurring_stage": value[5],
                "recurring_timestamp": value[6],
                "times_done": value[7],
                "times_missed": value[8],
                "paused": value[9],
            }
            data["dict"][value[0]] = entry
            data["list"].append(value[0])
        return data
    else:
        return sheet.get_values()


def fetch_all_sheets():
    transactions = {}

    transactions_date = datetime.strptime(
        google_sheets_config["transactions_start"], "%Y-%m-%d"
    )
    for transaction_code in date_utils.monthly_codes_range(
        transactions_date, transactions_date.today()
    ):
        transactions[transaction_code] = fetch_transaction_sheet(transaction_code)

    return {
        "users": fetch_sheet("users"),
        "categories": fetch_sheet("categories"),
        "methods": fetch_sheet("methods"),
        "merchants": fetch_sheet("merchants"),
        "currencies": fetch_sheet("currencies"),
        "transactions": transactions,
        "tasks_current": fetch_sheet("tasks_current"),
        "tasks_scheduled": fetch_sheet("tasks_scheduled"),
    }


def fetch_all_data(requests):
    for sheet in requests:
        if sheet == "transactions":
            pass
            # for transaction_sheet in sheets["transactions"]:
            #     data["transactions"][transaction_sheet] = fetch_data(
            #         transaction_sheet, sheets["transactions"][transaction_sheet])
        else:
            if (sheet not in sheets) or (sheet not in cached_data):
                sheets[sheet] = fetch_sheet(sheet)
            if (sheet not in data) or (sheet not in cached_data):
                data[sheet] = fetch_data(sheet, sheets[sheet])
            cached_data[sheet] = True
    return data


def get_cached_data(requests):
    global data
    data = fetch_all_data(requests)
    return data


def insert_into_transaction_sheet(id: str, row: list):
    if id not in sheets["transactions"]:
        sheets["transactions"][id] = fetch_transaction_sheet(id)
    insert_into_sheet(sheets["transactions"][id], row)


def insert_into_sheet_name(name: str, row: list):
    insert_into_sheet(sheets[name], row)


def insert_into_sheet(sheet: Worksheet, row: list):
    sheet.append_row(row)


def invalidate_all():
    global cached_data
    cached_data = {}
    get_cached_data(sheet_types)


# cache data from the start
get_cached_data(not general_config["quiet_mode"] and sheet_types or [])
