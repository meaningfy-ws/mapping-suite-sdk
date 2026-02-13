"""
Unit tests for the load_mapping_package service.

Tests focus on service-layer orchestration:
- Path and version handling
- Version detection and routing
- Optional validation (before and after conversion)
- Target version from include_test_data
- Optional MongoDB persistence
"""
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_lightweight import (
    MappingPackageV3Lightweight,
)
from mapping_suite_sdk.tools.services.convert_mapping_package import Version
from mapping_suite_sdk.tools.services.load_mapping_package import (
    InvalidPackagePathError,
    UnsupportedConversionError,
    UnsupportedVersionError,
    VersionDetectionError,
    load_mapping_package,
)


class TestLoadMappingPackagePathValidation:
    """Path validation at service entry."""

    def test_raises_when_path_does_not_exist(self):
        path = Path("/nonexistent/package")
        with pytest.raises(InvalidPackagePathError, match="does not exist"):
            load_mapping_package(path, version="v2")

    def test_raises_when_path_is_not_directory(self, tmp_path: Path):
        file_path = tmp_path / "file.txt"
        file_path.write_text("x")
        with pytest.raises(InvalidPackagePathError, match="not a directory"):
            load_mapping_package(file_path, version="v2")


class TestLoadMappingPackageVersionHandling:
    """Explicit version and auto-detection."""

    @patch(
        "mapping_suite_sdk.tools.services.load_mapping_package.load_mapping_package_from_folder"
    )
    def test_explicit_version_skips_detection(self, mock_load, tmp_path: Path):
        mock_load.return_value = Mock(spec=MappingPackageV3)
        load_mapping_package(tmp_path, version="v3", include_test_data=True, validate_package=False)
        mock_load.assert_called_once_with(Version.V3, tmp_path)

    @patch(
        "mapping_suite_sdk.tools.services.load_mapping_package.detect_mapping_package_version"
    )
    @patch(
        "mapping_suite_sdk.tools.services.load_mapping_package.load_mapping_package_from_folder"
    )
    def test_no_version_triggers_detection(self, mock_load, mock_detect, tmp_path: Path):
        mock_detect.return_value = "v2"
        mock_load.return_value = Mock(spec=MappingPackageV3)
        with patch(
            "mapping_suite_sdk.tools.services.load_mapping_package.convert_mapping_package_model"
        ) as mock_convert:
            mock_convert.return_value = Mock(spec=MappingPackageV3)
            load_mapping_package(tmp_path, include_test_data=True, validate_package=False)
        mock_detect.assert_called_once_with(tmp_path)
        mock_load.assert_called_once_with(Version.V2, tmp_path)

    @patch(
        "mapping_suite_sdk.tools.services.load_mapping_package.detect_mapping_package_version"
    )
    def test_detection_failure_raises(self, mock_detect, tmp_path: Path):
        mock_detect.return_value = None
        with pytest.raises(VersionDetectionError, match="Could not detect"):
            load_mapping_package(tmp_path, validate_package=False)

    def test_unsupported_version_string_raises(self, tmp_path: Path):
        with pytest.raises(UnsupportedVersionError, match="Unsupported version"):
            load_mapping_package(tmp_path, version="v99", validate_package=False)

    @patch(
        "mapping_suite_sdk.mapping_package_v3.services.load_mapping_package_v3_lightweight.load_mapping_package_v3_lightweight_from_folder"
    )
    def test_version_normalized_case_insensitive_v3l(self, mock_v3l_load, tmp_path: Path):
        mock_v3l_load.return_value = Mock(spec=MappingPackageV3Lightweight)
        result = load_mapping_package(
            tmp_path, version="  v3L  ", include_test_data=False, validate_package=False
        )
        mock_v3l_load.assert_called_once_with(
            mapping_package_folder_path=tmp_path,
        )
        assert result is mock_v3l_load.return_value


