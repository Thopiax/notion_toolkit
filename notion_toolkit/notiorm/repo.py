from typing import Optional, Dict
from uuid import UUID
from notion.client import NotionClient
from notion.collection import Collection, CollectionView

from notion_toolkit.config import cfg

class Repo(object):
    _client : NotionClient = None
    _collection_map : Dict = None

    def __init__(self):
        pass

    @classmethod
    def init(cls, **config) -> NotionClient:
        if cls._client is None:
            cls._client = NotionClient(
                token_v2=cfg.notion.token_v2,
                enable_caching=config.get("enable_caching", True),
                monitor=config.get("monitor", True),
                start_monitoring=config.get("start_monitoring", True)
            )

        return cls._client

    @classmethod
    def load_collection(cls, collection_id: UUID) -> Collection:
        if cls._collection_map is None:
            cls._collection_map = {}
        
        if collection_id not in cls._collection_map: #pylint:disable=unsupported-membership-test
            cls._collection_map[collection_id] = cls._client.get_collection(collection_id) #pylint:disable=unsupported-assignment-operation

        return cls._collection_map[collection_id] #pylint:disable=unsubscriptable-object

    @classmethod
    def load_collection_view(cls, collection_id: UUID, view_id: UUID) -> CollectionView:
        collection = cls.load_collection(collection_id)

        return cls._client.get_collection_view(view_id, collection=collection)


class ViewNotFoundError(BaseException):
    pass