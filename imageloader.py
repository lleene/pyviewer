import os
import math
import json
import glob

from zipfile import ZipFile
from tempfile import TemporaryDirectory


class ImageLoader:
    def __init__(self):
        self.artist_index = 0
        self._temp_dir = TemporaryDirectory()
        self.artists = list()
        self._artist_map = dict()
        self._tagfilter = dict()
        self._lasttag = ""
        for index in range(0, 3):
            os.mkdir(os.path.join(self._temp_dir.name, str(index)))

    def _fetchMetaFile(self, file_path):
        with ZipFile(file_path, "r") as archive:
            metafile = archive.extract("metadata.json", path=self._temp_dir.name)
            with open(metafile, "r") as file:
                return json.load(file)

    def _fetchImageFile(self, archive_path, output_dir):
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

    def _generateArtistMap(self, root_dir):
        meta_list = []
        for archive in glob.glob(root_dir + "/*.zip"):
            meta_data = self._fetchMetaFile(archive, self._temp_dir.name)
            meta_data.update({"path": archive})
            meta_list.append(meta_data)
        return {
            artist: [
                match["path"]
                for match in meta_list
                if "path" in match
                and "artist" in match
                and match["artist"][0] == artist
            ]
            for artist in {
                entry["artist"][0] for entry in meta_list if "artist" in entry
            }
        }

    def currentArtist(self):
        return self.artists[self.artist_index]

    def reportFilterState(self):
        print( "Exit on:", self.currentArtist())
        print( "Tag state:", len(self._tagfilter), "filtered,", len(self.artists), "remain")

    def _loadTagFilter(self):
        if os.path.isfile("tagfilter.json"):
            with open("tagfilter.json", "r") as filter_file:
                self._tagfilter = json.load(filter_file)

    def saveTagFilter(self):
        with open("tagfilter.json", "w") as filter_file:
            json.dump(self._tagfilter, filter_file)

    def updateTagFilter(self, filter_bool):
        if filter_bool:
            self._tagfilter.update({self.currentArtist(): "Approve"})
        else:
            self._tagfilter.update({self.currentArtist(): "Reject"})
        self._lasttag = self.currentArtist()
        self.artists = [key for key in self._artist_map if key not in self._tagfilter]

    def undoLastFilter(self):
        self._tagfilter.pop(self._lasttag)
        self._lasttag = ""
        self.artists = [key for key in self._artist_map if key not in self._tagfilter]

    def _loadArtistMap(self, root_dir):
        if os.path.isfile("artist.map"):
            with open("artist.map", "r") as map_file:
                self._artist_map = json.load(map_file)
        else:
            self._artist_map = self._generateArtistMap(root_dir, self._temp_dir.name)
            with open("artist.map", "w") as map_file:
                json.dump(self._artist_map, map_file)
        self.artists = [key for key in self._artist_map if key not in self._tagfilter]

    def loadMedia(self, root_dir):
        self._loadTagFilter()
        self._loadArtistMap(root_dir)

    def extractCurrentIndex(self):
        artist_tag = self.artists[self.artist_index]
        archive_list = self._artist_map[artist_tag]
        file_list = list()
        for index in range(0, min(len(archive_list), 3)):
            dir_name = os.path.join(self._temp_dir.name, str(index))
            file_list.append(
                [
                    dir_name + "/" + file_name
                    for file_name in self._fetchImageFile(archive_list[index], dir_name)
                ]
            )
        return file_list

    def orderFileList(self, file_list, modulo=4, max_image_count=40):
        for set in file_list:
            set.sort()
        set_size = [len(set) for set in file_list]
        set_index = [modulo] * len(file_list)
        ordered_list = list()
        for index in range(
            0,
            min(
                math.floor(sum(set_size) / modulo),
                math.floor(max_image_count / modulo) - 1,
            ),
        ):
            if set_index[index % len(set_size)] < set_size[index % len(set_size)]:
                ordered_list.extend(
                    file_list[index % len(set_size)][
                        set_index[index % len(set_size)]
                        - modulo : set_index[index % len(set_size)]
                    ]
                )
            else:
                ordered_list.extend(
                    file_list[index % len(set_size)][
                        set_index[index % len(set_size)]
                        - modulo : set_size[index % len(set_size)]
                    ]
                )
            set_index[index % len(set_size)] += modulo
        return ordered_list
