"""
Unit tests for the load_mapping_package service.

Tests focus on service-layer orchestration:
- Path and version handling
- Version detection and routing
- Loader construction with include_test_data / include_output flags
- Optional validation (before and after conversion)
- Target version from include_test_data
- Optional MongoDB persistence
"""

from pathlib import Path
from unittest.mock import Mock, call, patch

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
    _load_source_package,
    load_mapping_package,
)

# Patch targets for version-specific service functions (lazy-imported inside _load_source_package)
_V1_LOAD = "mapping_suite_sdk.mapping_package_v1.services.load_mapping_package_v1.load_mapping_package_v1_from_folder"
_V2_LOAD = "mapping_suite_sdk.mapping_package_v2.services.load_mapping_package_v2.load_mapping_package_v2_from_folder"
_V3_LOAD = "mapping_suite_sdk.mapping_package_v3.services.load_mapping_package_v3.load_mapping_package_v3_from_folder"
_V3L_LOAD = "mapping_suite_sdk.mapping_package_v3.services.load_mapping_package_v3_lightweight.load_mapping_package_v3_lightweight_from_folder"

# Patch targets for loader constructors
_V1_LOADER = "mapping_suite_sdk.mapping_package_v1.adapters.mp_v1_loader.MappingPackageV1Loader"
_V2_LOADER = "mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_loader.MappingPackageV2Loader"
_V3_LOADER = "mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_package_loader.MappingPackageV3Loader"
_V3L_LOADER = "mapping_suite_sdk.mapping_package_v3.adapters.mp_v3L_package_loader.MappingPackageV3LightweightLoader"


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

    @patch(_V3_LOAD)
    def test_explicit_version_skips_detection(self, mock_load, tmp_path: Path):
        mock_load.return_value = Mock(spec=MappingPackageV3)
        with patch("mapping_suite_sdk.tools.services.load_mapping_package.detect_mapping_package_version") as mock_detect:
            load_mapping_package(tmp_path, version="v3", include_test_data=True, validate_package=False)
            mock_detect.assert_not_called()
        mock_load.assert_called_once()

    @patch(_V2_LOAD)
    @patch("mapping_suite_sdk.tools.services.load_mapping_package.detect_mapping_package_version")
    def test_no_version_triggers_detection(self, mock_detect, mock_load, tmp_path: Path):
        mock_detect.return_value = "v2"
        mock_load.return_value = Mock(spec=MappingPackageV3)
        with patch("mapping_suite_sdk.tools.services.load_mapping_package.convert_mapping_package_model") as mock_convert:
            mock_convert.return_value = Mock(spec=MappingPackageV3)
            load_mapping_package(tmp_path, include_test_data=True, validate_package=False)
        mock_detect.assert_called_once_with(tmp_path)
        mock_load.assert_called_once()

    @patch("mapping_suite_sdk.tools.services.load_mapping_package.detect_mapping_package_version")
    def test_detection_failure_raises(self, mock_detect, tmp_path: Path):
        mock_detect.return_value = None
        with pytest.raises(VersionDetectionError, match="Could not detect"):
            load_mapping_package(tmp_path, validate_package=False)

    def test_unsupported_version_string_raises(self, tmp_path: Path):
        with pytest.raises(UnsupportedVersionError, match="Unsupported version"):
            load_mapping_package(tmp_path, version="v99", validate_package=False)

    def test_load_source_package_unsupported_source_version_raises(self, tmp_path: Path):
        with pytest.raises(UnsupportedVersionError, match="Unsupported source version"):
            _load_source_package(
                "v99",
                tmp_path,
                include_test_data=False,
                include_output=False,
            )

    @patch(_V3L_LOAD)
    def test_version_normalized_case_insensitive_v3l(self, mock_v3l_load, tmp_path: Path):
        mock_v3l_load.return_value = Mock(spec=MappingPackageV3Lightweight)
        result = load_mapping_package(tmp_path, version="  v3L  ", include_test_data=False, validate_package=False)
        mock_v3l_load.assert_called_once()
        assert mock_v3l_load.call_args[1]["mapping_package_folder_path"] == tmp_path
        assert result is mock_v3l_load.return_value