class TestLoadMappingPackageIncludeTestDataAndConversion:
    """Target version (v3 vs v3L) and conversion routing."""

    @patch(
        "mapping_suite_sdk.tools.services.load_mapping_package.convert_mapping_package_model"
    )
    @patch(
        "mapping_suite_sdk.tools.services.load_mapping_package.load_mapping_package_from_folder"
    )
    def test_include_test_data_true_targets_v3(
        self, mock_load, mock_convert, tmp_path: Path
    ):
        source = Mock(spec=MappingPackageV3)
        converted = Mock(spec=MappingPackageV3)
        mock_load.return_value = source
        mock_convert.return_value = converted
        result = load_mapping_package(
            tmp_path, version="v2", include_test_data=True, validate_package=False
        )
        mock_convert.assert_called_once_with(Version.V2, Version.V3, source)
        assert result is converted

    @patch(
        "mapping_suite_sdk.tools.services.load_mapping_package.convert_mapping_package_model"
    )
    @patch(
        "mapping_suite_sdk.tools.services.load_mapping_package.load_mapping_package_from_folder"
    )
    def test_include_test_data_false_targets_v3l(
        self, mock_load, mock_convert, tmp_path: Path
    ):
        source = Mock(spec=MappingPackageV3)
        converted = Mock(spec=MappingPackageV3Lightweight)
        mock_load.return_value = source
        mock_convert.return_value = converted
        result = load_mapping_package(
            tmp_path, version="v3", include_test_data=False, validate_package=False
        )
        mock_convert.assert_called_once_with(Version.V3, Version.V3L, source)
        assert result is converted

    @patch(
        "mapping_suite_sdk.mapping_package_v3.services.load_mapping_package_v3_lightweight.load_mapping_package_v3_lightweight_from_folder"
    )
    def test_v3l_source_with_include_test_data_true_raises(
        self, mock_v3l_load, tmp_path: Path
    ):
        mock_v3l_load.return_value = Mock(spec=MappingPackageV3Lightweight)
        with pytest.raises(
            UnsupportedConversionError,
            match="Cannot produce v3.*from a v3L source",
        ):
            load_mapping_package(
                tmp_path, version="v3L", include_test_data=True, validate_package=False
            )

    @patch(
        "mapping_suite_sdk.mapping_package_v3.services.load_mapping_package_v3_lightweight.load_mapping_package_v3_lightweight_from_folder"
    )
    def test_v3l_source_with_include_test_data_false_returns_without_conversion(
        self, mock_v3l_load, tmp_path: Path
    ):
        pkg = Mock(spec=MappingPackageV3Lightweight)
        mock_v3l_load.return_value = pkg
        with patch(
            "mapping_suite_sdk.tools.services.load_mapping_package.convert_mapping_package_model"
        ) as mock_convert:
            result = load_mapping_package(
                tmp_path, version="v3L", include_test_data=False, validate_package=False
            )
            mock_convert.assert_not_called()
        assert result is pkg


class TestLoadMappingPackageValidation:
    """Optional validation before and after conversion."""

    @patch(
        "mapping_suite_sdk.tools.services.validate_mapping_package.validate_mapping_package"
    )
    @patch(
        "mapping_suite_sdk.tools.services.load_mapping_package.convert_mapping_package_model"
    )
    @patch(
        "mapping_suite_sdk.tools.services.load_mapping_package.load_mapping_package_from_folder"
    )
    def test_validate_package_true_validates_before_and_after(
        self, mock_load, mock_convert, mock_validate, tmp_path: Path
    ):
        source = Mock(spec=MappingPackageV3)
        converted = Mock(spec=MappingPackageV3)
        mock_load.return_value = source
        mock_convert.return_value = converted
        load_mapping_package(
            tmp_path,
            version="v2",
            include_test_data=True,
            validate_package=True,
        )
        assert mock_validate.call_count == 2
        first_call = mock_validate.call_args_list[0]
        second_call = mock_validate.call_args_list[1]
        assert first_call[0][0] == tmp_path
        assert first_call[1].get("version") == "v2"
        assert second_call[0][0] is converted

    @patch(
        "mapping_suite_sdk.tools.services.validate_mapping_package.validate_mapping_package"
    )
    @patch(
        "mapping_suite_sdk.tools.services.load_mapping_package.load_mapping_package_from_folder"
    )
    def test_validate_package_false_skips_validation(
        self, mock_load, mock_validate, tmp_path: Path
    ):
        mock_load.return_value = Mock(spec=MappingPackageV3)
        load_mapping_package(
            tmp_path, version="v3", include_test_data=True, validate_package=False
        )
        mock_validate.assert_not_called()


