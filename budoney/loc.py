import utils.yaml_manager as yaml_manager
import configs

print("[budoney]", "Loading localization...")
localization = yaml_manager.load(f"localization/{configs.general['localization']}")


def translate(key: str) -> str:
    return localization["states"].get(key, key)
