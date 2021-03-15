from typing import List, Iterable, Dict
from datetime import datetime
from clippings.parser import Clipping
from uuid import UUID

from notion.block import QuoteBlock
from notion.collection import CollectionRowBlock

from functools import reduce

from notion_toolkit.config import cfg
from notion_toolkit.notiorm import Model
from notion_toolkit.reference import ReferenceModel, ReferenceNotFound

from notion_toolkit.kindle_clipping.utils import exclude_none


HIGHLIGHTS_ICON_URL = "https://img.icons8.com/ios/250/000000/barber-scissors.png"


class KindleClippingModel(Model):
    """
    Kindle Clipping - contains information about the clipping
    """

    collection_id = cfg.notion.collections["Kindle Highlights"].id

    def __init__(self, content: str, begin_location: int, category: str, reference_block: CollectionRowBlock, created_at: datetime):
        self.content = content
        self.begin_location = begin_location
        self.category = category

        self.reference_block = reference_block

        self.created_at = created_at

    @property
    def uid(self):
        return str(self.created_at.timestamp())

    @property
    def name(self):
        if self.category == "Highlight":
            return self.content[:75] + (self.content[75:] and '...')

        return f"{self.category} - {self.reference_block.title} @ {self.begin_location}"

    @classmethod
    def from_clipping(cls, clipping: Clipping, raise_errors: bool = True, add_missing_reference: bool = False):
        if clipping.document is None:
            if raise_errors:
                raise BadParsingError(clipping)

            return None


        reference_block = ReferenceModel.find_fuzzy(clipping.document.title, view="Kindle")

        if reference_block is None:
            if raise_errors:
                raise ReferenceNotFound(clipping.document.title)

            return None

        return cls(
            clipping.content,
            clipping.metadata.location.begin,
            clipping.metadata.category,
            reference_block,
            clipping.metadata.timestamp,
        )

    @classmethod
    def from_clippings(cls, clippings: Iterable[Clipping], raise_errors: bool = False):
        instances = map(lambda c: cls.from_clipping(c, raise_errors=raise_errors), clippings)

        return list(exclude_none(instances))

    def _build(self, row):
        row.uid = self.uid
        row.name = self.name

        row.Type = self.category
        row.Reference = [self.reference_block]
        row.Location = self.begin_location
        row.Created_at = self.created_at

        row.set("format.page_icon", HIGHLIGHTS_ICON_URL)
        row.children.add_new(QuoteBlock, title=self.content)

    def __str__(self):
        return f"#{self.uid} - {self.reference_block.title} @ {self.begin_location} - {self.name}"

    def to_dict(self):
        raise NotImplementedError


class BadParsingError(BaseException): pass
