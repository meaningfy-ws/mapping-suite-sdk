from pathlib import Path

import pytest

from mapping_suite_sdk import load_mapping_package_from_folder, serialise_mapping_package_to_folder, \
    load_mapping_package_from_archive, serialise_mapping_package
from mapping_suite_sdk.adapters.loader import MappingPackageAssetLoader, MappingPackageLoader
from mapping_suite_sdk.services.validate_mapping_package import validate_mapping_package_from_folder
from mapping_suite_sdk.utils import load_file_by_extensions, write_file_by_content_type


def test_load_file_by_extensions(tmp_path: Path):
    """Test the load_file_by_extensions function with various file types."""

    test_dir = tmp_path / "test_files"
    test_dir.mkdir()

    text_file = test_dir / "test.txt"
    text_file.write_text("This is a text file")

    binary_file = test_dir / "test.bin"
    binary_file.write_bytes(b'\x00\x01\x02\x03')

    unsupported_file = test_dir / "test.unknown"
    unsupported_file.write_text("This has an unsupported extension")

    str_extensions = (".txt", ".html", ".json")
    bytes_extensions = (".bin", ".zip")

    text_content = load_file_by_extensions(text_file, str_extensions, bytes_extensions)
    assert isinstance(text_content, str)
    assert text_content == "This is a text file"

    binary_content = load_file_by_extensions(binary_file, str_extensions, bytes_extensions)
    assert isinstance(binary_content, bytes)
    assert binary_content == b'\x00\x01\x02\x03'

    unsupported_content = load_file_by_extensions(unsupported_file, str_extensions, bytes_extensions)
    assert unsupported_content is None

    non_existent_file = test_dir / "non_existent.txt"
    non_existent_content = load_file_by_extensions(non_existent_file, str_extensions, bytes_extensions)
    assert non_existent_content is None


def test_write_file_by_content_type(tmp_path):
    """Test the write_file_by_content_type function with different content types."""

    test_dir = tmp_path / "test_files"

    text_file = test_dir / "test.txt"
    binary_file = test_dir / "test.bin"

    text_content = "This is a test text file"
    write_file_by_content_type(text_file, text_content)
    assert text_file.exists()
    assert text_file.read_text() == text_content

    binary_content = b'\x00\x01\x02\x03'
    write_file_by_content_type(binary_file, binary_content)
    assert binary_file.exists()
    assert binary_file.read_bytes() == binary_content

    invalid_file = test_dir / "invalid.txt"
    with pytest.raises(TypeError) as excinfo:
        write_file_by_content_type(invalid_file, 123)  # Integer should not a valid content type
    assert "Content must be str or bytes" in str(excinfo.value)
    assert not invalid_file.exists()

    nested_file = test_dir / "nested" / "directory" / "test.txt"
    write_file_by_content_type(nested_file, "Nested file content")
    assert nested_file.exists()
    assert nested_file.read_text() == "Nested file content"

    # Test writing to a location with insufficient permissions
    def mock_write_text(*args, **kwargs):
        raise PermissionError("Permission denied")

    original_write_text = Path.write_text
    try:
        Path.write_text = mock_write_text
        permission_file = test_dir / "permission.txt"
        with pytest.raises(PermissionError) as excinfo:
            write_file_by_content_type(permission_file, "Permission test")
        assert "Permission denied" in str(excinfo.value)
    finally:
        Path.write_text = original_write_text


# def test_l():
#     mp = load_mapping_package_from_archive(mapping_package_archive_path=
#                                            Path("/home/duprijil/work/mapping-suite-sdk/tests/test_data/mapping_packages/package_eforms_29_v1.9_changed.zip"))
#     serialise_mapping_package(mp, serialisation_folder_path=Path("/home/duprijil/work/mapping-suite-sdk/tests/test_data/mapping_packages/alooo.zip"))