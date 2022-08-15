import gspread
from gspread import Spreadsheet
from oauth2client.service_account import ServiceAccountCredentials

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


def fetch_flow_sheet():
    check_authorization()
    print(print_label, "Opening the flow sheet")
    sheet_credentials = google_sheets_config["sheets"]["flow"]
    sheet_name = sheet_credentials["sheetPrefix"] + "2022_08"
    return gspread_client.open_by_key(sheet_credentials["bookKey"]).worksheet(sheet_name)


def fetch_data(sheet: Spreadsheet):
    print(print_label, "Getting data from the sheet '" +
          str(sheet.title) + "' (" + str(sheet.id) + ")")
    return sheet.get_values()


def fetch_all_sheets():
    return {
        "categories": fetch_sheet("categories"),
        "methods": fetch_sheet("methods"),
        "venues": fetch_sheet("venues"),
        "flow": {
            "2022_08": fetch_flow_sheet()
        },
    }


def fetch_all_data(sheets):
    data = {"flow": {}}
    for sheet in sheets:
        if sheet == "flow":
            pass
            # for flow_sheet in sheets["flow"]:
            #     data["flow"][flow_sheet] = fetch_data(sheets["flow"][flow_sheet])
        else:
            data[sheet] = fetch_data(sheets[sheet])
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
