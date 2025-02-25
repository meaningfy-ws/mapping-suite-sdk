import shutil
import shutil
import tempfile
from pathlib import Path
from typing import List

import pytest

from mapping_suite_sdk.adapters.extractor import ArchivePackageExtractor
from mapping_suite_sdk.adapters.loader import MappingPackageLoader
from mapping_suite_sdk.models.mapping_package import MappingPackage
from mapping_suite_sdk.services.load_mapping_package import load_mapping_package_from_folder, \
    load_mapping_package_from_archive, load_mapping_packages_from_github
from tests.conftest import assert_valid_mapping_package


def test_load_mapping_package_from_folder(dummy_mapping_package_path: Path):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path: Path = Path(temp_dir)

        random_file: Path = (temp_dir_path / "tmp_file.txt")
        random_file.touch()

        temp_mp_archive_path = temp_dir_path / dummy_mapping_package_path.name
        shutil.copy(dummy_mapping_package_path, temp_mp_archive_path)

        temp_mp_path = temp_dir_path / dummy_mapping_package_path.stem
        temp_mp_path.mkdir()
        shutil.unpack_archive(temp_mp_archive_path, temp_mp_path)

        with pytest.raises(FileNotFoundError):
            load_mapping_package_from_folder(mapping_package_folder_path=Path("/non/existing/path"))
        with pytest.raises(ValueError):
            load_mapping_package_from_folder(mapping_package_folder_path=random_file)

        mapping_package: MappingPackage = load_mapping_package_from_folder(mapping_package_folder_path=temp_mp_path)

        assert_valid_mapping_package(mapping_package=mapping_package)

        mapping_package: MappingPackage = load_mapping_package_from_folder(mapping_package_folder_path=temp_mp_path,
                                                                           mapping_package_loader=MappingPackageLoader())

        assert_valid_mapping_package(mapping_package=mapping_package)


def test_load_mapping_package_from_archive_gets_invalid_archive(dummy_mapping_package_path: Path):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path: Path = Path(temp_dir)

        random_folder: Path = (temp_dir_path / "tmp_folder")
        random_folder.mkdir(exist_ok=True)

        with pytest.raises(ValueError):
            load_mapping_package_from_archive(mapping_package_archive_path=random_folder)


def test_load_mapping_package_from_archive_gets_invalid_path(dummy_mapping_package_path: Path):
    with pytest.raises(FileNotFoundError):
        load_mapping_package_from_archive(mapping_package_archive_path=Path("/non/existing/path"))


def test_load_mapping_package_from_archive_with_success(dummy_mapping_package_path: Path):
    mapping_package: MappingPackage = load_mapping_package_from_archive(
        mapping_package_archive_path=dummy_mapping_package_path)

    assert_valid_mapping_package(mapping_package=mapping_package)

    mapping_package: MappingPackage = load_mapping_package_from_archive(
        mapping_package_archive_path=dummy_mapping_package_path,
        mapping_package_loader=MappingPackageLoader())

    assert_valid_mapping_package(mapping_package=mapping_package)

    mapping_package: MappingPackage = load_mapping_package_from_archive(
        mapping_package_archive_path=dummy_mapping_package_path,
        mapping_package_loader=MappingPackageLoader(),
        archive_unpacker=ArchivePackageExtractor())

    assert_valid_mapping_package(mapping_package=mapping_package)


def test_load_mapping_packages_from_github_with_success(dummy_github_repo_url: str,
                                                        dummy_github_branch_name: str,
                                                        dummy_packages_path_pattern: str):
    mapping_packages: List[MappingPackage] = load_mapping_packages_from_github(
        github_repository_url=dummy_github_repo_url,
        packages_path_pattern=dummy_packages_path_pattern,
        branch_or_tag_name=dummy_github_branch_name)

    assert len(mapping_packages) > 0
    for mapping_package in mapping_packages:
        assert_valid_mapping_package(mapping_package)
