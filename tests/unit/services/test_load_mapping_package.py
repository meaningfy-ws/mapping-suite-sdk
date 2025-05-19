import shutil
import tempfile
from pathlib import Path
from typing import List

import mongomock
import pytest

from mapping_suite_sdk.adapters.extractor import ArchivePackageExtractor
from mapping_suite_sdk.adapters.loader import MappingPackageLoader
from mapping_suite_sdk.models.mapping_package import MappingPackage
from mapping_suite_sdk.services.load_mapping_package import load_mapping_package_from_folder, \
    load_mapping_package_from_archive, load_mapping_packages_from_github, load_mapping_package_from_mongo_db
from tests.conftest import assert_valid_mapping_package, _setup_temporary_test_git_repository
from mapping_suite_sdk.adapters.repository import MongoDBRepository, ModelNotFoundError


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
        with pytest.raises(NotADirectoryError):
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


def test_load_mapping_packages_from_github_with_success(dummy_github_project_path: Path,
                                                        dummy_github_branch_name: str,
                                                        dummy_packages_path_pattern: str):
    with _setup_temporary_test_git_repository(dummy_github_project_path, dummy_github_branch_name) as repo_path:
        mapping_packages: List[MappingPackage] = load_mapping_packages_from_github(
            github_repository_url=str(repo_path),
            packages_path_pattern=dummy_packages_path_pattern,
            branch_or_tag_name=dummy_github_branch_name)

        assert len(mapping_packages) > 0
        for mapping_package in mapping_packages:
            assert_valid_mapping_package(mapping_package)


def test_load_mapping_packages_from_github_fails_on_null_url(dummy_github_branch_name: str,
                                                             dummy_packages_path_pattern: str):
    with pytest.raises(ValueError):
        load_mapping_packages_from_github(
            github_repository_url=None,
            packages_path_pattern=dummy_packages_path_pattern,
            branch_or_tag_name=dummy_github_branch_name)


def test_load_mapping_packages_from_github_fails_on_null_pattern(dummy_github_project_path: Path,
                                                                 dummy_github_branch_name: str):
    with pytest.raises(ValueError):
        load_mapping_packages_from_github(
            github_repository_url=str(dummy_github_project_path),
            packages_path_pattern=None,
            branch_or_tag_name=dummy_github_branch_name)


def test_load_mapping_packages_from_github_success_on_null_branch_or_tag_name(dummy_github_project_path: Path,
                                                                              dummy_packages_path_pattern: str):
    with _setup_temporary_test_git_repository(dummy_github_project_path) as repo_path:
        mapping_packages = load_mapping_packages_from_github(
            github_repository_url=str(repo_path),
            packages_path_pattern=dummy_packages_path_pattern,
            branch_or_tag_name=None)

        assert len(mapping_packages) > 0
        for mapping_package in mapping_packages:
            assert_valid_mapping_package(mapping_package)


def test_load_mapping_packages_from_github_fails_on_non_existing_branch_or_tag_name(dummy_github_project_path: Path,
                                                                                    dummy_packages_path_pattern: str,
                                                                                    dummy_non_existing_github_branch_name: str):
    with _setup_temporary_test_git_repository(dummy_github_project_path) as repo_path:
        with pytest.raises(ValueError):
            load_mapping_packages_from_github(github_repository_url=str(repo_path),
                                              packages_path_pattern=dummy_packages_path_pattern,
                                              branch_or_tag_name=dummy_non_existing_github_branch_name)


def test_load_mapping_packages_from_github_success_get_all_packages_pattern(dummy_github_project_path: Path,
                                                                            dummy_get_all_packages_pattern: str):
    with _setup_temporary_test_git_repository(dummy_github_project_path) as repo_path:
        mapping_packages = load_mapping_packages_from_github(
            github_repository_url=str(repo_path),
            packages_path_pattern=dummy_get_all_packages_pattern,
            branch_or_tag_name=None)

        assert len(mapping_packages) > 0
        for mapping_package in mapping_packages:
            assert_valid_mapping_package(mapping_package)


def test_load_mapping_packages_from_github_fails_on_non_existing_pattern(dummy_github_project_path: Path,
                                                                         dummy_non_existing_pattern: str):
    with _setup_temporary_test_git_repository(dummy_github_project_path) as repo_path:
        with pytest.raises(ValueError):
            load_mapping_packages_from_github(github_repository_url=str(repo_path),
                                              packages_path_pattern=dummy_non_existing_pattern)


def test_load_mapping_package_from_mongo_db_fails_on_invalid_id(dummy_mongo_repository: MongoDBRepository):
    with pytest.raises(ValueError):
        load_mapping_package_from_mongo_db(mapping_package_id="",
                                           mapping_package_repository=dummy_mongo_repository)
    with pytest.raises(ValueError):
        load_mapping_package_from_mongo_db(mapping_package_id=None,
                                           mapping_package_repository=dummy_mongo_repository)


def test_load_mapping_package_from_mongo_db_fails_on_invalid_repository(dummy_mongo_repository: MongoDBRepository,
                                                                        dummy_mapping_package_model: MappingPackage):
    with pytest.raises(ValueError):
        load_mapping_package_from_mongo_db(mapping_package_id=dummy_mapping_package_model.id,
                                           mapping_package_repository=None)


def test_load_mapping_package_from_mongo_db_package_fails_on_id_not_found(dummy_mongo_repository: MongoDBRepository,
                                                                          dummy_mapping_package_model: MappingPackage):
    with pytest.raises(ModelNotFoundError):
        load_mapping_package_from_mongo_db(mapping_package_id="non_existing_id",
                                           mapping_package_repository=dummy_mongo_repository)


def test_load_mapping_package_from_mongo_db_with_success(mongo_client: mongomock.MongoClient,
                                                         dummy_mapping_package_model: MappingPackage):
    model_id = dummy_mapping_package_model.id
    model_dict = dummy_mapping_package_model.model_dump(by_alias=True, mode="json")
    model_dict["_id"] = model_id

    mongodb_repo = MongoDBRepository(
        model_class=MappingPackage,
        mongo_client=mongo_client,
        database_name="test_db"
    )
    mongodb_repo.collection.insert_one(model_dict)

    mapping_package = load_mapping_package_from_mongo_db(
        mapping_package_id=dummy_mapping_package_model.id,
        mapping_package_repository=mongodb_repo
    )

    assert mapping_package == dummy_mapping_package_model

