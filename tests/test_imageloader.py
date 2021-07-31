from pyviewer import ImageLoader


class dummy_tmp_dir:
    def __init__(self, dirname):
        self.name = dirname


mock_data_dir = "tests/data"
data_dir = dummy_tmp_dir(mock_data_dir)

# We keep this object uninitialized to avoid test dependancy
loader = ImageLoader(data_dir)


def test_startup():
    assert len(loader.artists) == 0
    assert loader.artist_index == 0


def test_tempdirs():
    assert loader._temp_dir.name == data_dir.name
    assert len(loader._subdirs) == 4


def test_tagfilter():
    loader.artists = ["test_name"]
    loader.updateTagFilter(True)
    assert loader._tagfilter == {"test_name": "Approve"}
    assert loader.artists == list()
    loader.undoLastFilter()
    assert loader._tagfilter == dict()


def test_ordering():
    sorted_names = loader.orderFileList([["C2.", "C1.", "C0."], ["A2.", "A0.", "A1."]])
    assert sorted_names[0:3] == ["C0.", "C1.", "C2."]
    assert sorted_names[3:] == ["A0.", "A1.", "A2."]


def test_loadMedia():
    initialized_loader = ImageLoader(data_dir)
    initialized_loader.loadMedia(mock_data_dir)
    assert initialized_loader.artists == ["name"]
    assert initialized_loader._artist_map["name"] == [
        "{}/test.zip".format(data_dir.name)
    ]
    initialized_loader._cleanTempDirs()


def test_extraction():
    initialized_loader = ImageLoader(data_dir)
    initialized_loader.loadMedia(mock_data_dir)
    file_list = initialized_loader.extractCurrentIndex()
    assert len(file_list) == 1
    assert len(file_list[0]) == 30
    initialized_loader._cleanTempDirs()
