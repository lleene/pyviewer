"""File system interface that manages and retrieves media."""

import os
import glob
import threading
import pickle

import psycopg2 
from PIL import Image
from pyviewer import ArchiveManager, TagManager, DoujinDB, MyAnimeListDB


class MetaMatcher(ArchiveManager, MyAnimeListDB):
    """Archive manager for updating and reviewing metadata using doujindb as reference."""
    def __init__(self):
        """Create empty media handler."""
        ArchiveManager.__init__(self)
        DoujinDB.__init__(self)
        self.index = 0
        self._media_map = []
        self._previews = []
        self._media_cache = {}

    def extract_current_index(self):
        """Extract archives associated with current index."""
        self._images = self.load_archive(self.media["path"])
        if self.media["name"] in self._media_cache:
            self._previews = self._media_cache[self.media["name"]]
        else:
            self._previews = []
            for i in range(len(self.media["name"].split())):
                if len(self._previews) > self.max_image_count:
                    break
                tag = self.media["name"] if i == 0 else " ".join(self.media["name"].split()[:-i])
                self._previews.extend(self.titles(tag))
            if self._previews:
                for preview in self._previews:
                    self.add_preview(preview)
            self._media_cache[self.media["name"]] = self._previews

    def load_file_map(self, media_object):
        self._media_map = [
                {"path":archive, "name":archive[len(media_object + "/"):-4]}
                for archive in glob.glob(media_object + "/*.zip")
                if not self.fetch_meta_file(archive)
            ]

    def load_cache(self, run_dir):
        if os.access(os.path.join(run_dir, "meta_data.json"), os.R_OK):
            with open(os.path.join(run_dir, "meta_data.json"), "rb") as file:
                self._media_cache = pickle.load(file)

    def save_cache(self, run_dir):
        if os.access(os.path.join(run_dir), os.W_OK):
            with open(os.path.join(run_dir, "meta_data.json"), "wb") as file:
                pickle.dump(self._media_cache, file, pickle.HIGHEST_PROTOCOL)

    def adjust_index(self, direction):
        if len(self._media_map) > 1:
            self.index = (self.index + direction) % len(self._media_map)

    @property
    def media(self):
        return self._media_map[self.index]

class ImageLoader(TagManager, ArchiveManager):
    """Archive manager for loading and organizing images with tag filters."""

    def __init__(self):
        """Create empty media handler."""
        TagManager.__init__(self)
        ArchiveManager.__init__(self)

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

    def extract_current_index(self):
        """Extract archives associated with active tag."""
        images = [ self.load_archive(media, self.max_image_count) for index, media in enumerate(self.media_list) if index < 4 ]
        self.order_images(images)

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
        # TODO use named tuple when fetching from sql
        # from collections import namedtuple
        # derive from table index names
        # namedtuple('query',['name','age','DOB'])
        """Query media at target index."""
        cursor = self.pgdb.cursor()
        cursor.execute(
            "SELECT * FROM posts WHERE tag_index "
            + "@@ $$'{}'$$::tsquery ".format(tag)
            + "AND 'jpg png'::tsvector @@ to_tsquery(file_ext)"
            + "AND file_size < 6400000 LIMIT {};".format(self.max_image_count))
        file_list = ["{}/{}/{}/{}.{}".format(self._data_root, entry[7][0:2],
                                             entry[7][2:4], entry[7], entry[30])
                     for entry in cursor.fetchall()]
        cursor.close()
        return file_list

    def files_at_index(self, index):
        """Query media at target index."""
        return self.files_at_tag(self.tag_at(index))

    @ property
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
