from pathlib import Path

import pytest

from mssdk.adapters.unpacker import ArchiveUnpacker


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
