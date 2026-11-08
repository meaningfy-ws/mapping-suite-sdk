"""Scenarios of the requirement *Load a package from bytes or a stream* (in-memory-package-io)."""

import io
import tempfile
import zipfile
from pathlib import Path

import pytest

from mapping_suite_sdk.core.adapters.extractor import ArchiveExtractor
from mapping_suite_sdk.core.adapters.validator import MPValidationException
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_lightweight import MappingPackageV3Lightweight
from mapping_suite_sdk.tools.services.load_mapping_package import (
    UnsupportedConversionError,
    UnsupportedVersionError,
    VersionDetectionError,
    load_mapping_package,
    load_mapping_package_from_bytes,
)
from tests import TEST_DATA_EXAMPLE_V3L_MAPPING_PACKAGE_FOLDER_PATH


def _zip_folder(folder: Path, wrapper: str | None = None) -> bytes:
    """Zip the files of ``folder``, under a wrapping folder named ``wrapper`` when given."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for file in sorted(folder.rglob("*")):
            if file.is_file():
                name = file.relative_to(folder).as_posix()
                archive.write(file, f"{wrapper}/{name}" if wrapper else name)
    return buffer.getvalue()


@pytest.fixture
def v2_zip(dummy_mapping_package_v2_archive_path: Path) -> bytes:
    return dummy_mapping_package_v2_archive_path.read_bytes()


@pytest.fixture
def no_disk_writes(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*_args, **_kwargs):
        raise AssertionError("the bytes loader must not write to disk")

    monkeypatch.setattr(tempfile, "TemporaryDirectory", forbidden)
    monkeypatch.setattr(tempfile, "mkdtemp", forbidden)
    for name in ("mkdir", "write_text", "write_bytes"):
        monkeypatch.setattr(Path, name, forbidden)


def test_v2_zip_bytes_load_to_valid_v3_and_write_nothing(v2_zip: bytes, no_disk_writes: None) -> None:
    package = load_mapping_package_from_bytes(v2_zip, target_version="v3")

    assert isinstance(package, MappingPackageV3)


def test_binary_stream_loads_the_same_as_bytes(v2_zip: bytes) -> None:
    assert load_mapping_package_from_bytes(io.BytesIO(v2_zip)) == load_mapping_package_from_bytes(v2_zip)


def test_wrapping_folder_loads_the_same_as_root_layout(dummy_mapping_package_v3_path: Path) -> None:
    root_layout = load_mapping_package_from_bytes(_zip_folder(dummy_mapping_package_v3_path))
    wrapped = load_mapping_package_from_bytes(_zip_folder(dummy_mapping_package_v3_path, wrapper="some_name"))

    assert wrapped == root_layout


def test_not_a_zip_raises_the_archive_error() -> None:
    with pytest.raises(ValueError, match="Failed to extract ZIP file"):
        load_mapping_package_from_bytes(b"definitely not a zip")


def test_unknown_version_raises_version_detection_error() -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("pkg/readme.txt", "nothing a detector knows")

    with pytest.raises(VersionDetectionError):
        load_mapping_package_from_bytes(buffer.getvalue())


@pytest.mark.parametrize(
    ("archive_fixture", "target_version", "expected_type"),
    [
        ("dummy_mapping_package_v1_archive_path", "v3", MappingPackageV3),
        ("dummy_mapping_package_v2_archive_path", "v3", MappingPackageV3),
        ("dummy_mapping_package_v3_archive_path", "v3", MappingPackageV3),
        ("dummy_mapping_package_v1_archive_path", "v3L", MappingPackageV3Lightweight),
        ("dummy_mapping_package_v2_archive_path", " V3l ", MappingPackageV3Lightweight),
        ("dummy_mapping_package_v3_archive_path", "v3L", MappingPackageV3Lightweight),
    ],
)
def test_every_source_version_loads_to_the_target(request, archive_fixture, target_version, expected_type) -> None:
    data = request.getfixturevalue(archive_fixture).read_bytes()

    assert isinstance(load_mapping_package_from_bytes(data, target_version=target_version), expected_type)


def test_v3_lightweight_source_loads_to_v3_lightweight() -> None:
    # validation off: the shipped v3L fixture has a stale hash, which load_mapping_package rejects as well
    package = load_mapping_package_from_bytes(
        _zip_folder(TEST_DATA_EXAMPLE_V3L_MAPPING_PACKAGE_FOLDER_PATH), target_version="v3L", validate_package=False
    )

    assert isinstance(package, MappingPackageV3Lightweight)


def test_v3_lightweight_source_cannot_become_v3() -> None:
    folder = TEST_DATA_EXAMPLE_V3L_MAPPING_PACKAGE_FOLDER_PATH

    with pytest.raises(UnsupportedConversionError):
        load_mapping_package_from_bytes(_zip_folder(folder), target_version="v3")


@pytest.mark.parametrize("target_version", ["v1", "v2", "v9"])
def test_other_targets_raise_a_typed_error(v2_zip: bytes, target_version: str) -> None:
    with pytest.raises(UnsupportedVersionError):
        load_mapping_package_from_bytes(v2_zip, target_version=target_version)


def test_invalid_source_is_rejected_unless_validation_is_off(dummy_mapping_package_v3_path: Path) -> None:
    tampered = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(_zip_folder(dummy_mapping_package_v3_path))) as source:
        with zipfile.ZipFile(tampered, "w") as target:
            for item in source.infolist():
                content = source.read(item.filename)
                target.writestr(item, content + b"\n# tampered" if item.filename.startswith("transformation/") else content)

    with pytest.raises(MPValidationException):
        load_mapping_package_from_bytes(tampered.getvalue())
    assert load_mapping_package_from_bytes(tampered.getvalue(), validate_package=False) is not None


def test_bytes_and_path_loaders_agree_on_metadata_and_hash(dummy_mapping_package_v2_archive_path: Path) -> None:
    with ArchiveExtractor().extract_temporary(dummy_mapping_package_v2_archive_path) as folder:
        from_path = load_mapping_package(folder, include_test_data=True)
    from_bytes = load_mapping_package_from_bytes(dummy_mapping_package_v2_archive_path.read_bytes())

    # file order inside a collection follows the directory listing, so compare the package identity, not the lists
    assert from_bytes.metadata == from_path.metadata
