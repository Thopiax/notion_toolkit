
# some code taken from https://github.com/Cobertos/notion_export_enhancer

import logging
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()  # Loads the .env file if it exists

# import tempfile
import sys
import os
import time
import re
import argparse
import yaml
import shutil
import zipfile

from box import Box

import urllib.parse

from datetime import datetime
from pathlib import Path, PosixPath
from tempfile import TemporaryDirectory

import csv

import unicodedata
import re


def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "_", value).strip("-_")


logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger()


def format_page_title(title: str):
    title = (
        title.replace(" ", "_")
        .replace("-", "")
        .replace("'", "_")
        .replace(",", "")
        .replace("&", "")
        .replace("/", "")
        .replace("|", "")
        .replace('"', "")
        .replace("@", "")
    )

    return title.lower()


class NotionPageExport:
    def __init__(
        self,
        id: str,
        title: str,
        content: str,
        prefix_slug: str = "",
        legacy_name: str = "",
    ):
        self.id = id
        self.title = title
        self.slug = slugify(title)

        self.content = content

        self.prefix_slug = prefix_slug
        self.legacy_name = legacy_name

        # self.filename = self._build_filename()

        self.properties = {}

    @property
    def parent_path(self) -> Path:
        return Path(
            "/".join([dir_name.title() for dir_name in self.prefix_slug.split(".")])
        )

    @property
    def filename(self):
        return str(self.parent_path / f"{self.slug}.md")

    @property
    def dendron(self):
        result = ["notion"]

        if self.prefix_slug:
            result.append(self.prefix_slug)

        result.append(self.slug)

        return ".".join(result) + ".md"

    def load_properties(
        self, databases: Dict, pages: Dict, include_relations: bool = True
    ):
        if self.prefix_slug in databases:
            if self.slug in databases[self.prefix_slug]:
                self.properties = { "Tags": [] }

                relation_seen = False
                db_properties = databases[self.prefix_slug][self.slug]

                for key, value in sorted(db_properties.items(), key=lambda x: x[0]):
                    if value is None:
                        continue

                    if type(value) is list:
                        if include_relations is False:
                            continue

                        if relation_seen is False:
                            self.content += "\n\n## Relations\n"
                            relation_seen = True

                        # property is a relation
                        self.content += f"\n### {key}\n"

                        for page_id in value:
                            if page_id in pages:
                                page = pages[page_id]

                                self.content += f"[[{page.filename[:-3]}]]\n"

                    elif key == "Tags":
                        for tag in value.split(","):
                            self.properties["Tags"].append(tag.strip())
                    elif key == "Type":
                        self.properties["Tags"].append(value)
                    else:
                        self.properties[key] = value

                self.properties["id"] = self.id
                self.properties["title"] = self.title

    def to_markdown(self):
        result = ""

        if len(self.properties) > 1:
            result += f"---\n{yaml.safe_dump(self.properties, allow_unicode=True)}---\n\n"

        return result + f"# {self.title}\n" + self.content

    def __repr__(self):
        return f"Page<{self.filename}>"


