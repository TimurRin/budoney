import utils.yaml_manager as yaml_manager
import configs

print("[budoney]", "Loading localization...")
localization = yaml_manager.load(f"config/static/loc/{configs.general['localization']}")
