import argparse
from notion_toolkit.notiorm import Repo

from clippings.parser import parse_clippings

from notion_toolkit.kindle_clipping.model import KindleClippingModel
from notion_toolkit.kindle_clipping.utils import filter_recent, filter_title


def main():
    """Read the provided clippings file, parse it,
    then print it using the provided format.
    """
    parser = argparse.ArgumentParser(description='Kindle Highlights Automatic Notion Uploader')
    parser.add_argument('-f', '--file', dest='clippings_file',
                        default="/Volumes/Kindle/documents/My Clippings.txt", type=argparse.FileType('r'))
    parser.add_argument('-d', '--days', dest='days', type=int, default=7)
    parser.add_argument('-t', '--title', dest='title', default='', type=str)
    args = parser.parse_args()

    clippings = parse_clippings(args.clippings_file)

    if args.days > 0:
        clippings = filter_recent(clippings, args.days)

    if len(args.title) > 0:
        clippings = filter_title(clippings, args.title)

    Repo.init()
    kindle_clippings = KindleClippingModel.from_clippings(clippings)

    for i, clipping in enumerate(kindle_clippings):
        print(f"Processing Clipping #{i}...")
        clipping.insert(unique=True, raise_errors=True)

if __name__ == '__main__':
    main()
