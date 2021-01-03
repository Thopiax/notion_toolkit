from notion.client import NotionClient
from notion.collection import Collection

from notion_toolkit.utils import config

class NotionHelper:
    _client = None

    def __init__(self):
        pass

    @classmethod
    def client(cls) -> NotionClient:
        if cls._client is None:
            cls._client = NotionClient(token_v2=config["notion_token_v2"])

        return cls._client

    @classmethod
    def load_collection(cls, collection_name: str) -> Collection:
        if collection_name in config["notion_collection_ids"]:
            return cls.client().get_collection(config["notion_collection_ids"][collection_name])
    
