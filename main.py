# %%

from notion.client import NotionClient
from utils import load_collection, collection_as_dict

# %%

reference_collection = load_collection("References")
kindle_highlight_collection = load_collection("Kindle Highlights")

kindle_references = collection_as_dict(reference_collection.get_rows(search="Kindle"))

# %%

from kindle_highlights.highlight import load_highlights_from_clippings, fuzzy_match_notion_references, filter_recent_highlights, push_new_highlights_to_notion

highlights = load_highlights_from_clippings()

recent_highlights = filter_recent_highlights(highlights)
fuzzy_match_notion_references(recent_highlights, kindle_references)

# %%

push_new_highlights_to_notion(kindle_highlight_collection, recent_highlights)
# %%
