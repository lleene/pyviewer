"""File system interface that manages and retrieves media."""

import io
import os
import glob
import threading
import atexit
from pathlib import Path
from typing import List, Dict, AnyStr
from functools import cached_property
import psycopg2
from PIL import Image
from .util import Archive, TagManager, sample_collection


class ArchiveBrowser(TagManager):
    """Archive manager for loading and organizing images with tag filters."""

    def __init__(self, media_dir: Path, state_file: Path = "pyviewer.state"):
        """Create empty media handler."""
        state_data = TagManager.load_state(state_file)
        if str(media_dir) not in state_data.tag_map:
            state_data.tag_map[str(media_dir)] = self._load_tag_map(media_dir)
        super().__init__(
            tag_map=state_data.tag_map[str(media_dir)],
            tag_filter=state_data.tag_filter,
        )
        atexit.register(
            self.save_state, file_path=state_file, media_path=media_dir
        )

    @classmethod
    def _load_tag_map(cls, media_dir: Path = None) -> Dict[str, List[str]]:
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

    def __init__(self, host="127.0.0.1"):
        """Connect to PG database on creation."""
        self._data_root = ""
        self._file_list = dict()
        self.max_image_count = 40
        self._worker = None
        super().__init__()
        self.pgdb = psycopg2.connect(
            dbname="danbooru2", user="lbl11", password="", host=host
        )

    @property
    def count(self):
        """File count."""
        return (
            len(self._file_list[self.tag])
            if self.tag and self.tag in self._file_list
            else 0
        )

    @classmethod
    def load_file(cls, path):
        """Read file to memory."""
        with open(path, "rb") as file:
            return file.read()

    @property
    def _images(self):
        """Read current index to memory."""
        return [self.load_file(image) for image in self.file_list]

    def load_media(self, run_dir, media_object):
        """Config root dir and load media map."""
        self._data_root = media_object
        super().load_media(run_dir, media_object)
        self._update_buffer()

    def _query_tag(self, tag):
        cursor = self.pgdb.cursor()
        cursor.execute(
            "SELECT * FROM tags WHERE name @@ $$'{}'$$".format(tag)
            + " AND category = 1 AND post_count >= 10 LIMIT 5"
        )
        entry = cursor.fetchone()
        cursor.close()
        return (
            {"id": entry[0], "count": entry[2]}
            if entry and entry[1] == tag
            else {}
        )

    def _get_selected_tags(self, tags):
        return {elem: self._query_tag(elem) for elem in tags}

    def _generate_tag_map(self, media_object):
        """Query booru for media tags."""
        self._media_map = self._get_selected_tags(["doppel", "mikoyan"])
        return
        cursor = self.pgdb.cursor()
        cursor.execute(
            "SELECT * FROM tags WHERE category = 1 AND post_count >= 10 ;"
        )
        self._media_map = {
            artist[1]: {"id": artist[0], "count": artist[2]}
            for artist in cursor.fetchall()
        }
        cursor.close()

    def _update_buffer(self):
        """Update the file list for list of tags."""
        tag_buffer = [
            self.tag_at(index)
            for index in list(range(self.index - 2, self.index + 3))
        ]
        for tag in set(tag_buffer) - set(self._file_list.keys()):
            self._file_list.update({tag: self.files_at_tag(tag)})

    def files_at_tag(self, tag):
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
                + "@@ $$'{}'$$::tsquery ".format(tag)
                + "AND 'jpg png'::tsvector @@ to_tsquery(file_ext)"
                + "AND file_size < 6400000 LIMIT {};".format(
                    self.max_image_count
                )
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

    def files_at_index(self, index):
        """Query media at target index."""
        return self.files_at_tag(self.tag_at(index))

    @property
    def file_list(self):
        """Query booru for media file list of current tag."""
        if self._worker and self._worker.is_alive():
            self._worker.join()
        if self.tag in self._file_list and self._file_list[self.tag] != "":
            file_list = self._file_list[self.tag]
        else:
            file_list = ""
        self._worker = threading.Thread(target=self._update_buffer)
        self._worker.start()
        return file_list


# =]

# =]
# =]

# =]
# =]

# =]

# =]
