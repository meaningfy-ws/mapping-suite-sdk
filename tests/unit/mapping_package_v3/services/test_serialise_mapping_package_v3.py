import zipfile
from pathlib import Path

import pytest

from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_hasher import MappingPackageV3Hasher
from mapping_suite_sdk.mapping_package_v3.services.serialise_mapping_package_v3 import (
    mapping_package_to_zip_bytes,
    save_mapping_package_v3_to_archive,
    save_mapping_package_v3_to_folder,
)
from mapping_suite_sdk.tools.services.load_mapping_package import load_mapping_package, load_mapping_package_from_bytes
from mapping_suite_sdk.tools.services.validate_mapping_package import validate_mapping_package


@pytest.fixture
def package(dummy_mapping_package_v3_path: Path):
    return load_mapping_package(dummy_mapping_package_v3_path, include_test_data=True, validate_package=False)


def _assert_same_package(loaded, original) -> None:
    # iterdir is sorted, so a collection's file order may differ from the order on disk: compare order-insensitively
    assert loaded.model_dump(exclude={"test_data_suites"}) == original.model_dump(exclude={"test_data_suites"})
    assert [sorted(s.files, key=lambda f: str(f.path)) for s in loaded.test_data_suites] == [
        sorted(s.files, key=lambda f: str(f.path)) for s in original.test_data_suites
    ]


def test_round_trip_through_bytes(package) -> None:
    data = mapping_package_to_zip_bytes(package)

    loaded = load_mapping_package_from_bytes(data, target_version="v3")

    _assert_same_package(loaded, package)
    assert validate_mapping_package(loaded) is True


def test_update_hash_sets_the_hash_on_the_passed_package(package) -> None:
    package.metadata.mapping_suite_hash_digest = "stale"

    mapping_package_to_zip_bytes(package, update_hash=True)

    assert package.metadata.mapping_suite_hash_digest == MappingPackageV3Hasher(package).hash()


def test_update_hash_false_keeps_the_hash(package) -> None:
    package.metadata.mapping_suite_hash_digest = "stale"

    mapping_package_to_zip_bytes(package, update_hash=False)

    assert package.metadata.mapping_suite_hash_digest == "stale"


def test_round_trip_through_an_archive(package, tmp_path: Path) -> None:
    archive = tmp_path / "package.zip"
    save_mapping_package_v3_to_archive(package, archive)

    extracted = tmp_path / "unzipped"
    zipfile.ZipFile(archive).extractall(extracted)
    loaded = load_mapping_package(extracted, include_test_data=True)

    _assert_same_package(loaded, package)


def test_round_trip_through_a_folder(package, tmp_path: Path) -> None:
    save_mapping_package_v3_to_folder(package, tmp_path / "out")

    loaded = load_mapping_package(tmp_path / "out", include_test_data=True)

    _assert_same_package(loaded, package)
