from datetime import datetime
import math

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

gspread_client: Client = None
book_cache: dict[str, Spreadsheet] = {}
books_by_sheet: dict[str, Spreadsheet] = {}
sheets: dict[str, Worksheet] = {}
data: dict = {}


def check_authorization(gspread_client: Client):
    if gspread_client:
        return gspread_client
    else:
        print(print_label, "Authorizing Google client")
        return gspread.authorize(google_sheets_credentials)


def fetch_sheet(name: str, code: str = None):
    global gspread_client
    gspread_client = check_authorization(gspread_client)
    print(
        print_label, "Opening the sheet '" + name + (code and ("_" + code) or "") + "'"
    )
    sheet_credentials = google_sheets_config["sheets"][name]
    if sheet_credentials["bookKey"] not in book_cache:
        book_cache[sheet_credentials["bookKey"]] = gspread_client.open_by_key(
            sheet_credentials["bookKey"]
        )
    books_by_sheet[name] = book_cache[sheet_credentials["bookKey"]]
    if code:
        return books_by_sheet[name].worksheet(sheet_credentials["sheetPrefix"] + code)
    else:
        return books_by_sheet[name].get_worksheet_by_id(sheet_credentials["sheetId"])


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
        data = {"dict": {}, "list": [], "pagination": {}}
        for value in sheet.get_values()[1:]:
            if not value[7]:
                entry = {
                    "id": value[0],
                    "name": value[1],
                    "importance": value[2] == "TRUE",
                    "urgency": value[3] == "TRUE",
                    "scheduled_id": value[4],
                    "created": value[5]
                    and datetime.strptime(value[5], "%Y-%m-%d")
                    or datetime.now(),
                    "due_to": value[6] and datetime.strptime(value[6], "%Y-%m-%d"),
                    "done": value[7]
                    and value[7] != "IGNORED"
                    and datetime.strptime(value[7], "%Y-%m-%d")
                    or value[7],
                }
                data["dict"][value[0]] = entry
                data["list"].append(value[0])
        data["list"] = sorted(
            list(data["list"]),
            key=lambda d: (
                -((data["dict"][d]["importance"] and 2 or 0) + (data["dict"][d]["urgency"] and 1 or 0)),
                data["dict"][d]["scheduled_id"] and 1 or 0,
                data["dict"][d]["name"].lower(),
            ),
        )
        data["pagination"]["items"] = len(data["list"])
        data["pagination"]["per_page"] = 5
        data["pagination"]["pages"] = math.ceil(len(data["list"]) / data["pagination"]["per_page"])
        return data
    elif name == "tasks_scheduled":
        data = {"dict": {}, "list": [], "pagination": {}}
        for value in sheet.get_values()[1:]:
            entry = {
                "id": value[0],
                "name": value[1],
                "importance": value[2] == "TRUE",
                "urgency": value[3] == "TRUE",
                "time": value[4],
                "recurring_type": value[5],
                "recurring_value": value[6] and int(value[6]) or 0,
                "recurring_stage": value[7] and int(value[7]) or 0,
                "recurring_timestamp": value[8],
                "times_scheduled": value[9] and int(value[9]) or 0,
                "times_done": value[10] and int(value[10]) or 0,
                "scheduled": value[11] == "TRUE",
                "paused": value[12] == "TRUE",
            }
            data["dict"][value[0]] = entry
            data["list"].append(value[0])

        data["list"] = sorted(
            list(data["list"]),
            key=lambda d: (
                not data["dict"][d]["scheduled"]
                and max(
                    data["dict"][d]["recurring_value"]
                    - (data["dict"][d]["recurring_stage"] - 1),
                    1,
                ) or 0,
                -((data["dict"][d]["importance"] and 2 or 0) + (data["dict"][d]["urgency"] and 1 or 0)),
                data["dict"][d]["name"].lower(),
            ),
        )
        data["pagination"]["items"] = len(data["list"])
        data["pagination"]["per_page"] = 5
        data["pagination"]["pages"] = math.ceil(len(data["list"]) / data["pagination"]["per_page"])
        return data
    else:
        return sheet.get_values()


def get_sheet_name(request):
    is_tuple = type(request) is tuple
    if is_tuple:
        sheet_name: str = request[0] + "_" + request[1]
    else:
        sheet_name: str = request
    return sheet_name, is_tuple


def get_cached_data(requests, update=False):
    for request in requests:
        sheet_name, is_tuple = get_sheet_name(request)

        if update:
            print(print_label, "Data update request for '" + sheet_name + "'")

        if (update) or (sheet_name not in sheets):
            sheets[sheet_name] = (
                is_tuple
                and fetch_sheet(request[0], code=request[1])
                or fetch_sheet(sheet_name)
            )

        if (update) or (sheet_name not in data):
            data[sheet_name] = fetch_data(sheet_name, sheets[sheet_name])

    return data


def insert_into_sheet(request: tuple[str, str] | str, rows: list[list]):
    sheet_name, is_tuple = get_sheet_name(request)
    if sheet_name not in sheets:
        sheets[sheet_name] = (
            is_tuple
            and fetch_sheet(request[0], code=request[1])
            or fetch_sheet(sheet_name)
        )
    print(print_label, "Inserting into '" + sheet_name + "':", str(rows))
    sheets[sheet_name].append_rows(rows)


def invalidate_all():
    sheets: dict[str, Worksheet] = {}
    data: dict = {}
    get_cached_data(sheet_types, update=True)


# cache data from the start
get_cached_data(general_config["production_mode"] and sheet_types or [])
