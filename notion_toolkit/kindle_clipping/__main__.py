import argparse
import logging
from notion_toolkit.notiorm import Repo

from clippings.parser import parse_clippings

from notion_toolkit.kindle_clipping.model import KindleClippingModel
from notion_toolkit.kindle_clipping.utils import filter_recent, filter_title, exclude_none

def main():
    """Read the provided clippings file, parse it,
    then print it using the provided format.
    """
    parser = argparse.ArgumentParser(description='Kindle Highlights Automatic Notion Uploader')
    parser.add_argument('-f', '--file', dest='clippings_file',
                        default="/Volumes/Kindle/documents/My Clippings.txt", type=argparse.FileType('r'))
    parser.add_argument('-d', '--days', dest='days', type=int, default=7)
    parser.add_argument('-t', '--title', dest='title', default='', type=str)
    parser.add_argument('-e', '--raise-errors', dest='raise_errors', type=bool, default=False)
    parser.add_argument('-v', '--verbose', dest='verbose', type=bool, default=False)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    logging.info("Extracting Clippings from file...")
    clippings = parse_clippings(args.clippings_file)

    logging.info("Removing empty clippings...")
    clippings = exclude_none(clippings)

    if args.days > 0:
        logging.info(f"Filtering last {args.days} days...")
        clippings = filter_recent(clippings, args.days)

    if len(args.title) > 0:
        logging.info(f"Filtering title: {args.title}...")
        clippings = filter_title(clippings, args.title)

    Repo.init()
    kindle_clippings = KindleClippingModel.from_clippings(clippings)

    for i, clipping in enumerate(kindle_clippings):
        logging.info(f"Processing Clipping ({i + 1}/{len(kindle_clippings)}): {clipping}")

        result = clipping.insert(unique=True, raise_errors=args.raise_errors)

        if result is None:
            logging.warning("Highlight already updated.")

if __name__ == '__main__':
    main()
