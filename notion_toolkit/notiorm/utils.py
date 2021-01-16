import os
from typing import List
from notion.collection import CollectionRowBlock


def collection_result_as_dict(collection_result: List[CollectionRowBlock], key: str = "title"):
    return {getattr(block, key): block for block in collection_result if hasattr(block, key)}