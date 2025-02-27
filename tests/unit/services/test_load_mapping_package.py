import shutil
import tempfile
from pathlib import Path

import mongomock
import pytest

from mapping_suite_sdk.adapters.extractor import ArchiveExtractor
from mapping_suite_sdk.adapters.loader import MappingPackageLoader
from mapping_suite_sdk.adapters.repository import MongoDBRepository, ModelNotFoundError
from mapping_suite_sdk.models.mapping_package import MappingPackage
from mapping_suite_sdk.services.load_mapping_package import load_mapping_package_from_folder, \
    load_mapping_package_from_archive, load_mapping_package_from_mongo_db
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
        archive_unpacker=ArchiveExtractor())

    assert_valid_mapping_package(mapping_package=mapping_package)


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
