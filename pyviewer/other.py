"""Not in use."""

import os
import glob
import pickle
import math
import secrets
import requests
from xmltodict import parse as xmlparse
from tempfile import TemporaryDirectory
from .util import ArchiveManager, TagManager


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
                tag = (
                    self.media["name"]
                    if i == 0
                    else " ".join(self.media["name"].split()[:-i])
                )
                self._previews.extend(self.titles(tag))
            if self._previews:
                for preview in self._previews:
                    self.add_preview(preview)
            self._media_cache[self.media["name"]] = self._previews

    def load_file_map(self, media_object):
        self._media_map = [
            {"path": archive, "name": archive[len(media_object + "/") : -4]}
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


class MyAnimeListDB:
    """Request handler for sending queries to the doujindb API."""

    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.code_verifier = self.get_new_code_verifier()
        self.print_new_authorisation_url()
        self.token = self.generate_new_token(input("Enter Code:"))
        # TODO Cleanup API key interface and exceptions
        """Create http client with a simple agent."""
        self._req_url = "https://api.myanimelist.net/v2"
        self.client = requests.Session()

        for k, v in {
            "MALHLOGSESSID": "09600cb730ef150cb482e3e57a4268f2",
            "MALSESSIONID": "vledmt4vrjqcg2d1to2k394sl5",
            "m_gdpr_mdl_5": "1",
            "is_logged_in": "1",
        }.items():
            cookie = requests.cookies.create_cookie(
                domain="myanimelist.net", name=k, value=v
            )
            self.client.cookies.set_cookie(cookie)
        self.client.headers = {
            "user-agent": "ddbRequest",
            "content-type": "application/json; charset=utf-8",
        }
        self.last_call = {}

    def get_new_code_verifier(self) -> str:
        token = secrets.token_urlsafe(100)
        return token[:128]

    def new_authorisation_url(self, cookies: dict) -> str:
        url = "https://myanimelist.net/v1/oauth2/authorize?response_type=code&client_id={}&code_challenge={}".format(
            self.client_id, self.code_verifier
        )
        print(url)

    def generate_new_token(self, authorisation_code: str) -> dict:
        url = "https://myanimelist.net/v1/oauth2/token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": authorisation_code,
            "code_verifier": self.code_verifier,
            "grant_type": "authorization_code",
        }
        response = requests.post(url, data)
        response.raise_for_status()  # Check whether the requests contains errors
        token = response.json()
        response.close()
        print("Token generated successfully!")
        return token

    def titles(self, tag):
        """Search for items matching title tag"""
        url = "{}/manga?q={}".format(self._req_url, tag.replace(" ", "+"))
        response = self.client.request("GET", url)
        self.last_call.update(
            {
                "url": response.url,
                "status_code": response.status_code,
                "status": response.status_code,
                "headers": response.headers,
            }
        )
        if response.status_code in (200, 201, 202, 204):
            # PUT returns empty JSON entry on success
            return response.content

    def add_preview(self, item):
        pass


class DoujinDB:
    """Request handler for sending queries to the doujindb API."""

    def __init__(self, api_key="050e77672f3d53170ac3"):
        # TODO Cleanup API key interface and exceptions
        """Create http client with a simple agent."""
        self._req_url = "http://doujinshi.mugimugi.org/api/{}".format(api_key)
        self._img_url = "https://img.doujinshi.org/big"
        self.client = requests.Session()
        headers = {
            "user-agent": "ddbRequest",
            "content-type": "application/json; charset=utf-8",
        }
        self.client.headers = headers
        self.last_call = {}

    def _request(self, url, method="GET"):
        """Perform HTTP request and expect xml response from doujindb."""
        try:
            response = self.client.request(method, url)
            self.last_call.update(
                {
                    "url": response.url,
                    "status_code": response.status_code,
                    "status": response.status_code,
                    "headers": response.headers,
                }
            )
            if response.status_code in (200, 201, 202, 204):
                # PUT returns empty JSON entry on success
                return xmlparse(response.content)
            raise error("In _request", response.status_code, response.url)
        except requests.exceptions.Timeout:
            raise error("Timeout! url: {0}".format(response.url))
        except ValueError as e:
            raise error(
                "JSON Error: {0} in line {1} column {2}".format(
                    e.msg, e.lineno, e.colno
                )
            )

    @classmethod
    def _aggregate_names(cls, entry, type_name):
        aggregate = []
        for item in [
            item
            for item in entry["LINKS"]["ITEM"]
            if "@TYPE" in item and item["@TYPE"] == type_name
        ]:
            for tag in ["NAME_EN", "NAME_JP", "NAME_R"]:
                if tag in item and item[tag]:
                    aggregate.append(item[tag])

    @classmethod
    def parse_entry(cls, entry):
        """Reorganize XML structure from doujindb into a simple dict."""
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
        LANG_MAP = [
            "Unknown",
            "English",
            "Japanese",
            "Chinese",
            "Korean",
            "French",
            "German",
            "Spanish",
            "Italian",
            "Russian",
        ]
        if "DATA_LANGUAGE" in entry and entry["DATA_LANGUAGE"]:
            result["language"] = [LANG_MAP[int(entry["DATA_LANGUAGE"])]]
        result["names"] = []
        for tag in ["NAME_EN", "NAME_JP", "NAME_R"]:
            if tag in entry and entry[tag]:
                result["names"].append(entry[tag])
        result["author"] = cls._aggregate_names(entry, "author")
        result["character"] = cls._aggregate_names(entry, "character")
        result["parody"] = cls._aggregate_names(entry, "parody")
        result["tags"] = cls._aggregate_names(entry, "contents")
        return result

    def search(self, api, tag):
        """Make a object API query and extract the list of books in response."""
        url = "{}/?S=objectSearch&T={}&sn={}".format(
            self._req_url, api, tag.replace(" ", "+")
        )
        response = self._request(url)
        if "LIST" in response and "BOOK" in response["LIST"]:
            if type(response["LIST"]["BOOK"]) == type([]):
                return [
                    self.parse_entry(entry)
                    for entry in response["LIST"]["BOOK"]
                ]
            else:
                return [self.parse_entry(response["LIST"]["BOOK"])]
        return []

    def titles(self, tag):
        """Search for items matching title tag."""
        return self.search("title", tag)

    def circles(self, tag):
        """Search for items matching author circle."""
        return self.search("circle", tag)

    def author(self, tag):
        """Search for items matching author tag."""
        return self.search("author", tag)

    def add_preview(self, item):
        """Determine preview URL and append image to search result."""
        if "id" in item:
            url = "{}/{}/{}.jpg".format(
                self._img_url, math.floor(item["id"] / 2000), item["id"]
            )
            response = requests.get(url)
            self.last_call.update(
                {
                    "url": response.url,
                    "status_code": response.status_code,
                    "status": response.status_code,
                    "headers": response.headers,
                }
            )
            if response.status_code in (200, 201, 202, 204):
                item["image"] = response.content


# =]
