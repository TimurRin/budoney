import yaml
from os import path


def load(name: str):
    yamlPath = name + ".yaml"
    if path.exists(yamlPath):
        with open(yamlPath, encoding="utf_8") as f:
            return yaml.load(f, Loader=yaml.FullLoader)
    else:
        print("No yaml file '" + path.abspath(yamlPath) + "' found")
        return {}


def save(name: str, data: str):
    yamlPath = name + ".yaml"
    with open(yamlPath, "w", encoding="utf_8") as f:
        yaml.dump(data, stream=f, default_flow_style=False, sort_keys=False)
        print("Config '" + path.abspath(yamlPath) + "' has been saved")
