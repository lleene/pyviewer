from pyviewer import ArchiveManager


class dummy_tmp_dir:
    def __init__(self, dirname):
        self.name = dirname


mock_data_dir = "tests/data"
data_dir = dummy_tmp_dir(mock_data_dir)

# We keep this object uninitialized to avoid test dependancy
loader = ArchiveManager(data_dir)


def test_tempdirs():
    assert loader._temp_dir.name == data_dir.name
    assert len(loader._subdirs) == 4


def test_ordering():
    sorted_names = loader.orderFileList(
        [["C2.", "C1.", "C0."], ["A2.", "A0.", "A1."]])
    assert sorted_names[0:3] == ["C0.", "C1.", "C2."]
    assert sorted_names[3:] == ["A0.", "A1.", "A2."]
