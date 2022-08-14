import gspread
import gspread_dataframe
from oauth2client.service_account import ServiceAccountCredentials

import utils.yaml_manager as yaml_manager

print("Loading google-sheets configs")
google_sheets_config = yaml_manager.load("config/local/google-sheets")

print("Setting scope to use when authenticating")
scope = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

print("Authenticating using  credentials, saved in JSON")
google_sheets_credentials = ServiceAccountCredentials.from_json_keyfile_name(
    '../../../config/local/google-api.json', scope)


def fetch_sheet():
    print("Initializing the client, and opening the sheet by id")
    client = gspread.authorize(google_sheets_credentials)
    return client.open_by_key(google_sheets_config["bookKey"]).get_worksheet_by_id(google_sheets_config["sheetId"])


def get_data():
    sheet = fetch_sheet()
    print("Getting data from the sheet")
    return gspread_dataframe.get_as_dataframe(sheet, parse_dates=True)


print(get_data())
