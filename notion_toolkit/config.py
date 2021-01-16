from box import Box
import yaml
from pathlib import Path

with open("config.yaml", "r") as config_file:
    cfg : Box = Box(yaml.safe_load(config_file), default_box=True, default_box_attr=None)