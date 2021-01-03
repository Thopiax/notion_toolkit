import os
from typing import Iterable
from notion.client import NotionClient
from notion.collection import Collection

import yaml
from pathlib import Path

config = None
with open(Path(".") / "config.yaml", "rb+") as config_file:
    config = yaml.load(config_file)


def collection_as_dict(collection_list: list, key: str = "title"):
    return {getattr(block, key): block for block in collection_list}


def exclude_existing_rows(collection: Collection, data: Iterable, id_field: str = "uid"):
    for datum in data:
        existing = collection.get_rows(search=datum[id_field])

        if len(existing) > 0:
            print(
                f"Skipping existing row with unique identifier {datum[id_field]}...")
            continue

        yield datum
