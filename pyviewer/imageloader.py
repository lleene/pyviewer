"""File system interface that manages and retrieves media."""

import io
import os
import glob
import atexit
import hashlib
from ipaddress import ip_address
from pathlib import Path
from typing import List, Dict, AnyStr, Tuple
from functools import cached_property
import psycopg2
from PIL import Image
from .util import Archive, TagManager, sample_collection, TagInfo


class ArchiveBrowser(TagManager):
    """Archive manager for loading and organizing images with tag filters."""

    def __init__(
        self,
        media_dir: Path,
        state_file: Path = "pyviewer.state",
        tags: List[str] = [],
    ):
        """Create empty media handler."""
        state_data = TagManager.load_state(state_file)
        if str(media_dir) not in state_data.tag_map:
            state_data.tag_map[str(media_dir)] = self.load_tag_map(
                media_dir, selected_tags=tags
            )
        super().__init__(
            tag_map=state_data.tag_map[str(media_dir)],
            tag_filter=state_data.tag_filter,
        )
        atexit.register(
            self.save_state, file_path=state_file, media_path=media_dir
        )

    @classmethod
    def load_tag_map(  # TODO handle tag selection
        cls, media_dir: Path = None, selected_tags: List[str] = []
    ) -> Dict[str, List[str]]:
        """Find archives and generate association map for each tag."""
        meta_list = {}
        for archive in glob.glob(os.path.join(media_dir, "*.zip")):
            meta_data = Archive(archive).meta_file
            for tag in "artist" in meta_data and meta_data["artist"] or []:
                if tag in meta_list and archive not in meta_list[tag]:
                    meta_list[tag].append(archive)
                elif tag not in meta_list:
                    meta_list[tag] = [archive]
        return meta_list

    @property
    def count(self) -> int:
        """File count."""
        return len(self.files)

    @cached_property
    def files(self) -> List[Tuple[Path, Path]]:
        """Extract archives associated with active tag."""
        return [
            (path, elem)
            for path in self.value
            for elem in Archive(path).image_files
        ]

    def hash(self, image_index: int = 0) -> str:
        """Return image hash at index."""
        archive, file = self.files[image_index % self.count]
        return hashlib.md5(Archive(archive).load_file(file)).hexdigest()

    def image(self, image_index: int = 0) -> AnyStr:
        """Return image at index."""
        archive, file = self.files[image_index % self.count]
        return Archive(archive).load_file(file)

    def path(self, image_index: int = 0) -> Path:
        """Return file path at index."""
        archive, file = self.files[image_index % self.count]
        return f"{archive}/{file}"


class BooruBrowser(TagManager):
    """Booru manager for loading and organizing images with tag filters."""

    def __init__(
        self,
        media_host: ip_address = ip_address("127.0.0.1"),
        state_file: Path = "pyviewer.state",
        tags: List[str] = None,
    ):
        """Connect to PG database on creation."""
        self._data_root = "/mnt/media/Media/booru_archive/data/original"
        self.pgdb = psycopg2.connect(
            dbname="danbooru2", user="lbl11", password="", host=media_host
        )
        state_data = TagManager.load_state(state_file)
        if str(media_host) not in state_data.tag_map:
            state_data.tag_map[str(media_host)] = self.load_tag_map(
                selected_tags=tags
            )
        super().__init__(
            tag_map=state_data.tag_map[str(media_host)],
            tag_filter=state_data.tag_filter,
        )

    @property
    def count(self) -> int:
        """File count."""
        return len(self.files)

    @cached_property
    def files(self) -> List[Path]:
        """Extract archives associated with active tag."""
        return self.files_at_tag(self.tag, self.value.count)

    def hash(self, image_index: int = 0) -> str:
        """Return image hash at index."""
        with open(self.files[image_index % self.count], "rb") as file:
            return hashlib.md5(file.read()).hexdigest()

    def image(self, image_index: int = 0) -> AnyStr:
        """Return image at index."""
        return self.load_image(self.files[image_index % self.count])

    def path(self, image_index: int = 0) -> Path:
        """Return file path at index."""
        return self.files[image_index % self.count]

    @classmethod
    def load_image(cls, file_path: Path) -> AnyStr:
        """Load binary image data."""
        with open(file_path, "rb") as file:
            return file.read()

    def _query_tag(self, tag: str) -> TagInfo:
        cursor = self.pgdb.cursor()
        cursor.execute(
            "SELECT * FROM tags WHERE name @@ $$'{}'$$".format(tag)
            + " AND category = 1 AND post_count >= 10 LIMIT 5"
        )
        entry = cursor.fetchone()
        cursor.close()
        return (
            TagInfo(entry[0], entry[2])
            if entry and entry[1] == tag
            else TagInfo()
        )

    def _get_selected_tags(self, tags: List[str]) -> Dict[str, TagInfo]:
        return {elem: self._query_tag(elem) for elem in tags}

    def load_tag_map(
        self, selected_tags: List[str] = []
    ) -> Dict[str, TagInfo]:
        """Query booru for media tags."""
        if selected_tags:
            return self._get_selected_tags(selected_tags)
        cursor = self.pgdb.cursor()
        cursor.execute(
            "SELECT * FROM tags WHERE category = 1 AND post_count >= 25 ;"
        )
        tag_map = {
            artist[1]: TagInfo(artist[0], artist[2])
            for artist in cursor.fetchall()
        }
        cursor.close()
        return tag_map

    def files_at_tag(
        self, tag: str, count: int = 40, offset: int = 0
    ) -> List[Path]:
        # TODO use named tuple when fetching from sql
        # from collections import namedtuple
        # derive from table index names
        # namedtuple('query',['name','age','DOB'])
        """Query media at target index."""
        file_list = []
        if tag:
            cursor = self.pgdb.cursor()
            cursor.execute(
                "SELECT * FROM posts WHERE tag_index "
                + f"@@ $$'{tag}'$$::tsquery "
                + "AND 'jpg png'::tsvector @@ to_tsquery(file_ext)"
                + f"AND file_size < 6400000 LIMIT {count} OFFSET {offset};"
            )
            file_list = [
                "{}/{}/{}/{}.{}".format(
                    self._data_root,
                    entry[7][0:2],
                    entry[7][2:4],
                    entry[7],
                    entry[30],
                )
                for entry in cursor.fetchall()
            ]
            cursor.close()
        return file_list


# =]


# =]


# =]
