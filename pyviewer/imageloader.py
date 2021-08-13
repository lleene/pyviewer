"""File system interface that manages and retrieves media."""
# TODO move management components to seperate file and rename this file

import psycopg2
import glob
import json
import math
import os
from tempfile import TemporaryDirectory
from zipfile import ZipFile
from PIL import Image


class ArchiveManager:
    # TODO Currently using temp dirs but we should use in-memory-object
    """Simple file handler for compressed archives."""

    def __init__(self, tempdir=TemporaryDirectory()):
        """Init manager with pre-allocated tempdirs."""
        self._temp_dir = tempdir
        self._subdirs = [
            TemporaryDirectory(dir=self._temp_dir.name) for index in range(4)
        ]

    def clean_temp_dirs(self):
        # TODO handle condition post cleaned up
        """Tempdir cleanup method."""
        for subdir in self._subdirs:
            subdir.cleanup()
        if isinstance(self._temp_dir, TemporaryDirectory):
            self._temp_dir.cleanup()

    @classmethod
    def order_file_list(cls, file_list, modulo=4, max_image_count=40):
        """Map nested file list into user-friendly flat list of files."""
        set_size = [len(set) for set in file_list]
        set_index = [modulo] * len(file_list)
        ordered_list = list()
        for index in range(
            min(
                math.ceil(sum(set_size) / modulo),
                math.ceil(max_image_count / modulo) - 1,
            )
        ):
            if set_index[index % len(set_size)] < set_size[index % len(set_size)]:
                ordered_list.extend(
                    file_list[index % len(set_size)][
                        set_index[index % len(set_size)]
                        - modulo: set_index[index % len(set_size)]
                    ]
                )
            else:
                ordered_list.extend(
                    file_list[index % len(set_size)][
                        set_index[index % len(set_size)]
                        - modulo: set_size[index % len(set_size)]
                    ]
                )
            set_index[index % len(set_size)] += modulo
        return ordered_list

    @classmethod
    def extract_archive(cls, archive_path, output_dir):
        """Extract all images from archive into output directory."""
        with ZipFile(archive_path, "r") as archive:
            images = [
                file.filename
                for file in archive.infolist()
                if "png" in file.filename or "jpg" in file.filename
            ]
            for image in images:
                file_path = os.path.join(output_dir, image)
                if os.path.exists(file_path):
                    os.remove(file_path)
                archive.extract(image, path=output_dir)
            return images


class TagManager():
    """Tag utility to manage and filter a tag list."""

    def __init__(self):
        """Initialize with empty struct since loading is expensive."""
        self.index = 0
        self._media_map = dict()
        self._tagfilter = dict()
        self._lasttag = ""

    def _generate_tag_map(self, media_object):
        """Adaptable method for generating the tag map from abstract object."""
        pass

    def load_media(self, run_dir, media_object):
        """Load tagfilter and archive map used to index archives."""
        if os.access(os.path.join(run_dir, "tagfilter.json"), os.R_OK):
            with open(os.path.join(run_dir, "tagfilter.json"), "r") as file:
                self._tagfilter = json.load(file)
        if os.access(os.path.join(run_dir, "mapfile.json"), os.R_OK):
            with open(os.path.join(run_dir, "mapfile.json"), "r") as file:
                self._media_map = json.load(file)
        else:
            self._generate_tag_map(media_object)
            if os.access(os.path.join(run_dir, "mapfile.json"), os.W_OK):
                with open(os.path.join(run_dir, "mapfile.json"), "w") as file:
                    json.dump(self._media_map, file)

    def update_tag_filter(self, filter_bool):
        """Update tag filter with filter decision."""
        self._lasttag = self.tag
        if filter_bool:
            self._tagfilter.update({self.tag: "Approve"})
        else:
            self._tagfilter.update({self.tag: "Reject"})

    def undo_last_filter(self):
        """Revert last filter decision."""
        # TODO implement undo stack
        if self._lasttag != "":
            self._tagfilter.pop(self._lasttag)
            self._lasttag = ""

    def adjust_index(self, direction):
        """Accumulate the current index with direction."""
        self.index = (self.index + direction) % len(self.tags)

    def _tag_index(self, tag_name):
        """Find tag name in filtered tag list to derive its index."""
        match = [index for index, tag in enumerate(
            self.tags) if tag == tag_name]
        return match[0] if len(match) >= 0 else self.index

    def set_tag(self, tag_name):
        """Set the current index to the matching tag name."""
        self.index = self._tag_index(tag_name)

    @property
    def tags(self):
        """Return all tags derived from media directory."""
        return [key for key in self._media_map if key not in self._tagfilter]

    @property
    def tag(self):
        """Return the current tag."""
        return self.tags[self.index] if 0 <= self.index < len(self.tags) else ""

    @property
    def media_list(self):
        """Return archives associated with current tag."""
        return self._media_map[self.tag] if self.tag in self._media_map else {}

    def report_filter_state(self):
        """Print a summary of the current tag filter state."""
        print("Exit on:", self.tag)
        print(
            "Tag state:",
            len(self._tagfilter),
            "filtered,",
            len(self.tags),
            "remain",
        )


class ImageLoader(ArchiveManager, TagManager):
    """Archive manager for loading and organizing images with tag filters."""

    def _fetch_meta_file(self, file_path):
        """Load archive metadata file into temp dir and return contents."""
        with ZipFile(file_path, "r") as archive:
            metafile = archive.extract(
                "metadata.json", path=self._temp_dir.name)
            with open(metafile, "r") as file:
                return json.load(file)

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
                if "path" in match and "artist" in match and match["artist"][0] == tag
            ]
            for tag in {entry["artist"][0] for entry in meta_list if "artist" in entry}
        }

    def _save_tag_filter(self, file_path):
        # TODO There must be a better way
        """Store tag filter from file."""
        with open(file_path, "w") as filter_file:
            json.dump(self._tagfilter, filter_file)

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
        for set in file_list:
            set.sort()
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
                except Exception as e:
                    print("Error in {}: {}".format(archive_path, e))

    @property
    def file_list(self):
        """Return file list associated with current tag."""
        return self.order_file_list(self.extract_current_index())


class BooruLoader(TagManager):
    """Booru manager for loading and organizing images with tag filters."""

    def __init__(self):
        """Connect to PG database on creation"""
        super().__init__()
        self._data_root = "/mnt/media/Media/booru_archive/data/original"
        self.pgdb = psycopg2.connect(
            dbname="danbooru2", user="lbl11", password="", host="127.0.0.1")

    def _generate_tag_map(self, media_object):
        """Query booru for media tags."""
        cursor = self.pgdb.cursor()
        cursor.execute(
            "SELECT * FROM tags WHERE category = 1 AND post_count >= 10 ;")
        self._media_map = {artist[1]: {
            "id": artist[0], "count": artist[2]} for artist in cursor.fetchall()}
        cursor.close()

    @ property
    def file_list(self):
        """Query booru for media file list of current tag."""
        cursor = self.pgdb.cursor()
        cursor.execute(
            "SELECT * FROM posts WHERE tag_index @@ $$'{}'$$::tsquery LIMIT 40;".format(self.tag))
        file_list = ["{}/{}/{}/{}".format(self._data_root, entry[7][0:2],
                                          entry[7][2:4], entry[7]) for entry in cursor.fetchall()]
        cursor.close()
        return file_list