class TestLoadMappingPackageMongoDBPersistence:
    """Optional persist to MongoDB."""

    @patch(
        "mapping_suite_sdk.tools.services.load_mapping_package._persist_to_mongodb"
    )
    @patch(
        "mapping_suite_sdk.tools.services.load_mapping_package.load_mapping_package_from_folder"
    )
    def test_persist_to_mongodb_calls_saver(
        self, mock_load, mock_persist, tmp_path: Path
    ):
        pkg = Mock(spec=MappingPackageV3)
        mock_load.return_value = pkg
        mock_persist.return_value = pkg
        client = MagicMock()
        load_mapping_package(
            tmp_path,
            version="v3",
            include_test_data=True,
            persist_to_mongodb=True,
            mongo_client=client,
            database_name="db",
            collection_name="coll",
            validate_package=False,
        )
        mock_persist.assert_called_once_with(
            pkg, client, "db", "coll"
        )

    def test_persist_to_mongodb_without_client_raises(self, tmp_path: Path):
        with patch(
            "mapping_suite_sdk.tools.services.load_mapping_package.load_mapping_package_from_folder"
        ) as mock_load:
            mock_load.return_value = Mock(spec=MappingPackageV3)
            with pytest.raises(ValueError, match="mongo_client and database_name"):
                load_mapping_package(
                    tmp_path,
                    version="v3",
                    include_test_data=True,
                    persist_to_mongodb=True,
                    database_name="db",
                    validate_package=False,
                )

    def test_persist_to_mongodb_without_database_name_raises(self, tmp_path: Path):
        with patch(
            "mapping_suite_sdk.tools.services.load_mapping_package.load_mapping_package_from_folder"
        ) as mock_load:
            mock_load.return_value = Mock(spec=MappingPackageV3)
            with pytest.raises(ValueError, match="mongo_client and database_name"):
                load_mapping_package(
                    tmp_path,
                    version="v3",
                    include_test_data=True,
                    persist_to_mongodb=True,
                    mongo_client=MagicMock(),
                    validate_package=False,
                )

    @patch(
        "mapping_suite_sdk.mapping_package_v3.services.save_mapping_package_v3_lightweight.save_mapping_package_v3_lightweight_to_mongo_db"
    )
    @patch(
        "mapping_suite_sdk.mapping_package_v3.services.save_mapping_package_v3.save_mapping_package_v3_to_mongo_db"
    )
    def test_persist_to_mongodb_calls_v3_saver(
        self, mock_save_v3, mock_save_v3l
    ):
        from tests import TEST_DATA_EXAMPLE_V3_MAPPING_PACKAGE_FOLDER_PATH
        mock_save_v3.return_value = Mock(spec=MappingPackageV3)
        client = MagicMock()
        load_mapping_package(
            TEST_DATA_EXAMPLE_V3_MAPPING_PACKAGE_FOLDER_PATH,
            version="v3",
            include_test_data=True,
            persist_to_mongodb=True,
            mongo_client=client,
            database_name="db",
            collection_name="coll",
            validate_package=False,
        )
        mock_save_v3.assert_called_once()
        assert mock_save_v3.call_args[1]["mapping_package"] is not None
        assert mock_save_v3.call_args[1]["mongo_client"] is client
        assert mock_save_v3.call_args[1]["database_name"] == "db"
        assert mock_save_v3.call_args[1]["collection_name"] == "coll"
        mock_save_v3l.assert_not_called()

    @patch(
        "mapping_suite_sdk.mapping_package_v3.services.save_mapping_package_v3_lightweight.save_mapping_package_v3_lightweight_to_mongo_db"
    )
    @patch(
        "mapping_suite_sdk.mapping_package_v3.services.save_mapping_package_v3.save_mapping_package_v3_to_mongo_db"
    )
    def test_persist_to_mongodb_calls_v3l_saver(
        self, mock_save_v3, mock_save_v3l
    ):
        from tests import TEST_DATA_EXAMPLE_V3L_MAPPING_PACKAGE_FOLDER_PATH
        mock_save_v3l.return_value = Mock(spec=MappingPackageV3Lightweight)
        client = MagicMock()
        load_mapping_package(
            TEST_DATA_EXAMPLE_V3L_MAPPING_PACKAGE_FOLDER_PATH,
            version="v3L",
            include_test_data=False,
            persist_to_mongodb=True,
            mongo_client=client,
            database_name="db",
            validate_package=False,
        )
        mock_save_v3l.assert_called_once()
        assert mock_save_v3l.call_args[1]["mapping_package"] is not None
        assert mock_save_v3l.call_args[1]["database_name"] == "db"
        mock_save_v3.assert_not_called()

    def test_persist_to_mongodb_unsupported_type_raises(self):
        from mapping_suite_sdk.tools.services.load_mapping_package import (
            _persist_to_mongodb,
        )
        client = MagicMock()
        invalid_package = Mock()
        with pytest.raises(
            UnsupportedConversionError,
            match="Cannot persist to MongoDB: unsupported package type",
        ):
            _persist_to_mongodb(
                invalid_package,
                client,
                "db",
                "coll",
            )


