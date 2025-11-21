import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from mapping_suite_sdk.core.adapters.extractor import ArchiveExtractor
from mapping_suite_sdk.core.adapters.repository import MongoDBRepository
from mapping_suite_sdk.mapping_package_v3.adapters.package_loader import MappingPackageV3Loader
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
from mapping_suite_sdk.mapping_package_v3.services.load_mapping_package_v3 import (
    load_mapping_package_v3_from_folder,
    load_mapping_package_v3_from_archive,
    load_mapping_packages_v3_from_github,
    load_mapping_package_v2_from_mongo_db
)


def test_load_mapping_package_v3_from_folder_success(dummy_mapping_package_v3_path: Path):
    result = load_mapping_package_v3_from_folder(dummy_mapping_package_v3_path)

    assert isinstance(result, MappingPackageV3)
    assert result.metadata is not None
    assert result.conceptual_mapping_asset is not None
    assert result.technical_mapping_suite is not None
    assert result.vocabulary_mapping_suite is not None


def test_load_mapping_package_v3_from_folder_with_custom_loader(dummy_mapping_package_v3_path: Path):
    custom_loader = MappingPackageV3Loader(include_test_data=False, include_output=False)

    result = load_mapping_package_v3_from_folder(dummy_mapping_package_v3_path, custom_loader)

    assert isinstance(result, MappingPackageV3)
    assert len(result.test_data_suites) == 0


def test_load_mapping_package_v3_from_folder_nonexistent_path():
    nonexistent_path = Path("/nonexistent/path")

    with pytest.raises(FileNotFoundError) as exc_info:
        load_mapping_package_v3_from_folder(nonexistent_path)

    assert "Mapping package folder not found" in str(exc_info.value)
    assert str(nonexistent_path) in str(exc_info.value)


def test_load_mapping_package_v3_from_folder_not_directory():
    with tempfile.NamedTemporaryFile() as temp_file:
        file_path = Path(temp_file.name)

        with pytest.raises(NotADirectoryError) as exc_info:
            load_mapping_package_v3_from_folder(file_path)

        assert "Specified path is not a directory" in str(exc_info.value)


def test_load_mapping_package_v3_from_archive_success(dummy_mapping_package_v3_archive_path: Path):
    result = load_mapping_package_v3_from_archive(dummy_mapping_package_v3_archive_path)

    assert isinstance(result, MappingPackageV3)
    assert result.metadata is not None
    assert result.conceptual_mapping_asset is not None
    assert result.technical_mapping_suite is not None
    assert result.vocabulary_mapping_suite is not None


def test_load_mapping_package_v3_from_archive_with_custom_loader(dummy_mapping_package_v3_archive_path: Path):
    custom_loader = MappingPackageV3Loader(include_test_data=False, include_output=False)

    result = load_mapping_package_v3_from_archive(dummy_mapping_package_v3_archive_path, custom_loader)

    assert isinstance(result, MappingPackageV3)
    assert len(result.test_data_suites) == 0


def test_load_mapping_package_v3_from_archive_with_custom_extractor(dummy_mapping_package_v3_archive_path: Path):
    custom_extractor = ArchiveExtractor()

    result = load_mapping_package_v3_from_archive(
        dummy_mapping_package_v3_archive_path,
        archive_unpacker=custom_extractor
    )

    assert isinstance(result, MappingPackageV3)


def test_load_mapping_package_v3_from_archive_nonexistent_file():
    nonexistent_path = Path("/nonexistent/archive.zip")

    with pytest.raises(FileNotFoundError) as exc_info:
        load_mapping_package_v3_from_archive(nonexistent_path)

    assert "Mapping package archive not found" in str(exc_info.value)


def test_load_mapping_package_v3_from_archive_not_file():
    with tempfile.TemporaryDirectory() as temp_dir:
        dir_path = Path(temp_dir)

        with pytest.raises(ValueError) as exc_info:
            load_mapping_package_v3_from_archive(dir_path)

        assert "Specified path is not a file" in str(exc_info.value)


def test_load_mapping_packages_v3_from_github_empty_repo_url():
    with pytest.raises(ValueError) as exc_info:
        load_mapping_packages_v3_from_github("", "pattern", "branch")

    assert "Repository URL is required" in str(exc_info.value)


def test_load_mapping_packages_v3_from_github_empty_pattern():
    with pytest.raises(ValueError) as exc_info:
        load_mapping_packages_v3_from_github("https://github.com/test/repo", "", "branch")

    assert "Packages path pattern is required" in str(exc_info.value)


def test_load_mapping_package_v3_from_mongo_db_success():
    mock_repository = Mock(spec=MongoDBRepository)
    mock_package = Mock(spec=MappingPackageV3)
    mock_repository.read.return_value = mock_package

    result = load_mapping_package_v2_from_mongo_db("test_id", mock_repository)

    mock_repository.read.assert_called_once_with("test_id")
    assert result == mock_package


def test_load_mapping_package_v3_from_mongo_db_empty_id():
    mock_repository = Mock(spec=MongoDBRepository)

    with pytest.raises(ValueError) as exc_info:
        load_mapping_package_v2_from_mongo_db("", mock_repository)

    assert "Mapping package ID must be provided" in str(exc_info.value)


def test_load_mapping_package_v3_from_mongo_db_none_id():
    mock_repository = Mock(spec=MongoDBRepository)

    with pytest.raises(ValueError) as exc_info:
        load_mapping_package_v2_from_mongo_db(None, mock_repository)

    assert "Mapping package ID must be provided" in str(exc_info.value)


def test_load_mapping_package_v3_from_mongo_db_none_repository():
    with pytest.raises(ValueError) as exc_info:
        load_mapping_package_v2_from_mongo_db("test_id", None)

    assert "MongoDB repository must be provided" in str(exc_info.value)


def test_load_mapping_package_v3_from_mongo_db_repository_exception():
    mock_repository = Mock(spec=MongoDBRepository)
    mock_repository.read.side_effect = Exception("Database connection failed")

    with pytest.raises(Exception) as exc_info:
        load_mapping_package_v2_from_mongo_db("test_id", mock_repository)

    assert "Database connection failed" in str(exc_info.value)


def test_load_mapping_package_v3_from_folder_tracer_decoration():
    assert hasattr(load_mapping_package_v3_from_folder, '__name__')
    assert load_mapping_package_v3_from_folder.__name__ == 'load_mapping_package_v3_from_folder'


def test_load_mapping_package_v3_from_archive_tracer_decoration():
    assert hasattr(load_mapping_package_v3_from_archive, '__name__')
    assert load_mapping_package_v3_from_archive.__name__ == 'load_mapping_package_v3_from_archive'


def test_load_mapping_packages_v3_from_github_tracer_decoration():
    assert hasattr(load_mapping_packages_v3_from_github, '__name__')
    assert load_mapping_packages_v3_from_github.__name__ == 'load_mapping_packages_v3_from_github'


def test_load_mapping_package_v3_from_mongo_db_tracer_decoration():
    assert hasattr(load_mapping_package_v2_from_mongo_db, '__name__')
    assert load_mapping_package_v2_from_mongo_db.__name__ == 'load_mapping_package_v2_from_mongo_db'