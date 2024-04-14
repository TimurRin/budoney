import json

with open("cinnabar.json", mode="r", encoding="utf-8") as file:
    cinnabar_data = json.load(file)
    budoney_version = f"{cinnabar_data['name']} v{cinnabar_data['version']['text']}"
