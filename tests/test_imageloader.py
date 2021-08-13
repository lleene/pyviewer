
from pyviewer import ImageLoader


class dummy_tmp_dir:
    def __init__(self, dirname):
        self.name = dirname


mock_data_dir = "tests/data"
data_dir = dummy_tmp_dir(mock_data_dir)
loader = ImageLoader(data_dir)


def test_startup():
    assert len(loader.tags) == 0
    assert loader.index == 0


def test_tagfilter():
    loader._media_map = {"test_name": ""}
    loader.update_tag_filter(True)
    assert loader._lasttag == "test_name"
    assert loader._tagfilter == {"test_name": "Approve"}
    assert loader.tags == list()
    loader.undo_last_filter()
    assert loader._tagfilter == dict()


def test_load_media():
    initialized_loader = ImageLoader(data_dir)
    initialized_loader.load_media(mock_data_dir, mock_data_dir)
    assert set(initialized_loader.tags) == {"name", "none"}
    assert initialized_loader._media_map["name"] == [
        "{}/test.zip".format(data_dir.name)
    ]
    initialized_loader.clean_temp_dirs()


def test_extraction():
    initialized_loader = ImageLoader(data_dir)
    initialized_loader.load_media(mock_data_dir, mock_data_dir)
    initialized_loader.set_tag("name")
    assert initialized_loader.tag == "name"
    initialized_loader.extract_current_index()
    # assert len(initialized_loader._file_list) == 1
    # assert len(initialized_loader._file_list[0]) == 30
    # initialized_loader.clean_temp_dirs()
