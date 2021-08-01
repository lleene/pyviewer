from tempfile import TemporaryDirectory
from zipfile import ZipFile
from pillow import Image

import glob
import json
import math
import os


class ArchiveManager:
    def __init__(self, tempdir=TemporaryDirectory()):
        self._archive_map = dict()
        self._temp_dir = tempdir
        self._subdirs = [
            TemporaryDirectory(dir=self._temp_dir.name) for index in range(4)
        ]

    def _cleanTempDirs(self):
        for subdir in self._subdirs:
            subdir.cleanup()
        if isinstance(self._temp_dir, TemporaryDirectory):
            self._temp_dir.cleanup()

    def _extractArchive(self, archive_path, output_dir):
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

    def loadMedia(self, media_path):
        self._archive_map = {
            "media": [archive_path for archive_path in glob.glob(media_path + "/*.zip")]
        }

    def validateImage(file_path):
        try:
            with Image.open(file_path) as file:
                file.verify()
                return True
        except Exception as e:
            return False

    def checkArchive(self, archive_path):
        for file_path in self._extractArchive(
            archive_path, self._subdirs[0].name
        ):
            self.validateImage(file_path)


class ImageLoader(ArchiveManager):
    def __init__(self, tempdir=TemporaryDirectory()):
        super().__init__(tempdir)
        self.index = 0
        self._tagfilter = dict()
        self._lasttag = ""

    def _fetchMetaFile(self, file_path):
        with ZipFile(file_path, "r") as archive:
            metafile = archive.extract(
                "metadata.json", path=self._temp_dir.name)
            with open(metafile, "r") as file:
                return json.load(file)

    def _generateTagMap(self, media_path):
        # TODO allow any tags to be matched
        meta_list = []
        for archive in glob.glob(media_path + "/*.zip"):
            meta_data = self._fetchMetaFile(archive)
            meta_data.update({"path": archive})
            meta_list.append(meta_data)
        return {
            tag: [
                match["path"]
                for match in meta_list
                if "path" in match and "artist" in match and match["artist"][0] == tag
            ]
            for tag in {entry["artist"][0] for entry in meta_list if "artist" in entry}
        }

    def _loadTagFilter(self, file_path):
        if os.path.isfile(file_path):
            with open(file_path, "r") as filter_file:
                self._tagfilter = json.load(filter_file)

    def _saveTagFilter(self, file_path):
        with open(file_path, "w") as filter_file:
            json.dump(self._tagfilter, filter_file)

    def updateTagFilter(self, filter_bool):
        self._lasttag = self.tag
        if filter_bool:
            self._tagfilter.update({self.tag: "Approve"})
        else:
            self._tagfilter.update({self.tag: "Reject"})

    def undoLastFilter(self):
        if self._lasttag != "":
            self._tagfilter.pop(self._lasttag)
            self._lasttag = ""
        # TODO implement undo stack

    def _loadTagMap(self, media_dir):
        map_file = os.path.join(media_dir, "mapfile.json")
        if os.path.isfile(map_file):
            with open(map_file, "r") as file:
                self._archive_map = json.load(file)
        else:
            self._archive_map = self._generateTagMap(media_dir)
            with open(map_file, "w") as file:
                json.dump(self._archive_map, file)

    def loadMedia(self, media_path):
        self._loadTagFilter(os.path.join(media_path, "tagfilter.json"))
        self._loadTagMap(media_path)

    def extractCurrentIndex(
        self,
    ):
        archive_list = self.archiveList
        file_list = list()
        for index, subdir in enumerate(self._subdirs):
            if index >= len(archive_list):
                break
            file_list.append(
                [
                    subdir.name + "/" + file_name
                    for file_name in self._extractArchive(
                        archive_list[index], subdir.name
                    )
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

    @property
    def _tags(self):
        return [key for key in self._archive_map if key not in self._tagfilter]

    @property
    def tag(self):
        if 0 <= self.index < len(self._tags):
            return self._tags[self.index]
        else:
            return ""

    @property
    def archiveList(self):
        return self._archive_map[self.tag]

    def reportFilterState(self):
        print("Exit on:", self.tag)
        print(
            "Tag state:",
            len(self._tagfilter),
            "filtered,",
            len(self._tags),
            "remain",
        )