class TestLoadMappingPackageIncludeTestDataAndConversion:
    """Target version (v3 vs v3L) and conversion routing."""

    @patch(_V2_LOAD)
    @patch("mapping_suite_sdk.tools.services.load_mapping_package.convert_mapping_package_model")
    def test_include_test_data_true_targets_v3(self, mock_convert, mock_load, tmp_path: Path):
        source = Mock(spec=MappingPackageV3)
        converted = Mock(spec=MappingPackageV3)
        mock_load.return_value = source
        mock_convert.return_value = converted
        result = load_mapping_package(tmp_path, version="v2", include_test_data=True, validate_package=False)
        mock_convert.assert_called_once_with(Version.V2, Version.V3, source)
        assert result is converted

    @patch(_V3_LOAD)
    @patch("mapping_suite_sdk.tools.services.load_mapping_package.convert_mapping_package_model")
    def test_include_test_data_false_targets_v3l(self, mock_convert, mock_load, tmp_path: Path):
        source = Mock(spec=MappingPackageV3)
        converted = Mock(spec=MappingPackageV3Lightweight)
        mock_load.return_value = source
        mock_convert.return_value = converted
        result = load_mapping_package(tmp_path, version="v3", include_test_data=False, validate_package=False)
        mock_convert.assert_called_once_with(Version.V3, Version.V3L, source)
        assert result is converted

    @patch(_V3L_LOAD)
    def test_v3l_source_with_include_test_data_true_raises(self, mock_v3l_load, tmp_path: Path):
        mock_v3l_load.return_value = Mock(spec=MappingPackageV3Lightweight)
        with pytest.raises(
            UnsupportedConversionError,
            match="Cannot produce v3.*from a v3L source",
        ):
            load_mapping_package(tmp_path, version="v3L", include_test_data=True, validate_package=False)

    @patch(_V3L_LOAD)
    def test_v3l_source_with_include_test_data_false_returns_without_conversion(self, mock_v3l_load, tmp_path: Path):
        pkg = Mock(spec=MappingPackageV3Lightweight)
        mock_v3l_load.return_value = pkg
        with patch("mapping_suite_sdk.tools.services.load_mapping_package.convert_mapping_package_model") as mock_convert:
            result = load_mapping_package(tmp_path, version="v3L", include_test_data=False, validate_package=False)
            mock_convert.assert_not_called()
        assert result is pkg


