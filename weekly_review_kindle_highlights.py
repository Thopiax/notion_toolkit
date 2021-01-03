
from notion_toolkit.notion_helper import NotionHelper
from notion_toolkit.utils import collection_as_dict
from notion_toolkit.kindle import load_highlights_from_clippings, fuzzy_match_notion_references, filter_recent_highlights, push_new_highlights_to_notion


if __name__ == "__main__":
    print("Loading Highlights from Clippings File...")
    all_highlights = load_highlights_from_clippings()
    recent_highlights = filter_recent_highlights(all_highlights)

    print("Matching Highlights to Notion recorrds...")
    reference_collection = NotionHelper.load_collection("References")
    kindle_references = collection_as_dict(
        reference_collection.get_rows(search="Kindle"))

    fuzzy_match_notion_references(recent_highlights, kindle_references)

    print("Pushing new Highlights to Notion...")
    kindle_highlights_collection = NotionHelper.load_collection(
        "Kindle Highlights")
    push_new_highlights_to_notion(
        kindle_highlights_collection, recent_highlights)

    print("Done")
