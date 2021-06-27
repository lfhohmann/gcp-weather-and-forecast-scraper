import yaml


def load_config(filepath):
    # Loads YAML config file
    with open(filepath, "r") as f:
        return yaml.load(f, Loader=yaml.FullLoader)
