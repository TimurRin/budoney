from datetime import datetime
import difflib
import gspread
from gspread import Spreadsheet, Worksheet
from oauth2client.service_account import ServiceAccountCredentials

import utils.date_utils as date_utils
import utils.string_utils as string_utils
import utils.yaml_manager as yaml_manager

print_label = "[google_sheets_handler]"

print(print_label, "Loading google-sheets configs")
google_sheets_config = yaml_manager.load("config/local/google-sheets")

print(print_label, "Setting scope to use when authenticating")
scope = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

print(print_label, "Authenticating using credentials, saved in JSON")
google_sheets_credentials = ServiceAccountCredentials.from_json_keyfile_name(
    '../../../config/local/google-api.json', scope)

gspread_client = None
sheets = None
data = None


def check_authorization():
    global gspread_client
    if not gspread_client:
        print(print_label, "Authorizing Google client")
        gspread_client = gspread.authorize(google_sheets_credentials)


def fetch_sheet(name):
    check_authorization()
    print(print_label, "Opening the sheet '" + name + "'")
    sheet_credentials = google_sheets_config["sheets"][name]
    return gspread_client.open_by_key(sheet_credentials["bookKey"]).get_worksheet_by_id(sheet_credentials["sheetId"])


def fetch_transaction_sheet(transaction_code):
    check_authorization()
    print(print_label, "Opening the transaction sheet '" + transaction_code + "'")
    sheet_credentials = google_sheets_config["sheets"]["transactions"]
    sheet_name = sheet_credentials["sheetPrefix"] + transaction_code
    return gspread_client.open_by_key(sheet_credentials["bookKey"]).worksheet(sheet_name)


def fetch_data(name: str, sheet: Spreadsheet):
    print(print_label, "Getting data from the sheet '" +
          name + "' (" + str(sheet.title) + ", " + str(sheet.id) + ")")

    if name == "categories":
        data = {
            "dict": {},
            "list": []
        }
        for value in sheet.get_values()[1:]:
            entry = {
                "id": value[0],
                "name": value[1],
                "emoji": value[2]
            }
            data["dict"][value[0]] = entry
            data["list"].append(value[0])
        return data
    elif name == "merchants":
        data = {
            "dict": {},
            "list": [],
            "keywords": {}
        }
        for value in sheet.get_values()[1:]:
            entry = {
                "id": value[0],
                "name": value[1],
                "category": value[3],
                "emoji": value[4]
            }
            data["dict"][value[0]] = entry
            data["list"].append(value[0])

            data["keywords"][value[0].casefold()] = value[0]
            data["keywords"][value[1].casefold()] = value[0]
            for keyword in value[2].split(","):
                data["keywords"][keyword.casefold()] = value[0]
                # for edited_keyword in string_utils.edits1(keyword):
                #     data["keywords"][edited_keyword.casefold()] = value[0]
                # difflib.get_close_matches(keyword)

        return data
    elif name == "methods":
        data = {
            "dict": {},
            "list": []
        }
        for value in sheet.get_values()[1:]:
            entry = {
                "id": value[0],
                "name": value[1],
                "credit": value[2] == "TRUE" and True or False,
                "mir": value[3] == "TRUE" and True or False,
                "cashback": value[4] == "TRUE" and True or False,
                "owner": value[5]
            }
            data["dict"][value[0]] = entry
            data["list"].append(value[0])
        return data
    elif name == "currencies" or name == "users":
        data = {
            "dict": {},
            "list": []
        }
        for value in sheet.get_values()[1:]:
            entry = {
                "id": value[0],
                "name": value[1]
            }
            data["dict"][value[0]] = entry
            data["list"].append(value[0])
        return data
    else:
        return sheet.get_values()


def fetch_all_sheets():
    transactions = {}

    date = datetime.strptime(google_sheets_config["transactions_start"], '%Y-%m-%d')
    for transaction_code in date_utils.transaction_codes_range(date, date.today()):
        transactions[transaction_code] = fetch_transaction_sheet(transaction_code)

    return {
        "users": fetch_sheet("users"),
        "categories": fetch_sheet("categories"),
        "methods": fetch_sheet("methods"),
        "merchants": fetch_sheet("merchants"),
        "currencies": fetch_sheet("currencies"),
        "transactions": transactions
    }


def fetch_all_data(sheets):
    data = {"transactions": {}}
    for sheet in sheets:
        if sheet == "transactions":
            # pass
            for transaction_sheet in sheets["transactions"]:
                data["transactions"][transaction_sheet] = fetch_data(
                    transaction_sheet, sheets["transactions"][transaction_sheet])
        else:
            data[sheet] = fetch_data(sheet, sheets[sheet])
        pass
    return data


def get_cached_sheets():
    global sheets
    if not sheets:
        sheets = fetch_all_sheets()
    return sheets


def get_cached_data():
    global data
    if not data:
        data = fetch_all_data(get_cached_sheets())
    return data


def insert_into_transaction_sheet(id: str, row: list):
    insert_into_sheet(sheets["transactions"][id], row)


def insert_into_sheet(sheet: Worksheet, row: list):
    sheet.append_row(row)


def invalidate_all():
    global sheets, data
    sheets = None
    data = None


# cache data from the start
get_cached_data()
