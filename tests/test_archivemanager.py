"""Test module for validating archive management operations"""

from pyviewer import ArchiveManager


class DummyTempDir:
    """Mocking object for handling a temp-dir in local file structure"""

    def __init__(self, dirname):
        self.name = dirname


MOCK_DATA_DIR = "tests/data"
data_dir = DummyTempDir(MOCK_DATA_DIR)

# We keep this object uninitialized to avoid test dependancy
loader = ArchiveManager(data_dir)


def test_tempdirs():
    """Verify the instantiation of temp directory structure"""
    assert loader._run_dir.name == data_dir.name
    assert len(loader._subdirs) == 4


def test_ordering():
    """Test file ordering procedure"""
    sorted_names = loader.order_file_list(
        [["C0.", "C1.", "C2."], ["A0.", "A1.", "A2."]])
    assert sorted_names == ["C0.", "C1.", "C2.", "A0.", "A1.", "A2."]
