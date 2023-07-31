import utils.yaml_manager as yaml_manager

print("[budoney]", "Loading configs...")
general = yaml_manager.load("config/general")
telegram = yaml_manager.load("config/telegram")
