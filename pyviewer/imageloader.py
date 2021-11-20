"""File system interface that manages and retrieves media."""

import io
import glob
import threading

import psycopg2
from PIL import Image
from .util import ArchiveManager, TagManager


class ImageLoader(TagManager, ArchiveManager):
    """Archive manager for loading and organizing images with tag filters."""

    def __init__(self):
        """Create empty media handler."""
        TagManager.__init__(self)
        ArchiveManager.__init__(self)
        self._file_list = dict()
        self.max_image_count = 40
        self._worker = None

    @property
    def count(self):
        """File count."""
        return (
            len(self._file_list[self.tag])
            if self.tag and self.tag in self._file_list
            else 0
        )

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

    def _generate_tag_map(self, media_object):
        # TODO allow any tags to be matched
        """Parse archives to derive a tag list with associated archives."""
        meta_list = []
        for archive in glob.glob(media_object + "/*.zip"):
            meta_data = self.fetch_meta_file(archive)
            meta_data.update({"path": archive})
            meta_list.append(meta_data)
        self._media_map = {
            tag: [
                match["path"]
                for match in meta_list
                if "path" in match
                and "artist" in match
                and match["artist"][0] == tag
            ]
            for tag in {
                entry["artist"][0] for entry in meta_list if "artist" in entry
            }
        }

    @property
    def _images(self):
        """Extract archives associated with active tag."""
        return self.order_images(
            [
                self.load_archive(media, self.max_image_count)
                for index, media in enumerate(self.media_list)
                if index < 4
            ]
        )

    def _check_archive(self, archive_path):
        """Validate all images in archive."""
        for image in self.load_archive(archive_path):
            Image.open(io.BytesIO(image)).verify()

    def check_media(self):
        """Check every archive in media directory for corrupt images."""
        for index, _ in enumerate(self.tags):
            self.index = index
            for archive_path in self.media_list:
                try:
                    self._check_archive(archive_path)
                except Image.UnidentifiedImageError as error:
                    print("Cannot open {}: {}".format(archive_path, error))


class BooruLoader(TagManager):
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
