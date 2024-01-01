import json

with open("version.json", mode="r", encoding="utf-8") as file:
    cf_version_data = json.load(file)
    cf_version = f"{cf_version_data['package']}@{cf_version_data['major']}.{cf_version_data['minor']}.{cf_version_data['patch']}"
