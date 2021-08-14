"""File system interface that manages and retrieves media."""

import os
import glob
import threading


import psycopg2
from PIL import Image
from pyviewer import ArchiveManager, TagManager


class ImageLoader(TagManager, ArchiveManager):
    """Archive manager for loading and organizing images with tag filters."""

    def __init__(self, run_dir):
        """Create empty media handler."""
        TagManager.__init__(self)
        ArchiveManager.__init__(self, run_dir)

    def _generate_tag_map(self, media_object):
        # TODO allow any tags to be matched
        """Parse archives to derive a tag list with associated archives."""
        meta_list = []
        for archive in glob.glob(media_object + "/*.zip"):
            meta_data = self._fetch_meta_file(archive)
            meta_data.update({"path": archive})
            meta_list.append(meta_data)
        self._media_map = {
            tag: [
                match["path"]
                for match in meta_list
                if "path" in match and "artist" in match
                and match["artist"][0] == tag
            ]
            for tag in {entry["artist"][0] for
                        entry in meta_list if "artist" in entry}
        }

    def extract_current_index(
        self,
    ):
        """Extract archives associated with active tag."""
        file_list = []
        for index, subdir in enumerate(self._subdirs):
            if index >= len(self.media_list):
                break
            file_list.append(
                [
                    os.path.join(subdir.name, file_name)
                    for file_name in self.extract_archive(
                        self.media_list[index], subdir.name
                    )
                ]
            )
        return file_list

    def _check_archive(self, archive_path):
        """Validate all images in archive."""
        for file_path in self.extract_archive(
            archive_path, self._subdirs[0].name
        ):
            full_path = os.path.join(self._subdirs[0].name, file_path)
            with Image.open(full_path) as file:
                file.verify()

    def check_media(self):
        """Check every archive in media directory for corrupt images."""
        for index, tag in enumerate(self.tags):
            self.index = index
            for archive_path in self.media_list:
                try:
                    self._check_archive(archive_path)
                except Image.UnidentifiedImageError as error:
                    print("Cannot open {}: {}".format(archive_path, error))

    @property
    def file_list(self):
        """Return file list associated with current tag."""
        return self.order_file_list(self.extract_current_index())


class BooruLoader(TagManager):
    """Booru manager for loading and organizing images with tag filters."""

    def __init__(self, host="127.0.0.1"):
        """Connect to PG database on creation."""
        self._data_root = ""
        self._file_list = dict()
        self._worker = None
        super().__init__()
        self.pgdb = psycopg2.connect(
            dbname="danbooru2", user="lbl11", password="", host=host)

    def load_media(self, run_dir, media_object):
        """Config root dir and load media map."""
        self._data_root = media_object
        super().load_media(run_dir, media_object)
        tag_buffer = [self.tag_at(index)
                      for index in list(range(self.index-1, self.index+2))]
        self._update_buffer()

    def _generate_tag_map(self, media_object):
        """Query booru for media tags."""
        cursor = self.pgdb.cursor()
        cursor.execute(
            "SELECT * FROM tags WHERE category = 1 AND post_count >= 10 ;")
        self._media_map = {artist[1]: {
            "id": artist[0], "count": artist[2]} for
            artist in cursor.fetchall()}
        cursor.close()

    def _update_buffer(self):
        """Update the file list for list of tags."""
        tag_buffer = [self.tag_at(index)
                      for index in list(range(self.index-2, self.index+3))]
        for tag in set(tag_buffer) - set(self._file_list.keys()):
            self._file_list.update({tag: self.files_at_tag(tag)})

    def files_at_tag(self, tag):
        """Query media at target index."""
        cursor = self.pgdb.cursor()
        cursor.execute(
            "SELECT * FROM posts WHERE tag_index "
            + "@@ $$'{}'$$::tsquery LIMIT 40;".format(tag))
        file_list = ["{}/{}/{}/{}".format(self._data_root, entry[7][0:2],
                                          entry[7][2:4], entry[7])
                     for entry in cursor.fetchall()]
        cursor.close()
        return file_list

    def files_at_index(self, index):
        """Query media at target index."""
        cursor = self.pgdb.cursor()
        cursor.execute(
            "SELECT * FROM posts WHERE tag_index "
            + "@@ $$'{}'$$::tsquery LIMIT 40;".format(self.tag_at(index)))
        file_list = ["{}/{}/{}/{}".format(self._data_root, entry[7][0:2],
                                          entry[7][2:4], entry[7])
                     for entry in cursor.fetchall()]
        cursor.close()
        return file_list

    @ property
    def file_list(self):
        """Query booru for media file list of current tag."""
        if self._worker and self._worker.is_alive():
            self._worker.join()
        if self.tag in self._file_list.keys() and self._file_list[self.tag] != "":
            file_list = self._file_list[self.tag]
        else:
            file_list = ""
        self._worker = threading.Thread(target=self._update_buffer)
        self._worker.start()
        return file_list
