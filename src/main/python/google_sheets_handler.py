from datetime import datetime
import string
import gspread
from gspread import Spreadsheet
from oauth2client.service_account import ServiceAccountCredentials

import utils.date_utils as date_utils
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


def fetch_flow_sheet(flow_code):
    check_authorization()
    print(print_label, "Opening the flow sheet '" + flow_code + "'")
    sheet_credentials = google_sheets_config["sheets"]["flow"]
    sheet_name = sheet_credentials["sheetPrefix"] + flow_code
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
    elif name == "venues":
        data = {
            "dict": {},
            "list": []
        }
        for value in sheet.get_values()[1:]:
            entry = {
                "id": value[0],
                "name": value[1],
                "category": value[3]
            }
            data["dict"][value[0]] = entry
            data["list"].append(value[0])
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
                "owner": value[3]
            }
            data["dict"][value[0]] = entry
            data["list"].append(value[0])
        return data
    else:
        return sheet.get_values()


def fetch_all_sheets():
    flows = {}

    date = datetime.strptime(google_sheets_config["flow_start"], '%Y-%m-%d')
    for flow_code in date_utils.flow_codes_range(date, date.today()):
        flows[flow_code] = fetch_flow_sheet(flow_code)

    return {
        "categories": fetch_sheet("categories"),
        "methods": fetch_sheet("methods"),
        "venues": fetch_sheet("venues"),
        "flow": flows
    }


def fetch_all_data(sheets):
    data = {"flow": {}}
    for sheet in sheets:
        if sheet == "flow":
            # pass
            for flow_sheet in sheets["flow"]:
                data["flow"][flow_sheet] = fetch_data(
                    flow_sheet, sheets["flow"][flow_sheet])
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


def invalidate_all():
    global sheets, data
    sheets = None
    data = None


# cache data from the start
get_cached_data()
