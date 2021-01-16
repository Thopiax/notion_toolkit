from notion_toolkit.notiorm import Model
from notion_toolkit.config import cfg


class ReferenceModel(Model):
    """
    Reference - a model for references (books, web articles, videos, etc.) stored in Notion.
    """

    collection_id = cfg.notion.collections.References.id
    collection_view_ids = cfg.notion.collections.References.views.to_dict()


class ReferenceNotFound(BaseException):
    pass
