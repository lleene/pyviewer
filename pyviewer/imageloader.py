"""File system interface that manages and retrieves media."""

import io
import os
import glob
import atexit
from ipaddress import ip_address
from pathlib import Path
from typing import List, Dict, AnyStr
from functools import cached_property
import psycopg2
from PIL import Image
from .util import Archive, TagManager, sample_collection, TagInfo


class ArchiveBrowser(TagManager):
    """Archive manager for loading and organizing images with tag filters."""

    def __init__(self, media_dir: Path, state_file: Path = "pyviewer.state"):
        """Create empty media handler."""
        state_data = TagManager.load_state(state_file)
        if str(media_dir) not in state_data.tag_map:
            state_data.tag_map[str(media_dir)] = self.load_tag_map(media_dir)
        super().__init__(
            tag_map=state_data.tag_map[str(media_dir)],
            tag_filter=state_data.tag_filter,
        )
        atexit.register(
            self.save_state, file_path=state_file, media_path=media_dir
        )

    @classmethod
    def load_tag_map(cls, media_dir: Path = None) -> Dict[str, List[str]]:
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

    @cached_property
    def images(self) -> List[AnyStr]:
        """Extract archives associated with active tag."""
        return sample_collection(
            [
                Archive(archive_path).get_images()
                for index, archive_path in enumerate(self.value)
                if index < 4
            ]
        )

    @classmethod
    def _check_archive(cls, archive_path: Path) -> None:
        """Validate all images in archive."""
        for image in Archive(archive_path).get_images():
            Image.open(io.BytesIO(image)).verify()

    def check_media(self) -> None:
        """Check every archive in media directory for corrupt images."""
        for archive_path in self.values:
            try:
                self._check_archive(archive_path)
            except Image.UnidentifiedImageError as error:
                print("Cannot open {}: {}".format(archive_path, error))

    @property
    def count(self) -> int:
        """File count."""
        return len(self.images)


class BooruBrowser(TagManager):
    """Booru manager for loading and organizing images with tag filters."""

    def __init__(
        self,
        media_host: ip_address = ip_address("127.0.0.1"),
        state_file: Path = "pyviewer.state",
    ):
        """Connect to PG database on creation."""
        self._data_root = "/mnt/media/Media/booru_archive/data/original"
        self.pgdb = psycopg2.connect(
            dbname="danbooru2", user="lbl11", password="", host=media_host
        )
        state_data = TagManager.load_state(state_file)
        if str(media_host) not in state_data.tag_map:
            state_data.tag_map[str(media_host)] = self.load_tag_map()
        super().__init__(
            tag_map=state_data.tag_map[str(media_host)],
            tag_filter=state_data.tag_filter,
        )

    @property
    def count(self) -> int:
        """File count."""
        return len(self.images)

    @classmethod
    def load_image(cls, file_path: Path) -> AnyStr:
        """Load binary image data."""
        with open(file_path, "rb") as file:
            return file.read()

    @cached_property
    def images(self) -> List[AnyStr]:
        """Extract archives associated with active tag."""
        return [
            self.load_image(file_path)
            for index, file_path in enumerate(self.files_at_tag(self.tag))
            if index < 40
        ]

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

    def load_tag_map(self) -> Dict[str, TagInfo]:
        """Query booru for media tags."""
        return self._get_selected_tags(
            ["mikoyan", "asanagi", "honjou_raita", "uno_makoto"]
        )
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
