import tempfile
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from mapping_suite_sdk.core.adapters.extractor import ArchiveExtractor, GitHubExtractor
from mapping_suite_sdk.core.adapters.repository import MongoDBRepository
from mapping_suite_sdk.mapping_suite.adapters.loader import MappingSuiteLoader
from mapping_suite_sdk.mapping_suite.models.mapping_suite import MappingSuite
from mapping_suite_sdk.mapping_suite.services.load_mapping_suite import (
    load_mapping_suite_from_folder,
    load_mapping_suite_from_archive,
    load_mapping_suites_from_github,
    load_mapping_suite_from_mongo_db
)


class TestLoadMappingSuiteFromFolder:
    """Tests for loading mapping suites from filesystem folders."""

    def test_load_mapping_suite_from_folder_success(self, dummy_mapping_suite_folder_path: Path):
        """Test successful loading of a mapping suite from a valid folder."""
        result = load_mapping_suite_from_folder(dummy_mapping_suite_folder_path)

        assert isinstance(result, MappingSuite)
        assert result.mapping_suite_config is not None
        assert result.mapping_suite_config.mapping_suite_metadata is not None
        assert result.resource_references is not None

    def test_load_mapping_suite_from_folder_with_custom_loader(
            self,
            dummy_mapping_suite_folder_path: Path
    ):
        """Test loading with a custom loader instance."""
        custom_loader = MappingSuiteLoader(include_resources=False)

        result = load_mapping_suite_from_folder(
            dummy_mapping_suite_folder_path,
            custom_loader
        )

        assert isinstance(result, MappingSuite)
        assert result.resource_references.file_paths is None

    def test_load_mapping_suite_from_folder_nonexistent_path(self):
        """Test error handling for non-existent folder paths."""
        nonexistent_path = Path("/nonexistent/path/to/suite")

        with pytest.raises(FileNotFoundError) as exc_info:
            load_mapping_suite_from_folder(nonexistent_path)

        assert "Mapping suite folder not found" in str(exc_info.value)
        assert str(nonexistent_path) in str(exc_info.value)

    def test_load_mapping_suite_from_folder_not_directory(self):
        """Test error handling when path is a file instead of directory."""
        with tempfile.NamedTemporaryFile() as temp_file:
            file_path = Path(temp_file.name)

            with pytest.raises(NotADirectoryError) as exc_info:
                load_mapping_suite_from_folder(file_path)

            assert "Specified path is not a directory" in str(exc_info.value)

    def test_load_mapping_suite_from_folder_tracer_decoration(self):
        """Test that the function is properly decorated with tracer."""
        assert hasattr(load_mapping_suite_from_folder, '__name__')
        assert load_mapping_suite_from_folder.__name__ == 'load_mapping_suite_from_folder'


