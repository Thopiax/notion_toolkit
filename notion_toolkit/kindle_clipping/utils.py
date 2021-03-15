import os
import datetime
from typing import Iterable

from fuzzywuzzy.process import extractOne
from clippings.parser import Clipping


def filter_timestamp(metadata, cutoff):
    if metadata is None:
        return True

    return metadata.timestamp > cutoff


def filter_recent(clippings: Iterable[Clipping], n_days: int = 7) -> Iterable[Clipping]:
    cutoff = datetime.datetime.now() - datetime.timedelta(days=n_days)

    return filter(lambda c: filter_timestamp(c.metadata, cutoff), clippings)


def exclude_none(clippings: Iterable[Clipping]) -> Iterable[Clipping]:
    return filter(lambda c: c is not None, clippings)


def filter_title(clippings: Iterable[Clipping], title: str) -> Iterable[Clipping]:
    clipping_references = set(map(lambda c: c.document.title, clippings))

    result = extractOne(title, clipping_references)

    if result is None:
        return clippings

    best_title_match, best_match_score = result

    print(
        f"Best match found for \"{title}\" in clippings ({best_match_score:.2f}% accuracy):\n\t{best_title_match}")

    return filter(lambda c: c.document.title == best_title_match, clippings)
