from pathlib import Path

import yaml


def load_config(config_path=".doctrack.yaml"):
    config_file = Path(config_path)
    if not config_file.exists():
        return {}

    with open(config_file) as f:
        try:
            config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise RuntimeError(f"Error parsing YAML: {e}")

    return config


def update_args(args, config: dict):
    for key, value in config.items():
        if key not in ["add_git_message"] and getattr(args, key) is None:
            setattr(args, key, value)

    return args
