import os
import math
import json
import glob

from zipfile import ZipFile
from tempfile import TemporaryDirectory


class ImageLoader:
    def __init__(self):
        self.temp_dir = TemporaryDirectory()
        self.artist_index = 1
        self.artists = list()
        self.artist_map = dict()
        for index in range(1, 4):
            os.mkdir(os.path.join(self.temp_dir.name, str(index)))

    def _fetchMetaFile(self, file_path):
        with ZipFile(file_path, "r") as archive:
            metafile = archive.extract("metadata.json", path=self.temp_dir.name)
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
                archive.extract(image, path=output_dir)
            return images

    def _generateArtistMap(self, root_dir):
        meta_list = []
        for archive in glob.glob(root_dir + "/*.zip"):
            meta_data = self._fetchMetaFile(archive, self.temp_dir.name)
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

    def loadArtistMap(self, root_dir):
        if os.path.isfile("artist.map"):
            with open("artist.map", "r") as map_file:
                self.artist_map = json.load(map_file)
        else:
            self.artist_map = self._generateArtistMap(root_dir, self.temp_dir.name)
            with open("artist.map", "w") as map_file:
                json.dump(self.artist_map, map_file)
        self.artists = [key for key in self.artist_map]

    def loadViews(self):
        artist_tag = self.artists[self.artist_index]
        archive_list = self.artist_map[artist_tag]
        file_list = list()
        for index in range(1, min(len(archive_list), 4)):
            dir_name = os.path.join(self.temp_dir.name, str(index))
            file_list.append(
                [
                    dir_name + "/" + file_name
                    for file_name in self._fetchImageFile(archive_list[index], dir_name)
                ]
            )
        return file_list

    def orderFileList(self, file_list, modulo=4, max_views=24):
        set_size = [len(set) for set in file_list]
        set_index = [modulo] * len(file_list)
        ordered_list = list()
        for index in range(
            0,
            min(math.floor(sum(set_size) / modulo), math.floor(max_views / modulo) - 1),
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
