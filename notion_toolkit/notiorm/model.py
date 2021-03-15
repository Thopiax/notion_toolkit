from typing import Dict, Optional
from functools import lru_cache
from uuid import UUID
from notion.collection import CollectionRowBlock
from abc import ABC, abstractmethod

from fuzzywuzzy.process import extractOne

from notion_toolkit.notiorm.repo import Repo, ViewNotFoundError
from notion_toolkit.notiorm.utils import collection_result_as_dict


class Model(ABC):
    """
    A Model is used to map Python classes to Notion Collection rows. 
    """

    collection_id: UUID
    collection_view_ids: Dict[str, UUID]

    @property
    @abstractmethod
    def uid(self):
        raise NotImplementedError

    @abstractmethod
    def _build(self, row: CollectionRowBlock):
        raise NotImplementedError

    def insert(self, unique: bool = True, raise_errors: bool = True):
        if unique:
            results = self.__class__.find(self.uid)

            if len(results) > 0:
                if raise_errors:
                    raise RecordAlreadyExistsError

                return None

        row = self.__class__.get_collection().add_row()
        self._build(row)

    @classmethod
    def get_collection(cls):
        return Repo.load_collection(cls.collection_id)

    @classmethod
    def get_view(cls, name: str):
        if name not in cls.collection_view_ids:
            raise ViewNotFoundError(name)

        return Repo.load_collection_view(cls.collection_id, cls.collection_view_ids[name])

    @classmethod
    @lru_cache(maxsize=128)
    def find(cls, query: str, view: Optional[str] = None, refresh: bool = False, **kwargs):
        collection = cls.get_collection()

        if refresh:
            collection.refresh()

        if view is None:
            return collection.get_rows(search=query, **kwargs)

        collection_view = cls.get_view(view)

        collection_view_filter = collection_view._get_record_data()["query2"]["filter"]

        return collection_view.build_query(search=query, filter=collection_view_filter, **kwargs).execute()

    @classmethod
    @lru_cache(maxsize=32)
    def find_all(cls, query: str = "", **kwargs):
        result = cls.find(query, **kwargs)

        return collection_result_as_dict(result)

    @classmethod
    @lru_cache(maxsize=32)
    def find_fuzzy(cls, query: str, fuzzy_cutoff: float = 0.85, **kwargs):
        collection_result = cls.find_all(**kwargs)

        best_match, _ = extractOne(
            query, collection_result.keys(), score_cutoff=fuzzy_cutoff)

        if best_match is None:
            return None

        return collection_result[best_match]



class RecordAlreadyExistsError(BaseException):
    pass
