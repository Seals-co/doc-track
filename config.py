import yaml
from pathlib import Path

def load_config(config_path=".doctrack.yaml"):
    config_file = Path(config_path)
    if not config_file.exists():
        return {}

    with open(config_file, "r") as f:
        try:
            config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise RuntimeError(f"Error parsing YAML: {e}")

    return config

def update_args(args, config: dict):
    for key, value in config.items():
        if key not in ["add_git_message"]:
            if not getattr(args, key):
                setattr(args, key, value)


    return args