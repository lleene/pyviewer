"""File system interface that manages and retrieves media."""

import os
import glob
import atexit
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Tuple
from functools import cached_property
import psycopg2
from .util import Archive, TagManager


class ArchiveBrowser(TagManager):
    """Archive manager for loading and organizing images with tag filters."""

    def __init__(
        self,
        media_dir: Path,
        state_file: Path = Path("pyviewer.state"),
        tags: List[str] = [],
        reload: bool = False,
    ):
        """Create empty media handler."""
        state_data = TagManager.load_state(state_file)
        if str(media_dir) not in state_data.tag_map or reload:
            state_data.tag_map[str(media_dir)] = self.load_tag_map(
                media_dir, selected_tags=tags
            )
        super().__init__(
            tag_map=state_data.tag_map[str(media_dir)],
            tag_filter=state_data.tag_filter,
            tag_selection=tags,
        )
        atexit.register(
            self.save_state, file_path=state_file, media_path=media_dir
        )

    @classmethod
    def load_tag_map(
        cls, media_dir: Path, selected_tags: List[str] = None
    ) -> Dict[str, Tuple[str, ...]]:
        """Find archives and generate association map for each tag."""
        logging.info(f"Regenerating tag map for: {media_dir}")
        meta_list: Dict[str, Tuple[str, ...]] = {}
        for archive in glob.glob(os.path.join(str(media_dir), "*.zip")):
            logging.info(f"Found archive: {archive}")
            meta_data = Archive(archive).meta_file
            tags = (
                meta_data["artist"]
                if "artist" in meta_data and len(meta_data["artist"]) <= 3
                else []
            )
            for tag in tags:
                if "|" in tag:
                    for sub_tag in tag.split("|"):
                        sub_tag.strip()
                        if (
                            sub_tag in meta_list
                            and archive not in meta_list[sub_tag]
                        ):
                            meta_list[sub_tag] = (archive,) + meta_list[
                                sub_tag
                            ]
                        elif sub_tag not in meta_list:
                            meta_list[sub_tag] = (archive,)
                else:
                    tag.strip()
                    if tag in meta_list and archive not in meta_list[tag]:
                        meta_list[tag] = (archive,) + meta_list[tag]
                    elif tag not in meta_list:
                        meta_list[tag] = (archive,)
        return (
            meta_list
            if not selected_tags
            else {
                elem: meta_list[elem]
                for elem in selected_tags
                if elem in meta_list
            }
        )

    @property
    def count(self) -> int:
        """File count."""
        return len(self.files)

    @cached_property
    def files(self) -> List[Tuple[Path, str]]:
        """Extract archives associated with active tag."""
        logging.info(f"Loading archive: {self.value}.")
        return [
            (Path(path), elem)
            for path in self.value
            for elem in Archive(path).image_files
        ]

    def hash(self, image_index: int = 0) -> str:
        """Return image hash at index."""
        if self.count:
            archive, file = self.files[image_index % self.count]
            return hashlib.md5(Archive(archive).load_file(file)).hexdigest()
        return ""

    def image(self, image_index: int = 0) -> bytes:
        """Return image at index."""
        if self.count:
            archive, file = self.files[image_index % self.count]
            return Archive(archive).load_file(file)
        return bytes()

    def path(self, image_index: int = 0) -> str:
        """Return file path at index."""
        if self.count:
            archive, file = self.files[image_index % self.count]
            return f"{archive}/{file}"
        return ""


class BooruBrowser(TagManager):
    """Booru manager for loading and organizing images with tag filters."""

    def __init__(
        self,
        media_host: str = "127.0.0.1",
        state_file: Path = Path("pyviewer.state"),
        tags: List[str] = None,
        reload: bool = False,
    ):
        """Connect to PG database on creation."""
        self._data_root = "/mnt/media/Media/booru_archive/data/original"
        self.pgdb = psycopg2.connect(
            dbname="danbooru2",
            user="lbl11",
            password="",
            host=media_host,
        )
        state_data = TagManager.load_state(state_file)
        if str(media_host) not in state_data.tag_map or reload:
            state_data.tag_map[str(media_host)] = self.load_tag_map(
                selected_tags=tags
            )
        super().__init__(
            tag_map=state_data.tag_map[str(media_host)],
            tag_filter=state_data.tag_filter,
            tag_selection=tags,
        )

    @property
    def count(self) -> int:
        """File count."""
        return len(self.files)

    @cached_property
    def files(self) -> List[Path]:
        """Extract archives associated with active tag."""
        return self.files_at_tag(self.tag, self.value[1])

    def hash(self, image_index: int = 0) -> str:
        """Return image hash at index."""
        if self.count:
            with open(self.files[image_index % self.count], "rb") as file:
                return hashlib.md5(file.read()).hexdigest()
        return ""

    def image(self, image_index: int = 0) -> bytes:
        """Return image at index."""
        if self.count:
            return self.load_image(self.files[image_index % self.count])
        return bytes()

    def path(self, image_index: int = 0) -> Path:
        """Return file path at index."""
        if self.count:
            return self.files[image_index % self.count]
        return Path()

    @classmethod
    def load_image(cls, file_path: Path) -> bytes:
        """Load binary image data."""
        with open(file_path, "rb") as file:
            return file.read()

    def _query_tag(self, tag: str) -> Tuple[str, ...]:
        cursor = self.pgdb.cursor()
        cursor.execute(
            "SELECT * FROM tags WHERE name @@ $$'{}'$$".format(tag)
            + " AND category = 1 AND post_count >= 10 LIMIT 5"
        )
        entry = cursor.fetchone()
        cursor.close()
        return (entry[0], entry[2]) if entry and entry[1] == tag else (0, 0)

    def _get_selected_tags(
        self, tags: List[str]
    ) -> Dict[str, Tuple[str, ...]]:
        return {elem: self._query_tag(elem) for elem in tags}

    def load_tag_map(
        self, selected_tags: List[str] = None
    ) -> Dict[str, Tuple[str, ...]]:
        """Query booru for media tags."""
        logging.info(f"Regenerating tag map for {self.pgdb.info}.")
        if selected_tags:
            return self._get_selected_tags(selected_tags)
        cursor = self.pgdb.cursor()
        cursor.execute(
            "SELECT * FROM tags WHERE category = 1 AND post_count >= 25 ;"
        )
        tag_map: Dict[str, Tuple[str, ...]] = {
            str(artist[1]): (str(artist[0]), str(artist[2]))
            for artist in cursor.fetchall()
        }
        cursor.close()
        return tag_map

    def files_at_tag(
        self, tag: str, count: str = "40", offset: str = "0"
    ) -> List[Path]:
        # TODO use named tuple when fetching from sql
        # from collections import namedtuple
        # derive from table index names
        # namedtuple('query',['name','age','DOB'])
        """Query media at target index."""
        logging.info(f"SQL query for files matching {tag}.")
        file_list = []
        if tag:
            cursor = self.pgdb.cursor()
            cursor.execute(
                "SELECT * FROM posts WHERE tag_index "
                + f"@@ $$'{tag}'$$::tsquery "
                + "AND 'jpg png jpeg JPG PNG JPEG'::tsvector @@ to_tsquery(file_ext) "
                # + f"AND file_size < 6400000 LIMIT {count} OFFSET {offset} "
                + f"ORDER BY id DESC;"
            )
            file_list = [
                Path(
                    os.path.join(
                        self._data_root,
                        entry[7][0:2],
                        entry[7][2:4],
                        f"{entry[7]}.{entry[30]}",
                    )
                )
                for entry in cursor.fetchall()
            ]
            cursor.close()
        return file_list


# =]
