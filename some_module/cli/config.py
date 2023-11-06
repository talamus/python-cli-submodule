import os.path
import yaml
from typing import Any


def read_yaml_dict(file_name: str) -> dict[str, Any]:
    """
    Read a YAML file and return a dictionary.
    Throw an error if something goes wrong.
    """
    with open(file_name) as stream:
        content = yaml.safe_load(stream)
    if not isinstance(content, dict):
        raise TypeError(f"'{file_name}' is not a YAML dictionary")
    return content


def set_up_config(
    defaults: dict[str, Any], overrides: dict[str, Any]
) -> dict[str, Any]:
    """
    Build configuration for the application.
    """

    if "config_file" in overrides:
        config = read_yaml_dict(overrides["config_file"])
    elif "config_file" in defaults and os.path.exists(defaults["config_file"]):
        config = read_yaml_dict(defaults["config_file"])
    else:
        config = {}

    config = defaults | config
    config = config | overrides
    return config
