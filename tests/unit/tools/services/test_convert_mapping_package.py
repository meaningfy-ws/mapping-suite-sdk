"""
Unit tests for the convert_mapping_package orchestration service.

Tests focus on service layer responsibilities:
- Orchestration of load, convert, serialize workflow
- Exception handling and hard fails
- File operations (context.jsonld, metadata cleanup)
"""
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2 import MappingPackageV2
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_lightweight import MappingPackageV3Lightweight
from mapping_suite_sdk.tools.services.convert_mapping_package import (
    ConversionError,
    InvalidPackagePathError,
    UnsupportedVersionError,
    Version,
    convert_mapping_package_from_folder,
    convert_mapping_package_model,
    convert_mapping_packages_from_folder,
    load_mapping_package_from_folder,
    serialise_mapping_package
)


class TestLoadMappingPackageFromFolder:
    """Tests for load_mapping_package_from_folder function."""

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.load_mapping_package_v2_from_folder')
    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.MappingPackageV2Loader')
    def test_load_v2_package_success(self, mock_loader_class, mock_load_service, tmp_path: Path):
        """Test loading V2 package successfully."""
        mock_package = Mock(spec=MappingPackageV2)
        mock_loader = Mock()
        mock_loader_class.return_value = mock_loader
        mock_load_service.return_value = mock_package

        result = load_mapping_package_from_folder(Version.V2, tmp_path)

        assert result is mock_package
        mock_loader_class.assert_called_once()
        mock_load_service.assert_called_once_with(
            mapping_package_folder_path=tmp_path,
            mapping_package_loader=mock_loader
        )

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.load_mapping_package_v3_from_folder')
    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.MappingPackageV3Loader')
    def test_load_v3_package_success(self, mock_loader_class, mock_load_service, tmp_path: Path):
        """Test loading V3 package successfully."""
        mock_package = Mock(spec=MappingPackageV3)
        mock_loader = Mock()
        mock_loader_class.return_value = mock_loader
        mock_load_service.return_value = mock_package

        result = load_mapping_package_from_folder(Version.V3, tmp_path)

        assert result is mock_package
        mock_loader_class.assert_called_once()
        mock_load_service.assert_called_once_with(
            mapping_package_folder_path=tmp_path,
            mapping_package_loader=mock_loader
        )

    def test_load_package_invalid_path_not_exists(self, tmp_path: Path):
        """Test that non-existent path raises InvalidPackagePathError."""
        invalid_path = tmp_path / "nonexistent"

        with pytest.raises(InvalidPackagePathError, match="does not exist"):
            load_mapping_package_from_folder(Version.V2, invalid_path)

    def test_load_package_invalid_path_not_directory(self, tmp_path: Path):
        """Test that file path (not directory) raises InvalidPackagePathError."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")

        with pytest.raises(InvalidPackagePathError, match="not a directory"):
            load_mapping_package_from_folder(Version.V2, file_path)

    def test_load_package_unsupported_version(self, tmp_path: Path):
        """Test that unsupported version raises UnsupportedVersionError."""
        with pytest.raises(UnsupportedVersionError, match="Unsupported source version"):
            load_mapping_package_from_folder("v1", tmp_path)


class TestConvertMappingPackageModel:
    """Tests for convert_mapping_package_model function."""

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.convert_mapping_package_v2_to_v3')
    def test_convert_v2_to_v3_success(self, mock_convert, fixture_mapping_package_v3_model: MappingPackageV3):
        """Test converting V2 to V3 model successfully."""
        mock_v2_package = Mock(spec=MappingPackageV2)
        mock_convert.return_value = fixture_mapping_package_v3_model

        result = convert_mapping_package_model(Version.V2, Version.V3, mock_v2_package)

        assert result is fixture_mapping_package_v3_model
        mock_convert.assert_called_once_with(mock_v2_package)

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.convert_mapping_package_v3_to_v3_lightweight')
    def test_convert_v3_to_v3l_success(self, mock_convert, fixture_mapping_package_v3_model: MappingPackageV3):
        """Test converting V3 to V3L model successfully."""
        mock_v3l_package = Mock(spec=MappingPackageV3Lightweight)
        mock_convert.return_value = mock_v3l_package

        result = convert_mapping_package_model(Version.V3, Version.V3L, fixture_mapping_package_v3_model)

        assert result is mock_v3l_package
        mock_convert.assert_called_once_with(fixture_mapping_package_v3_model)

    def test_convert_unsupported_conversion(self):
        """Test that unsupported conversion raises UnsupportedVersionError."""
        mock_package = Mock()

        with pytest.raises(UnsupportedVersionError, match="Unsupported conversion"):
            convert_mapping_package_model(Version.V1, Version.V3, mock_package)


class TestSerialiseMappingPackage:
    """Tests for serialise_mapping_package function."""

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package._copy_context_jsonld_to_package')
    @patch('mapping_suite_sdk.tools.services.convert_mapping_package._remove_old_metadata_json')
    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.MappingPackageV3Serialiser')
    def test_serialise_v3_package_success(
        self,
        mock_serialiser_class,
        mock_remove_metadata,
        mock_copy_context,
        tmp_path: Path,
        fixture_mapping_package_v3_model: MappingPackageV3
    ):
        """Test serializing V3 package successfully."""
        mock_serialiser = Mock()
        mock_serialiser_class.return_value = mock_serialiser

        serialise_mapping_package(Version.V3, tmp_path, fixture_mapping_package_v3_model)

        mock_serialiser_class.assert_called_once()
        mock_serialiser.serialise.assert_called_once_with(tmp_path, fixture_mapping_package_v3_model)
        mock_copy_context.assert_called_once_with(tmp_path, fixture_mapping_package_v3_model)
        mock_remove_metadata.assert_called_once_with(tmp_path)

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package._remove_conceptual_mapping_file')
    @patch('mapping_suite_sdk.tools.services.convert_mapping_package._copy_context_jsonld_to_package')
    @patch('mapping_suite_sdk.tools.services.convert_mapping_package._remove_old_metadata_json')
    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.MappingPackageV3LightweightSerialiser')
    def test_serialise_v3l_package_success(
        self,
        mock_serialiser_class,
        mock_remove_metadata,
        mock_copy_context,
        mock_remove_conceptual,
        tmp_path: Path,
        fixture_mapping_package_v3_model: MappingPackageV3
    ):
        """Test serializing V3L package successfully."""
        mock_v3l_package = Mock(spec=MappingPackageV3Lightweight)
        mock_serialiser = Mock()
        mock_serialiser_class.return_value = mock_serialiser

        serialise_mapping_package(Version.V3L, tmp_path, mock_v3l_package)

        mock_serialiser_class.assert_called_once()
        mock_serialiser.serialise.assert_called_once_with(tmp_path, mock_v3l_package)
        mock_copy_context.assert_called_once_with(tmp_path, mock_v3l_package)
        mock_remove_metadata.assert_called_once_with(tmp_path)
        mock_remove_conceptual.assert_called_once_with(tmp_path)

    def test_serialise_unsupported_version(self, tmp_path: Path):
        """Test that unsupported version raises UnsupportedVersionError."""
        mock_package = Mock()

        with pytest.raises(UnsupportedVersionError, match="Unsupported target version"):
            serialise_mapping_package("v1", tmp_path, mock_package)


class TestConvertMappingPackageFromFolder:
    """Tests for convert_mapping_package_from_folder orchestration function."""

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.serialise_mapping_package')
    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.convert_mapping_package_model')
    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.load_mapping_package_from_folder')
    def test_convert_package_full_workflow_success(
        self,
        mock_load,
        mock_convert,
        mock_serialise,
        tmp_path: Path
    ):
        """Test complete conversion workflow: load -> convert -> serialize."""
        mock_source = Mock()
        mock_converted = Mock()
        mock_load.return_value = mock_source
        mock_convert.return_value = mock_converted

        convert_mapping_package_from_folder(Version.V2, Version.V3, tmp_path)

        mock_load.assert_called_once_with(Version.V2, tmp_path)
        mock_convert.assert_called_once_with(Version.V2, Version.V3, mock_source)
        mock_serialise.assert_called_once_with(Version.V3, tmp_path, mock_converted)

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.load_mapping_package_from_folder')
    def test_convert_package_hard_fail_on_load_error(self, mock_load, tmp_path: Path):
        """Test that load errors propagate (hard fail)."""
        mock_load.side_effect = InvalidPackagePathError("Load failed")

        with pytest.raises(InvalidPackagePathError, match="Load failed"):
            convert_mapping_package_from_folder(Version.V2, Version.V3, tmp_path)

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.serialise_mapping_package')
    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.convert_mapping_package_model')
    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.load_mapping_package_from_folder')
    def test_convert_package_hard_fail_on_convert_error(
        self,
        mock_load,
        mock_convert,
        mock_serialise,
        tmp_path: Path
    ):
        """Test that convert errors propagate (hard fail)."""
        mock_load.return_value = Mock()
        mock_convert.side_effect = UnsupportedVersionError("Convert failed")

        with pytest.raises(UnsupportedVersionError, match="Convert failed"):
            convert_mapping_package_from_folder(Version.V2, Version.V3, tmp_path)

        mock_serialise.assert_not_called()

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.serialise_mapping_package')
    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.convert_mapping_package_model')
    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.load_mapping_package_from_folder')
    def test_convert_package_hard_fail_on_serialise_error(
        self,
        mock_load,
        mock_convert,
        mock_serialise,
        tmp_path: Path
    ):
        """Test that serialize errors propagate (hard fail)."""
        mock_load.return_value = Mock()
        mock_convert.return_value = Mock()
        mock_serialise.side_effect = FileNotFoundError("context.jsonld not found")

        with pytest.raises(FileNotFoundError, match="context.jsonld not found"):
            convert_mapping_package_from_folder(Version.V2, Version.V3, tmp_path)


class TestConvertMappingPackagesFromFolder:
    """Tests for convert_mapping_packages_from_folder batch conversion function."""

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.convert_mapping_package_from_folder')
    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.is_mapping_package_already_converted')
    def test_convert_multiple_packages_success(
        self,
        mock_is_converted,
        mock_convert,
        tmp_path: Path
    ):
        """Test converting multiple packages successfully."""
        # Create test directories
        pkg1 = tmp_path / "package1"
        pkg2 = tmp_path / "package2"
        pkg3 = tmp_path / "package3"
        pkg1.mkdir()
        pkg2.mkdir()
        pkg3.mkdir()

        # Setup mocks: pkg1 and pkg3 need conversion, pkg2 already converted
        mock_is_converted.side_effect = lambda path, version: path == pkg2

        result = convert_mapping_packages_from_folder(Version.V2, Version.V3, tmp_path)

        assert result['converted'] == 2
        assert result['skipped'] == 1
        assert result['total'] == 3
        assert mock_convert.call_count == 2
        # Verify convert was called for pkg1 and pkg3, not pkg2
        converted_paths = [call[0][2] for call in mock_convert.call_args_list]
        assert pkg1 in converted_paths
        assert pkg3 in converted_paths
        assert pkg2 not in converted_paths

    def test_convert_packages_invalid_path_not_exists(self, tmp_path: Path):
        """Test that non-existent folder path raises InvalidPackagePathError."""
        invalid_path = tmp_path / "nonexistent"

        with pytest.raises(InvalidPackagePathError, match="does not exist"):
            convert_mapping_packages_from_folder(Version.V2, Version.V3, invalid_path)

    def test_convert_packages_invalid_path_not_directory(self, tmp_path: Path):
        """Test that file path (not directory) raises InvalidPackagePathError."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")

        with pytest.raises(InvalidPackagePathError, match="not a directory"):
            convert_mapping_packages_from_folder(Version.V2, Version.V3, file_path)

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.convert_mapping_package_from_folder')
    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.is_mapping_package_already_converted')
    def test_convert_packages_hard_fail_on_error(
        self,
        mock_is_converted,
        mock_convert,
        tmp_path: Path
    ):
        """Test that conversion errors propagate (hard fail) - stops batch processing."""
        pkg1 = tmp_path / "package1"
        pkg1.mkdir()

        mock_is_converted.return_value = False
        mock_convert.side_effect = ConversionError("Conversion failed")

        # Hard fail: exception should propagate, not be caught
        with pytest.raises(ConversionError, match="Conversion failed"):
            convert_mapping_packages_from_folder(Version.V2, Version.V3, tmp_path)

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.convert_mapping_package_from_folder')
    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.is_mapping_package_already_converted')
    def test_convert_packages_empty_folder(self, mock_is_converted, mock_convert, tmp_path: Path):
        """Test converting from empty folder returns zero counts."""
        result = convert_mapping_packages_from_folder(Version.V2, Version.V3, tmp_path)

        assert result['converted'] == 0
        assert result['skipped'] == 0
        assert result['total'] == 0
        mock_convert.assert_not_called()

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.convert_mapping_package_from_folder')
    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.is_mapping_package_already_converted')
    def test_convert_packages_all_already_converted(
        self,
        mock_is_converted,
        mock_convert,
        tmp_path: Path
    ):
        """Test that all packages already converted results in all skipped."""
        pkg1 = tmp_path / "package1"
        pkg2 = tmp_path / "package2"
        pkg1.mkdir()
        pkg2.mkdir()

        mock_is_converted.return_value = True

        result = convert_mapping_packages_from_folder(Version.V2, Version.V3, tmp_path)

        assert result['converted'] == 0
        assert result['skipped'] == 2
        assert result['total'] == 2
        mock_convert.assert_not_called()