class TestLoadMappingPackageLoaderFlags:
    """Loader is constructed with include_test_data and include_output flags."""

    @patch(_V1_LOAD)
    @patch(_V1_LOADER)
    def test_include_output_false_passed_to_v1_loader(self, mock_loader_cls, mock_load, tmp_path: Path):
        mock_instance = Mock()
        mock_loader_cls.return_value = mock_instance
        mock_load.return_value = Mock(spec=MappingPackageV3)
        with patch("mapping_suite_sdk.tools.services.load_mapping_package.convert_mapping_package_model") as mock_convert:
            mock_convert.return_value = Mock(spec=MappingPackageV3)
            load_mapping_package(tmp_path, version="v1", include_test_data=True, include_output=False, validate_package=False)
        mock_loader_cls.assert_called_once_with(include_test_data=True, include_output=False)

    @patch(_V2_LOAD)
    @patch(_V2_LOADER)
    def test_include_output_false_passed_to_v2_loader(self, mock_loader_cls, mock_load, tmp_path: Path):
        mock_instance = Mock()
        mock_loader_cls.return_value = mock_instance
        mock_load.return_value = Mock(spec=MappingPackageV3)
        with patch("mapping_suite_sdk.tools.services.load_mapping_package.convert_mapping_package_model") as mock_convert:
            mock_convert.return_value = Mock(spec=MappingPackageV3)
            load_mapping_package(tmp_path, version="v2", include_test_data=True, include_output=False, validate_package=False)
        mock_loader_cls.assert_called_once_with(include_test_data=True, include_output=False)

    @patch(_V3_LOAD)
    @patch(_V3_LOADER)
    def test_include_output_false_passed_to_v3_loader(self, mock_loader_cls, mock_load, tmp_path: Path):
        mock_instance = Mock()
        mock_loader_cls.return_value = mock_instance
        mock_load.return_value = Mock(spec=MappingPackageV3)
        load_mapping_package(tmp_path, version="v3", include_test_data=True, include_output=False, validate_package=False)
        mock_loader_cls.assert_called_once_with(include_test_data=True, include_output=False)

    @patch(_V3L_LOAD)
    @patch(_V3L_LOADER)
    def test_include_output_false_passed_to_v3l_loader(self, mock_loader_cls, mock_load, tmp_path: Path):
        mock_instance = Mock()
        mock_loader_cls.return_value = mock_instance
        mock_load.return_value = Mock(spec=MappingPackageV3Lightweight)
        load_mapping_package(tmp_path, version="v3L", include_test_data=False, include_output=False, validate_package=False)
        mock_loader_cls.assert_called_once_with(include_test_data=False, include_output=False)

    @patch(_V3_LOAD)
    @patch(_V3_LOADER)
    def test_include_output_defaults_to_false(self, mock_loader_cls, mock_load, tmp_path: Path):
        mock_instance = Mock()
        mock_loader_cls.return_value = mock_instance
        mock_load.return_value = Mock(spec=MappingPackageV3)
        load_mapping_package(tmp_path, version="v3", include_test_data=True, validate_package=False)
        mock_loader_cls.assert_called_once_with(include_test_data=True, include_output=False)

    @patch(_V3_LOAD)
    @patch(_V3_LOADER)
    def test_loader_instance_passed_to_service_function(self, mock_loader_cls, mock_load, tmp_path: Path):
        mock_instance = Mock()
        mock_loader_cls.return_value = mock_instance
        mock_load.return_value = Mock(spec=MappingPackageV3)
        load_mapping_package(tmp_path, version="v3", include_test_data=True, validate_package=False)
        assert mock_load.call_args[1]["mapping_package_loader"] is mock_instance


class TestLoadMappingPackageValidation:
    """Optional validation before and after conversion."""

    @patch("mapping_suite_sdk.tools.services.validate_mapping_package.validate_mapping_package")
    @patch(_V2_LOAD)
    @patch("mapping_suite_sdk.tools.services.load_mapping_package.convert_mapping_package_model")
    def test_validate_package_true_validates_before_and_after(self, mock_convert, mock_load, mock_validate, tmp_path: Path):
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
        assert mock_validate.call_args_list[0] == call(tmp_path, include_test_data=True, include_output=False)
        assert mock_validate.call_args_list[1] == call(converted, include_test_data=True, include_output=False)

    @patch("mapping_suite_sdk.tools.services.validate_mapping_package.validate_mapping_package")
    @patch(_V3_LOAD)
    def test_validate_package_false_skips_validation(self, mock_load, mock_validate, tmp_path: Path):
        mock_load.return_value = Mock(spec=MappingPackageV3)
        load_mapping_package(tmp_path, version="v3", include_test_data=True, validate_package=False)
        mock_validate.assert_not_called()


class TestLoadMappingPackageNeverPersists:
    """mongodb-persistence: loading never persists (DEC-1)."""

    def test_old_parameter_rejected(self, tmp_path: Path):
        with pytest.raises(TypeError, match="persist_to_mongodb"):
            load_mapping_package(tmp_path, persist_to_mongodb=True)


class TestLoadMappingPackageV3NoConversion:
    """When source is already target version, no conversion."""

    @patch(_V3_LOAD)
    @patch("mapping_suite_sdk.tools.services.load_mapping_package.convert_mapping_package_model")
    def test_v3_source_target_v3_returns_same_instance(self, mock_convert, mock_load, tmp_path: Path):
        pkg = Mock(spec=MappingPackageV3)
        mock_load.return_value = pkg
        result = load_mapping_package(tmp_path, version="v3", include_test_data=True, validate_package=False)
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
