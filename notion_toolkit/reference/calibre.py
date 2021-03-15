from notion.collection import CollectionRowBlock

from notion_toolkit.reference import ReferenceModel
from notion_toolkit.notiorm import Model
from notion_toolkit.config import cfg

HIGHLIGHTS_ICON_URL = "https://img.icons8.com/ios/250/000000/barber-scissors.png"

class BookModel(ReferenceModel):
    """
    Books model within the Reference database stored in Notion.
    """

    collection_id = cfg.notion.collections.References.id
    collection_view_ids = cfg.notion.collections.References.views.to_dict()

    BOOK_ICON

    def __init__(self, name: str):
        self.name = name