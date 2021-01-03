
from typing import List, Iterable, Dict
import datetime
import os

from notion.collection import CollectionRowBlock, Collection
from notion.block import QuoteBlock

from fuzzywuzzy.process import extractOne

from notion_toolkit.utils import exclude_existing_rows
from notion_toolkit.kindle.schemas import ClippingSchema

HIGHLIGHTS_ICON_URL = "https://img.icons8.com/ios/250/000000/barber-scissors.png"


def load_highlights_from_clippings(clippings_path: str = "/Volumes/Kindle/documents/My Clippings.txt") -> List:
    if os.path.exists(clippings_path):
        with os.popen(f"clippings -o json \"{clippings_path}\"") as stream:
            return ClippingSchema(many=True).loads(stream.read())


def fuzzy_match_notion_references(highlights: Iterable, notion_kindle_references: Dict[str, CollectionRowBlock], fuzzy_score_cutoff: float = 0.85):
    memo = dict()
    reference_names = notion_kindle_references.keys()

    for highlight in highlights:
        kindle_title = highlight["kindle_reference_title"]

        if kindle_title not in memo:
            best_guess, _ = extractOne(
                kindle_title, reference_names, score_cutoff=fuzzy_score_cutoff)

            if best_guess is None:
                print(f"No reference in Notion resembling {kindle_title}.")

                continue

            highlight['notion_reference_title'] = best_guess
            highlight['notion_reference_block'] = notion_kindle_references[best_guess]


def filter_recent_highlights(highlights: Iterable, n_last_days: int = 7):
    minimum_date = datetime.datetime.now() - datetime.timedelta(days=n_last_days)

    return list(filter(lambda h: h["created_at"] > minimum_date, highlights))


def push_new_highlights_to_notion(collection: Collection, highlights: List):
    for highlight in exclude_existing_rows(collection, highlights):
        row = collection.add_row(
            name=f"{highlight['notion_reference_title']} - Location {highlight['location']}",
            Status="not reviewed",
            Reference=[highlight['notion_reference_block']],
            Location=highlight["location"],
            Created_at=highlight["created_at"],
            uid=highlight["uid"]
        )
        row.set("format.page_icon", HIGHLIGHTS_ICON_URL)
        row.children.add_new(QuoteBlock, title=highlight["content"])
