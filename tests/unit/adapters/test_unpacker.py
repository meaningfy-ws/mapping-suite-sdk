import shutil
import tempfile
from pathlib import Path

import pytest

from mssdk.adapters.unpacker import ArchiveUnpacker
from tests.conftest import _compare_directories


def test_archive_unpack_successful(dummy_mapping_package_path: Path) -> None:
    with ArchiveUnpacker.extract_temporary(dummy_mapping_package_path) as extracted_path:
        assert extracted_path.exists()
        assert extracted_path.is_dir()


def test_archive_cleanup_after_context(dummy_mapping_package_path: Path) -> None:
    with ArchiveUnpacker.extract_temporary(dummy_mapping_package_path) as path:
        extracted_path = path
        assert extracted_path.exists()

    assert not extracted_path.exists()


def test_nonexistent_archive() -> None:
    with pytest.raises(FileNotFoundError) as exc_info:
        with ArchiveUnpacker.extract_temporary(Path("nonexistent.zip")):
            pass
        assert "Archive file not found" in str(exc_info.value)


def test_invalid_archive_path() -> None:
    with pytest.raises(ValueError) as exc_info:
        with ArchiveUnpacker.extract_temporary(Path(__file__)):
            pass
        assert "Specified path is not a file" in str(exc_info.value)


def test_corrupted_archive(dummy_corrupted_mapping_package_path: Path) -> None:
    with pytest.raises(ValueError) as exc_info:
        with ArchiveUnpacker.extract_temporary(dummy_corrupted_mapping_package_path):
            pass
    assert "Failed to extract archive" in str(exc_info.value)


def test_unpacker_pack_directory_generates_same_output(dummy_mapping_package_extracted_path: Path,
                                                       dummy_mapping_package_path: Path):
    with tempfile.TemporaryDirectory() as temp_directory:
        temp_directory_path = Path(temp_directory)

        archived_path = ArchiveUnpacker().pack_directory(dummy_mapping_package_extracted_path,
                                                         temp_directory_path / "packed.zip")
        extracted_path: Path = temp_directory_path / archived_path.stem
        shutil.unpack_archive(archived_path, extracted_path)

        is_equal, error_message = _compare_directories(dummy_mapping_package_extracted_path, extracted_path)
        assert is_equal, f"Directory comparison failed:\n{error_message}"