class NotionWorkspaceExport:
    def __init__(
        self,
        root_path: str,
        out_path: str = "./out",
        assets_path: str = "./out/assets/images",
    ):
        self.root_path: PosixPath = Path(root_path)
        self.out_path: PosixPath = Path(out_path)
        self.assets_path: PosixPath = Path(assets_path)

        self.pages: Dict[str, NotionPageExport] = {}

        self.databases: Dict[str, Box] = {}
        self.databases_seen = {}

        if self.out_path.exists() is False:
            os.makedirs(self.out_path)

        if self.assets_path.exists() is False:
            os.makedirs(self.assets_path)

        if os.path.isfile(root_path):
            raise NotImplementedError("Temporary path not implemented")
            assert str(path).endswith(".zip")

            with TemporaryDirectory() as tmp_dir:
                self._extract_zip(tmp_dir)

    def _extract_zip(self):
        with zipfile.ZipFile(self.path) as zf:
            zf.extractall()

    def _process_workspace(self):
        # extract all paths
        self.processing_queue = []
        self.processing_queue.append(self.root_path)

        while len(self.processing_queue) > 0:
            next_path = self.processing_queue.pop(0)

            self._parse_dir(next_path)

        return True

    def convert_dirs(self, include_backlinks: bool = True):
        self._process_workspace()

        for page_id, page in self.pages.items():
            page.load_properties(
                self.databases, self.pages, include_relations=include_backlinks
            )

            page.content = self._format_links(page.content)

            if os.path.isdir(self.out_path / page.parent_path) is False:
                os.makedirs(self.out_path / page.parent_path)

            with open(self.out_path / page.filename, "w", encoding="utf-8") as md_file:
                md_file.write(page.to_markdown())

    def convert_to_dendron(self):
        self._process_workspace()

        # build pages
        for page_id, page in self.pages.items():
            page.load_properties(self.databases, self.pages)
            page.content = self._format_links(page.content)

            with open(self.out_path / page.dendron, "w", encoding="utf-8") as md_file:
                md_file.write(page.to_markdown())

    def _parse_filename(self, filename: str):
        match = re.search(r"(.+?) ([0-9a-f]{32})\.?(md|csv)?$", filename)
        if not match:
            return (None, None, None)

        return slugify(match.groups()[0]), match.groups()[0], match.groups()[1]

    def _parse_db_slug(self, pathname: PosixPath):
        if pathname.parent == self.root_path:
            return ""

        slug, _, _ = self._parse_filename(pathname.parent.name)

        return slug

    def _slugify_path(self, fullpath: str):
        """
        Parses a full path into a tuple of (path, filename)
        """
        path = Path(fullpath)

        if path == self.root_path:
            return ""

        slug, _, _ = self._parse_filename(path.name)

        if path.parent == self.root_path:
            return slug

        parent_slug = self._slugify_path(str(path.parent))

        return ".".join([parent_slug, slug])

    def _parse_dir(self, path: PosixPath):
        assert path.is_dir()

        for filename in os.listdir(path):
            if filename.endswith(".md"):
                page_slug, page_name, page_id = self._parse_filename(filename)

                page_title, page_content = self._parse_page(path / filename)

                full_path_slug = self._slugify_path(path)

                self.pages[page_id] = NotionPageExport(
                    page_id,
                    page_title,
                    page_content,
                    prefix_slug=full_path_slug,
                    legacy_name=page_slug,
                )

            elif filename.endswith(".csv"):
                self._read_database(path / filename)

            elif filename.endswith(("png", "jpg", "jpeg", "pdf")):
                parts = filename.split(".")
                name = parts[:-1]
                ext = parts[-1]
                print(f"{slugify(name)}.{ext}")

                shutil.copyfile(path / filename, self.assets_path / f"{slugify(name)}.{ext}")

            elif os.path.isdir(path / filename):
                self.processing_queue.append(path / filename)

    def _parse_page(self, page_path: PosixPath):
        full_title, true_content = "", ""

        with open(page_path, encoding="utf-8", mode="r") as md_file:
            content = md_file.readlines()

            full_title = content[0][2:].strip()  # remove the starting '#' symbol for H1

            if len(content) > 2:
                content_start_line = 2  # start at the second line
                while re.match(
                    r"^\s*([a-zA-Z0-9_\- ]+)\s*:\s*(.+)$", content[content_start_line]
                ):
                    if content_start_line == len(content) - 1:
                        break

                    content_start_line += 1

                if content_start_line < len(content) - 1:
                    true_content = "\n".join(
                        [line.strip() for line in content[content_start_line:]]
                    )

        return full_title, true_content

    def _format_links(self, content: str):
        pattern = re.compile(
            r"!?\[([^\]]+?)\]\(([\w\d\-._~:/?=#%\]\[@!$&'\(\)*+,;]+?)\)"
        )

        for m in re.finditer(pattern, content):
            link_text, quoted_link_url = m.groups()
            link_url = urllib.parse.unquote(quoted_link_url)

            new_content = m.group(0)

            if link_url.startswith("http"):
                continue

            link_path = Path(link_url)

            # TODO: abstract into a function

            if link_url.endswith(("png", "jpg", "jpeg", "pdf")):
                link_text = urllib.parse.unquote(link_text.split("/")[-1])

                ext = link_text.split(".")[-1]

                new_content = f"![{link_text}](assets/images/{slugify(link_text[:-len(ext) - 1])}.{ext})"

            elif link_url.endswith("csv"):
                db_slug, db_name, _ = self._parse_filename(link_path.name)

                if db_slug not in self.databases_seen:
                    continue

                full_path = [
                    dir.title() for dir in self.databases_seen[db_slug].split(".")
                ]

                # while absolute_path.is_relative_to(self.root_path):
                #     if db_name is None:
                #         print("ERROR:", absolute_path)
                #         break

                #     true_path = [db_name.title()] + true_path

                #     absolute_path = absolute_path.parent

                # print(true_path)

                new_content = f"[[{'/'.join(full_path)}]]"

            elif link_url.endswith("md"):
                _, _, page_id = self._parse_filename(link_path.name)

                page: NotionPageExport = self.pages.get(page_id)

                if page is None:
                    continue

                ## in case I want to convert topics into tags.

                # if str(page.parent_path).split("/")[-1] == "Topics":
                #     new_content = f"#{page.slug}"
                # else:

                new_content = f"[[{page.filename[:-3]} | {link_text.strip()}]]"

            else:
                continue

            content = content.replace(m.group(0), new_content)

        return content

    def _read_database(self, db_filepath: PosixPath):
        db_slug, db_name, db_id = self._parse_filename(db_filepath.name)

        # check if the database with this slug already exists - notion export replicates the full database for every linked view.
        # FIXME: this is a hack to avoid duplicating the database, but doesn't support multiple databases with the same slug (the id is linked to the view)
        if db_slug in self.databases_seen:
            return  # already parsed

        # use full slugs for nesting (doens't matter for the actual file name)
        full_slug = self._slugify_path(db_filepath)

        self.databases_seen[db_slug] = full_slug

        logger.info(f"Building index for with path: {full_slug}")

        self.databases[full_slug] = {}
        self.databases[full_slug]["name"] = db_name
        self.databases[full_slug]["id"] = db_id

        with open(db_filepath, encoding="utf-8-sig", mode="r") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")

            keys = next(csv_reader)

            for row in csv_reader:
                if row[0] == "":
                    continue

                self.databases[full_slug][slugify(row[0])] = {
                    keys[i]: self._format_property(row[i]) for i in range(1, len(row))
                }

    def _format_property(self, property: str):
        # nil
        if property == "":
            return None

        # boolean
        if property == "No":
            return False
        elif property == "Yes":
            return True

        # relation
        unquoted_property = urllib.parse.unquote(property)

        if unquoted_property != property:
            result = []
            for relation in unquoted_property.split(","):
                _, _, page_id = self._parse_filename(Path(relation).name)
                result.append(page_id)

            return result

        # date
        try:
            return datetime.strptime(property, "%B %d, %Y %I:%M %p")
        except ValueError:
            pass

        return property


def cli(argv):
    """
    CLI entrypoint, takes CLI arguments array
    """
    parser = argparse.ArgumentParser(description="Prettifies Notion .zip exports")
    parser.add_argument(
        "-i",
        "--input-file",
        type=str,
        default=os.environ.get("ZIP_PATH"),
        help="the path to the Notion exported .zip file",
    )
    parser.add_argument(
        "-o",
        "--output-path",
        action="store",
        type=str,
        default="./out",
        help="The path to output to, defaults to cwd",
    )
    args = parser.parse_args(argv)

    startTime = time.time()

    exporter = NotionWorkspaceExport(args.input_file, out_path=args.output_path)
    exporter.convert_dirs()

    print("--- Finished in %s seconds ---" % (time.time() - startTime))
    # print(f"Output file written as '{outFileName}'")


if __name__ == "__main__":
    cli(sys.argv[1:])
