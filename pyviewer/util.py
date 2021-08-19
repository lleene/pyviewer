"""utility classes for managing imageloaders."""

import math
import json
import os

import requests
from xmltodict import parse as xmlparse
from zipfile import ZipFile
from tempfile import TemporaryDirectory


class ArchiveManager:
    """Simple file handler for compressed archives."""

    def __init__(self):
        """Init manager empty data structure."""
        self.max_image_count = 40
        self.modulo = 4
        self._images = []

    def load_file(self, archive, filename):
        with archive.open(filename,'r') as file:
            return file.read()

    def _fetch_meta_file(self, file_path):
        """Load archive metadata file into temp dir and return contents."""
        with ZipFile(file_path, "r") as archive:
            return json.loads(self.load_file(archive,"metadata.json"))

    def load_archive(self, archive_path, count=None):
        # TODO asses file integrity here
        """Extract and return images as array of binary objects."""
        with ZipFile(archive_path, "r") as archive:
            image_list = [
                file.filename
                for file in archive.infolist()
                if ".png" == file.filename[-4:] or ".jpg" == file.filename[-4:]
            ]
            image_list.sort()
            if count :
                image_list = image_list[0:min(count, len(image_list))]
            return [ self.load_file(archive, image_name) for image_name in image_list ]

    def order_images(self, images):
        """Map list into user-friendly flat list of files."""
        set_size = [len(set) for set in images]
        set_index = [self.modulo] * len(images)
        ordered_list = []
        for index in range(
            min(
                math.ceil(sum(set_size) / self.modulo),
                math.ceil(self.max_image_count / self.modulo),
            )
        ):
            if set_index[index % len(set_size)] \
              < set_size[index % len(set_size)]:
                ordered_list.extend(
                    images[index % len(set_size)][
                        set_index[index % len(set_size)]
                        - self.modulo: set_index[index % len(set_size)]
                    ]
                )
            else:
                ordered_list.extend(
                    images[index % len(set_size)][
                        set_index[index % len(set_size)]
                        - self.modulo: set_size[index % len(set_size)]
                    ]
                )
            set_index[index % len(set_size)] += self.modulo
        self._images = ordered_list

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
            if os.access(os.path.join(run_dir), os.W_OK):
                with open(os.path.join(run_dir, "mapfile.json"), "w") as file:
                    json.dump(self._media_map, file)

    def save_tag_filter(self, run_dir):
        """Store tag filter from file."""
        if os.access(os.path.join(run_dir), os.W_OK):
            with open(os.path.join(run_dir, "tagfilter.json"), "w") as file:
                json.dump(self._tagfilter, file)

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

    def tag_at(self, index):
        """Tag at index in filtered tag list."""
        return self.tags[index] \
            if 0 <= self.index < len(self.tags) else ""

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
        return self.tag_at(self.index)

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


class DoujinDB():

    def __init__(self, site_url="http://doujinshi.mugimugi.org/api/050e77672f3d53170ac3"):
        self.site_url = site_url
        self.client = requests.Session()
        headers = {'user-agent': 'ddbRequest',
                   'content-type': 'application/json; charset=utf-8'}
        self.client.headers = headers
        self.last_call = {}

    def _request(self, url, method='GET'):
        try:
            response = self.client.request(method, url)
            self.last_call.update({
                'url': response.url,
                'status_code': response.status_code,
                'status': response.status_code,
                'headers': response.headers
                })
            if response.status_code in (200, 201, 202, 204):
                # PUT returns empty JSON entry on success
                return xmlparse(response.content)
            raise error("In _request", response.status_code, response.url)
        except requests.exceptions.Timeout:
            raise error("Timeout! url: {0}".format(response.url))
        except ValueError as e:
            raise error("JSON Error: {0} in line {1} column {2}".format(e.msg, e.lineno, e.colno))

    @classmethod
    def parse_entry(cls, entry):
        result = {}
        if "@ID" in entry and entry["@ID"]:
            result["id"] = int(entry["@ID"][1:])
        if "NAME_EN" in entry and entry["NAME_EN"]:
            result["title"] = entry["NAME_EN"]
        elif "NAME_JP" in entry and entry["NAME_JP"]:
            result["title"] = entry["NAME_JP"]
        elif "NAME_R" in entry and entry["NAME_R"]:
            result["title"] = entry["NAME_R"]
        if "DATA_PAGES" in entry and entry["DATA_PAGES"]:
            result["pages"] = entry["DATA_PAGES"]
        LANG_MAP = ["Unknown","English","Japanese","Chinese","Korean","French","German","Spanish","Italian","Russian"]
        if "DATA_LANGUAGE" in entry and entry["DATA_LANGUAGE"]:
            result["language"] = [LANG_MAP[int(entry["DATA_LANGUAGE"])]]
        result["author"] = []
        for item in [ item for item in entry["LINKS"]["ITEM"] if "@TYPE" in item and item["@TYPE"] == "author"]:
             for tag in ["NAME_EN","NAME_JP","NAME_R"]:
                 if tag in item and item[tag]:
                     result["author"].append(item[tag])
        result["character"] = []
        for item in [item for item in entry["LINKS"]["ITEM"] if "@TYPE" in item and item["@TYPE"] == "character"]:
             for tag in ["NAME_EN","NAME_JP","NAME_R"]:
                 if tag in item and item[tag]:
                     result["character"].append(item[tag])
        result["parody"] = []
        for item in [item for item in entry["LINKS"]["ITEM"] if "@TYPE" in item and item["@TYPE"] == "parody"]:
             for tag in ["NAME_EN","NAME_JP","NAME_R"]:
                 if tag in item and item[tag]:
                     result["character"].append(item[tag])
        result["tags"] = []
        for item in [item for item in entry["LINKS"]["ITEM"] if "@TYPE" in item and item["@TYPE"] == "contents"]:
             for tag in ["NAME_EN","NAME_JP","NAME_R"]:
                 if tag in item and item[tag]:
                     result["tags"].append(item[tag])
        return result

    def search(self, api, tag):
        """Make a object API query and extract the list of books in response."""
        url = "{}/?S=objectSearch&T={}&sn={}".format(self.site_url, api, tag)
        response = self._request(url)
        if "LIST" in response and "BOOK" in response["LIST"]:
            if type(response["LIST"]["BOOK"]) == type([]):
                return [ self.parse_entry(entry) for entry in response["LIST"]["BOOK"] ]
            elif type(response["LIST"]["BOOK"]) == type({}):
                return [ self.parse_entry( response["LIST"]["BOOK"] ) ]

    def titles(self, tag):
        return self.search("title", tag)

    def circles(self, tag):
        return self.search("circle", tag)

    def author(self, tag):
        return self.search("author",tag)

    def previews(self, item_list):
         return [ "https://img.doujinshi.org/big/{}/{}.jpg".format(math.floor(item["id"]/2000), item["id"])
                for item in item_list if "id" in item ]