class TestLoadMappingPackageV3NoConversion:
    """When source is already target version, no conversion."""

    @patch(
        "mapping_suite_sdk.tools.services.load_mapping_package.convert_mapping_package_model"
    )
    @patch(
        "mapping_suite_sdk.tools.services.load_mapping_package.load_mapping_package_from_folder"
    )
    def test_v3_source_target_v3_returns_same_instance(
        self, mock_load, mock_convert, tmp_path: Path
    ):
        pkg = Mock(spec=MappingPackageV3)
        mock_load.return_value = pkg
        result = load_mapping_package(
            tmp_path, version="v3", include_test_data=True, validate_package=False
        )
        mock_convert.assert_not_called()
        assert result is pkg


# ---------------------------------------------------------------------------
# Integration tests: run the service against actual packages in tests/test_data
# All supported source → target combinations (service only outputs v3 or v3L).
# Assertions verify real content from disk (metadata, mappings) to confirm we
# are not mocking and that actual package data is loaded.
# ---------------------------------------------------------------------------

class TestLoadMappingPackageIntegration:
    """
    Tests against actual v1, v2, v3 and v3L packages under tests/test_data.

    Uses real folder paths; loads and converts real package content from disk.
    Asserts on metadata and mapping content to ensure actual packages are used.

    Covers: v1→v3, v1→v3L, v2→v3, v2→v3L, v3→v3, v3→v3L, v3L→v3L, v3L→v3 (raises).
    """

    def test_v1_to_v3(self):
        from tests import TEST_DATA_EXAMPLE_SF_MAPPING_PACKAGE_FOLDER_PATH
        assert TEST_DATA_EXAMPLE_SF_MAPPING_PACKAGE_FOLDER_PATH.exists()
        pkg = load_mapping_package(
            TEST_DATA_EXAMPLE_SF_MAPPING_PACKAGE_FOLDER_PATH,
            include_test_data=True,
            validate_package=False,
        )
        assert isinstance(pkg, MappingPackageV3)
        assert pkg.metadata.id == "package_F22"
        assert pkg.technical_mapping_suite is not None
        assert len(pkg.technical_mapping_suite.files) >= 1

    def test_v1_to_v3l(self):
        from tests import TEST_DATA_EXAMPLE_SF_MAPPING_PACKAGE_FOLDER_PATH
        assert TEST_DATA_EXAMPLE_SF_MAPPING_PACKAGE_FOLDER_PATH.exists()
        pkg = load_mapping_package(
            TEST_DATA_EXAMPLE_SF_MAPPING_PACKAGE_FOLDER_PATH,
            include_test_data=False,
            validate_package=False,
        )
        assert isinstance(pkg, MappingPackageV3Lightweight)
        assert pkg.metadata.id == "package_F22"
        assert pkg.technical_mapping_suite is not None

    def test_v2_to_v3(self):
        from tests import TEST_DATA_EXAMPLE_EFORMS_MAPPING_PACKAGE_FOLDER_PATH
        assert TEST_DATA_EXAMPLE_EFORMS_MAPPING_PACKAGE_FOLDER_PATH.exists()
        pkg = load_mapping_package(
            TEST_DATA_EXAMPLE_EFORMS_MAPPING_PACKAGE_FOLDER_PATH,
            include_test_data=True,
            validate_package=False,
        )
        assert isinstance(pkg, MappingPackageV3)
        assert pkg.metadata.project_identifier == "eforms"
        assert pkg.technical_mapping_suite is not None
        assert len(pkg.technical_mapping_suite.files) >= 1

    def test_v2_to_v3l(self):
        from tests import TEST_DATA_EXAMPLE_EFORMS_MAPPING_PACKAGE_FOLDER_PATH
        assert TEST_DATA_EXAMPLE_EFORMS_MAPPING_PACKAGE_FOLDER_PATH.exists()
        pkg = load_mapping_package(
            TEST_DATA_EXAMPLE_EFORMS_MAPPING_PACKAGE_FOLDER_PATH,
            include_test_data=False,
            validate_package=False,
        )
        assert isinstance(pkg, MappingPackageV3Lightweight)
        assert pkg.metadata.project_identifier == "eforms"
        assert pkg.technical_mapping_suite is not None

    def test_v3_to_v3(self):
        from tests import TEST_DATA_EXAMPLE_V3_MAPPING_PACKAGE_FOLDER_PATH
        assert TEST_DATA_EXAMPLE_V3_MAPPING_PACKAGE_FOLDER_PATH.exists()
        pkg = load_mapping_package(
            TEST_DATA_EXAMPLE_V3_MAPPING_PACKAGE_FOLDER_PATH,
            include_test_data=True,
            validate_package=False,
        )
        assert isinstance(pkg, MappingPackageV3)
        assert pkg.metadata.id == "https://meaningfy.ws/mapping/package_eforms_sdk1.13_epo4.0"
        assert pkg.technical_mapping_suite is not None
        assert len(pkg.technical_mapping_suite.files) >= 1

    def test_v3_to_v3l(self):
        from tests import TEST_DATA_EXAMPLE_V3_MAPPING_PACKAGE_FOLDER_PATH
        assert TEST_DATA_EXAMPLE_V3_MAPPING_PACKAGE_FOLDER_PATH.exists()
        pkg = load_mapping_package(
            TEST_DATA_EXAMPLE_V3_MAPPING_PACKAGE_FOLDER_PATH,
            include_test_data=False,
            validate_package=False,
        )
        assert isinstance(pkg, MappingPackageV3Lightweight)
        assert pkg.metadata.id == "https://meaningfy.ws/mapping/package_eforms_sdk1.13_epo4.0"
        assert pkg.technical_mapping_suite is not None

    def test_v3l_to_v3l(self):
        from tests import TEST_DATA_EXAMPLE_V3L_MAPPING_PACKAGE_FOLDER_PATH
        assert TEST_DATA_EXAMPLE_V3L_MAPPING_PACKAGE_FOLDER_PATH.exists()
        pkg = load_mapping_package(
            TEST_DATA_EXAMPLE_V3L_MAPPING_PACKAGE_FOLDER_PATH,
            include_test_data=False,
            validate_package=False,
        )
        assert isinstance(pkg, MappingPackageV3Lightweight)
        assert pkg.metadata.id == "https://meaningfy.ws/mapping/package_eforms_sdk1.13_epo4.0"
        assert pkg.technical_mapping_suite is not None
        assert len(pkg.technical_mapping_suite.files) >= 1

    def test_v3l_to_v3_raises_unsupported(self):
        from tests import TEST_DATA_EXAMPLE_V3L_MAPPING_PACKAGE_FOLDER_PATH
        assert TEST_DATA_EXAMPLE_V3L_MAPPING_PACKAGE_FOLDER_PATH.exists()
        with pytest.raises(UnsupportedConversionError, match="Cannot produce v3.*from a v3L source"):
            load_mapping_package(
                TEST_DATA_EXAMPLE_V3L_MAPPING_PACKAGE_FOLDER_PATH,
                include_test_data=True,
                validate_package=False,
            )
