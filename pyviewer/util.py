"""utility classes for managing imageloaders."""

import json
import os
from math import ceil
from pathlib import Path
from typing import NamedTuple, List, Dict, Set, Any, AnyStr, Tuple
from zipfile import ZipFile


class Archive(ZipFile):
    """Simple file handler for compressed archives."""

    def load_file(self, file_name: str) -> AnyStr:
        """Load file from archive by name."""
        with self.open(file_name, "r") as file:
            return file.read()

    @property
    def meta_file(self) -> dict:
        """Fetch the meta file from archive."""
        return (
            json.loads(self.load_file("metadata.json"))
            if "metadata.json" in [elem.filename for elem in self.infolist()]
            else {}
        )

    @property
    def image_files(self) -> List[str]:
        """Return list of file names in archive."""
        return [
            file.filename
            for file in self.infolist()
            if file.filename[-4:] == ".png" or file.filename[-4:] == ".jpg"
        ]

    def get_images(self, count: int = 40) -> List[AnyStr]:
        """Extract and return images as array of binary objects."""
        image_list = self.image_files
        image_list.sort()
        return [
            self.load_file(elem)
            for index, elem in enumerate(image_list)
            if index < count
        ]


class FilterEntry(NamedTuple):
    """Typed container presenting a tag filter entry."""

    tag: str
    state: bool


class FilterState(NamedTuple):
    """Typed container presenting a tag filter entry."""

    tag_map: Dict[str, List[str]] = {}
    tag_filter: List[FilterEntry] = []


class TagInfo(NamedTuple):
    """Typed container presenting booru tag information."""

    id: int = None
    count: int = 0


class TagManager:
    """Utility to manage a collection indexed and filtered by keys."""

    def __init__(
        self,
        tag_map: Dict[str, List[str]] = None,
        tag_filter: List[FilterEntry] = None,
    ):
        """Initialize with empty struct since loading is expensive."""
        self.index = 0
        self._tag_map = tag_map or {}
        self._filter = tag_filter or []
        self._tagstack: List[FilterEntry] = []

    def update_tag_filter(self, filter_bool: bool) -> bool:
        """Update tag filter with filter decision."""
        if self.tag in self.filter:
            return False
        self._tagstack.append(FilterEntry(self.tag, filter_bool))
        return True

    def undo_last_filter(self) -> bool:
        """Revert last filter decision."""
        if self._tagstack and self.tag in self.filter:
            self._tagstack.pop(-1)
            return True
        return False

    def adjust_index(self, direction: int) -> None:
        """Accumulate the current index with direction."""
        if len(self.tags) > 1:
            self.index = (self.index + direction) % len(self.tags)

    def _tag_index(self, tag_name: str) -> int:
        """Find tag name in filtered tag list to derive its index."""
        match = [
            index for index, tag in enumerate(self.tags) if tag == tag_name
        ]
        return match[0] if len(match) >= 0 else self.index

    def tag_at(self, index: int) -> str:
        """Tag at index in filtered tag list."""
        return self.tags[index] if 0 <= index < len(self.tags) else ""

    def set_tag(self, tag_name: str) -> None:
        """Set the current index to the matching tag name."""
        self.index = self._tag_index(tag_name)

    @property
    def filter(self) -> Set[str]:
        """Return the current tag filter being applied."""
        return {elem.tag for elem in self._filter + self._tagstack}

    @property
    def tags(self) -> List[str]:
        """Return all tags derived from media directory."""
        return [key for key in self._tag_map if key not in self.filter]

    @property
    def tag(self) -> str:
        """Return the current tag."""
        return self.tag_at(self.index)

    @property
    def value(self) -> List[str]:
        """Return elements associated with current tag."""
        return self._tag_map[self.tag] if self.tag in self._tag_map else []

    @property
    def values(self) -> Set[str]:
        """Return all unique elements in map."""
        return {elem for tag in self.tags for elem in self._tag_map[tag]}

    @property
    def tag_filter_state(self) -> str:
        """Return a summary of the current tag filter state."""
        return (
            f"Current Tag: {self.tag},"
            + f" Filter Count: {len(self.filter)},"
            + f" Active Count: {len(self.tags)}"
        )

    @classmethod
    def load_state(cls, file_path: Path) -> FilterState:
        """Load tag filter from file."""
        if os.access(file_path, os.R_OK):
            with open(file_path, mode="r", encoding="utf8") as file:
                return FilterState(*json.load(file))
        return FilterState()

    def save_state(self, file_path: Path, media_path: Path) -> None:
        """Save current tag filter to file."""
        old_state = self.load_state(file_path)
        old_state.tag_map[str(media_path)] = self._tag_map
        with open(file_path, mode="w", encoding="utf8") as file:
            json.dump(FilterState(old_state.tag_map, self._filter), file)


def sample_collection(
    collection: List[List[Any]], modulo: int = 4, count: int = 40
) -> List[Any]:
    """Organize several lists into flat list using interlaced groups."""
    set_size = [len(set) for set in collection]
    ordered_list = []
    if sum(set_size) <= 0:
        return []
    set_index = [modulo] * len(collection)
    for index in range(
        min(
            ceil(sum(set_size) / modulo),
            ceil(count / modulo),
        )
    ):
        if set_index[index % len(set_size)] < set_size[index % len(set_size)]:
            ordered_list.extend(
                collection[index % len(set_size)][
                    set_index[index % len(set_size)]
                    - modulo : set_index[index % len(set_size)]
                ]
            )
        else:
            ordered_list.extend(
                collection[index % len(set_size)][
                    set_index[index % len(set_size)]
                    - modulo : set_size[index % len(set_size)]
                ]
            )
        set_index[index % len(set_size)] += modulo
    return ordered_list


# =]
# =]