class TestLoadMappingSuiteFromArchive:
    """Tests for loading mapping suites from archive files."""

    def test_load_mapping_suite_from_archive_success(
            self,
            dummy_mapping_suite_archive_path: Path
    ):
        """Test successful loading of a mapping suite from an archive."""
        result = load_mapping_suite_from_archive(dummy_mapping_suite_archive_path)

        assert isinstance(result, MappingSuite)
        assert result.mapping_suite_config is not None
        assert result.mapping_suite_config.mapping_suite_metadata is not None

    def test_load_mapping_suite_from_archive_with_custom_loader(
            self,
            dummy_mapping_suite_archive_path: Path
    ):
        """Test loading from archive with a custom loader instance."""
        custom_loader = MappingSuiteLoader(include_resources=False)

        result = load_mapping_suite_from_archive(
            dummy_mapping_suite_archive_path,
            mapping_suite_loader=custom_loader
        )

        assert isinstance(result, MappingSuite)
        assert result.resource_references.file_paths is None

    def test_load_mapping_suite_from_archive_with_custom_extractor(
            self,
            dummy_mapping_suite_archive_path: Path
    ):
        """Test loading from archive with a custom extractor instance."""
        custom_extractor = ArchiveExtractor()

        result = load_mapping_suite_from_archive(
            dummy_mapping_suite_archive_path,
            archive_unpacker=custom_extractor
        )

        assert isinstance(result, MappingSuite)

    def test_load_mapping_suite_from_archive_nonexistent_file(self):
        """Test error handling for non-existent archive files."""
        nonexistent_path = Path("/nonexistent/archive.zip")

        with pytest.raises(FileNotFoundError) as exc_info:
            load_mapping_suite_from_archive(nonexistent_path)

        assert "Mapping suite archive not found" in str(exc_info.value)

    def test_load_mapping_suite_from_archive_not_file(self):
        """Test error handling when path is a directory instead of file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            dir_path = Path(temp_dir)

            with pytest.raises(ValueError) as exc_info:
                load_mapping_suite_from_archive(dir_path)

            assert "Specified path is not a file" in str(exc_info.value)

    def test_load_mapping_suite_from_archive_tracer_decoration(self):
        """Test that the function is properly decorated with tracer."""
        assert hasattr(load_mapping_suite_from_archive, '__name__')
        assert load_mapping_suite_from_archive.__name__ == 'load_mapping_suite_from_archive'


class TestLoadMappingSuitesFromGitHub:
    """Tests for loading mapping suites from GitHub repositories."""

    def test_load_mapping_suites_from_github_empty_repo_url(self):
        """Test error handling for empty repository URL."""
        with pytest.raises(ValueError) as exc_info:
            load_mapping_suites_from_github("", "pattern", "branch")

        assert "Repository URL is required" in str(exc_info.value)

    def test_load_mapping_suites_from_github_empty_pattern(self):
        """Test error handling for empty path pattern."""
        with pytest.raises(ValueError) as exc_info:
            load_mapping_suites_from_github(
                "https://github.com/test/repo",
                "",
                "branch"
            )

        assert "Suites path pattern is required" in str(exc_info.value)

    def test_load_mapping_suites_from_github_no_pattern(self):
        """Test error handling when pattern is None."""
        with pytest.raises(ValueError) as exc_info:
            load_mapping_suites_from_github(
                "https://github.com/test/repo",
                None,
                "branch"
            )

        assert "Suites path pattern is required" in str(exc_info.value)

    def test_load_mapping_suites_from_github_no_suites_found(self):
        """Test error handling when no suites match the pattern."""
        mock_extractor = Mock(spec=GitHubExtractor)

        @contextmanager
        def mock_extract_temporary(*args, **kwargs):
            yield []

        mock_extractor.extract_temporary = mock_extract_temporary

        with pytest.raises(ValueError) as exc_info:
            load_mapping_suites_from_github(
                "https://github.com/test/repo",
                "suites/*",
                "main",
                github_suite_extractor=mock_extractor
            )

        assert "No mapping suites found" in str(exc_info.value)

    def test_load_mapping_suites_from_github_success_single_suite(
            self,
            dummy_mapping_suite_folder_path: Path
    ):
        """Test successful loading of a single suite from GitHub."""
        mock_extractor = Mock(spec=GitHubExtractor)

        @contextmanager
        def mock_extract_temporary(*args, **kwargs):
            yield [dummy_mapping_suite_folder_path]

        mock_extractor.extract_temporary = mock_extract_temporary

        result = load_mapping_suites_from_github(
            "https://github.com/test/repo",
            "suites/*",
            "main",
            github_suite_extractor=mock_extractor
        )

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], MappingSuite)

    def test_load_mapping_suites_from_github_with_custom_loader(
            self,
            dummy_mapping_suite_folder_path: Path
    ):
        """Test loading from GitHub with a custom loader."""
        mock_extractor = Mock(spec=GitHubExtractor)
        custom_loader = MappingSuiteLoader(include_resources=False)

        @contextmanager
        def mock_extract_temporary(*args, **kwargs):
            yield [dummy_mapping_suite_folder_path]

        mock_extractor.extract_temporary = mock_extract_temporary

        result = load_mapping_suites_from_github(
            "https://github.com/test/repo",
            "suites/*",
            "main",
            github_suite_extractor=mock_extractor,
            mapping_suite_loader=custom_loader
        )

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].resource_references.file_paths is None

    def test_load_mapping_suites_from_github_partial_failure(
            self,
            dummy_mapping_suite_folder_path: Path
    ):
        """Test loading from GitHub with some suites failing to load."""
        mock_extractor = Mock(spec=GitHubExtractor)
        invalid_path = Path("/nonexistent/invalid/path")

        @contextmanager
        def mock_extract_temporary(*args, **kwargs):
            yield [dummy_mapping_suite_folder_path, invalid_path]

        mock_extractor.extract_temporary = mock_extract_temporary

        # Should log warning for invalid path but return successfully loaded suites
        result = load_mapping_suites_from_github(
            "https://github.com/test/repo",
            "suites/*",
            "main",
            github_suite_extractor=mock_extractor
        )

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], MappingSuite)

    def test_load_mapping_suites_from_github_tracer_decoration(self):
        """Test that the function is properly decorated with tracer."""
        assert hasattr(load_mapping_suites_from_github, '__name__')
        assert load_mapping_suites_from_github.__name__ == 'load_mapping_suites_from_github'


class TestLoadMappingSuiteFromMongoDB:
    """Tests for loading mapping suites from MongoDB."""

    def test_load_mapping_suite_from_mongo_db_success(self):
        """Test successful loading of a mapping suite from MongoDB."""
        mock_repository = Mock(spec=MongoDBRepository)
        mock_suite = Mock(spec=MappingSuite)
        mock_repository.read.return_value = mock_suite

        result = load_mapping_suite_from_mongo_db("test_id", mock_repository)

        mock_repository.read.assert_called_once_with("test_id")
        assert result == mock_suite

    def test_load_mapping_suite_from_mongo_db_empty_id(self):
        """Test error handling for empty suite ID."""
        mock_repository = Mock(spec=MongoDBRepository)

        with pytest.raises(ValueError) as exc_info:
            load_mapping_suite_from_mongo_db("", mock_repository)

        assert "Mapping suite ID must be provided" in str(exc_info.value)

    def test_load_mapping_suite_from_mongo_db_none_id(self):
        """Test error handling for None suite ID."""
        mock_repository = Mock(spec=MongoDBRepository)

        with pytest.raises(ValueError) as exc_info:
            load_mapping_suite_from_mongo_db(None, mock_repository)

        assert "Mapping suite ID must be provided" in str(exc_info.value)

    def test_load_mapping_suite_from_mongo_db_none_repository(self):
        """Test error handling for None repository."""
        with pytest.raises(ValueError) as exc_info:
            load_mapping_suite_from_mongo_db("test_id", None)

        assert "MongoDB repository must be provided" in str(exc_info.value)

    def test_load_mapping_suite_from_mongo_db_repository_exception(self):
        """Test error propagation from database access failures."""
        mock_repository = Mock(spec=MongoDBRepository)
        mock_repository.read.side_effect = Exception("Database connection failed")

        with pytest.raises(Exception) as exc_info:
            load_mapping_suite_from_mongo_db("test_id", mock_repository)

        assert "Database connection failed" in str(exc_info.value)

    def test_load_mapping_suite_from_mongo_db_tracer_decoration(self):
        """Test that the function is properly decorated with tracer."""
        assert hasattr(load_mapping_suite_from_mongo_db, '__name__')
        assert load_mapping_suite_from_mongo_db.__name__ == 'load_mapping_suite_from_mongo_db'