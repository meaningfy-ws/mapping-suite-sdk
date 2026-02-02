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
# Import private helpers for testing
from mapping_suite_sdk.tools.services.convert_mapping_package import (
    _copy_context_jsonld_to_package,
    _get_context_jsonld_path,
    _remove_conceptual_mapping_file,
    _remove_folder,
    _remove_old_metadata_json
)


class TestLoadMappingPackageFromFolder:
    """Tests for load_mapping_package_from_folder function."""

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.load_mapping_package_v1_from_folder')
    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.MappingPackageV1Loader')
    def test_load_v1_package_success(self, mock_loader_class, mock_load_service, tmp_path: Path):
        """Test loading V1 package successfully."""
        from mapping_suite_sdk.mapping_package_v1.models.mapping_package_v1 import MappingPackageV1

        mock_package = Mock(spec=MappingPackageV1)
        mock_loader = Mock()
        mock_loader_class.return_value = mock_loader
        mock_load_service.return_value = mock_package

        result = load_mapping_package_from_folder(Version.V1, tmp_path)

        assert result is mock_package
        mock_loader_class.assert_called_once()
        mock_load_service.assert_called_once_with(
            mapping_package_folder_path=tmp_path,
            mapping_package_loader=mock_loader
        )

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
            load_mapping_package_from_folder("v0", tmp_path)


class TestConvertMappingPackageModel:
    """Tests for convert_mapping_package_model function."""

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.convert_mapping_package_v1_to_v3')
    def test_convert_v1_to_v3_success(self, mock_convert, fixture_mapping_package_v3_model: MappingPackageV3):
        """Test converting V1 to V3 model successfully."""
        from mapping_suite_sdk.mapping_package_v1.models.mapping_package_v1 import MappingPackageV1

        mock_v1_package = Mock(spec=MappingPackageV1)
        mock_convert.return_value = fixture_mapping_package_v3_model

        result = convert_mapping_package_model(Version.V1, Version.V3, mock_v1_package)

        assert result is fixture_mapping_package_v3_model
        mock_convert.assert_called_once_with(mock_v1_package)

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

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.convert_mapping_package_v2_to_v3_lightweight')
    def test_convert_v2_to_v3l_success(self, mock_convert):
        """Test converting V2 to V3L model successfully."""
        mock_v2_package = Mock(spec=MappingPackageV2)
        mock_v3l_package = Mock(spec=MappingPackageV3Lightweight)
        mock_convert.return_value = mock_v3l_package

        result = convert_mapping_package_model(Version.V2, Version.V3L, mock_v2_package)

        assert result is mock_v3l_package
        mock_convert.assert_called_once_with(mock_v2_package)

    def test_convert_unsupported_conversion(self):
        """Test that unsupported conversion raises UnsupportedVersionError."""
        mock_package = Mock()

        with pytest.raises(UnsupportedVersionError, match="Unsupported conversion"):
            convert_mapping_package_model(Version.V1, Version.V3L, mock_package)


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

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package._get_context_jsonld_path')
    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.MappingPackageV3Serialiser')
    def test_serialise_v3_package_copies_context_jsonld(
        self,
        mock_serialiser_class,
        mock_get_context,
        tmp_path: Path,
        fixture_mapping_package_v3_model: MappingPackageV3
    ):
        """Test that serializing V3 package copies context.jsonld."""
        # Create mock context file
        schema_context = tmp_path / "schema" / "context.jsonld"
        schema_context.parent.mkdir(parents=True)
        schema_context.write_text('{"@context": {}}')
        mock_get_context.return_value = schema_context
        
        mock_serialiser = Mock()
        mock_serialiser_class.return_value = mock_serialiser
        
        # Create package structure
        metadata_dir = tmp_path / fixture_mapping_package_v3_model.metadata.path.parent
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        serialise_mapping_package(Version.V3, tmp_path, fixture_mapping_package_v3_model)
        
        # Verify context.jsonld was copied
        package_context = metadata_dir / "context.jsonld"
        assert package_context.exists()
        assert package_context.read_text() == '{"@context": {}}'
        mock_get_context.assert_called_once()

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package._resolve_package_root')
    @patch('mapping_suite_sdk.tools.services.convert_mapping_package._get_context_jsonld_path')
    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.MappingPackageV3Serialiser')
    def test_serialise_v3_package_removes_old_metadata_json(
        self,
        mock_serialiser_class,
        mock_get_context,
        mock_resolve,
        tmp_path: Path,
        fixture_mapping_package_v3_model: MappingPackageV3
    ):
        """Test that serializing V3 package removes old metadata.json."""
        # Create mock context file
        schema_context = tmp_path / "schema" / "context.jsonld"
        schema_context.parent.mkdir(parents=True)
        schema_context.write_text('{"@context": {}}')
        mock_get_context.return_value = schema_context
        
        mock_serialiser = Mock()
        mock_serialiser_class.return_value = mock_serialiser
        mock_resolve.return_value = tmp_path
        
        # Create old metadata.json
        old_metadata = tmp_path / "metadata.json"
        old_metadata.write_text('{"old": "data"}')
        assert old_metadata.exists()
        
        metadata_dir = tmp_path / fixture_mapping_package_v3_model.metadata.path.parent
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        serialise_mapping_package(Version.V3, tmp_path, fixture_mapping_package_v3_model)
        
        # Verify old metadata.json was removed
        assert not old_metadata.exists()
        mock_resolve.assert_called_once_with(tmp_path)

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package._remove_folder')
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
        mock_remove_folder,
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
        # Verify _remove_folder is called 3 times for test_data, output, and validation
        assert mock_remove_folder.call_count == 3

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package._resolve_package_root')
    @patch('mapping_suite_sdk.tools.services.convert_mapping_package._get_context_jsonld_path')
    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.MappingPackageV3LightweightSerialiser')
    def test_serialise_v3l_package_removes_conceptual_mapping_file(
        self,
        mock_serialiser_class,
        mock_get_context,
        mock_resolve,
        tmp_path: Path,
        fixture_mapping_package_v3_model: MappingPackageV3
    ):
        """Test that serializing V3L package removes conceptual_mappings.xlsx."""
        from mapping_suite_sdk import mssdk_config
        from mapping_suite_sdk.tools.services.convert_mapping_package_v3_to_v3_lightweight import convert_mapping_package_v3_to_v3_lightweight
        
        # Create mock context file
        schema_context = tmp_path / "schema" / "context.jsonld"
        schema_context.parent.mkdir(parents=True)
        schema_context.write_text('{"@context": {}}')
        mock_get_context.return_value = schema_context
        
        mock_serialiser = Mock()
        mock_serialiser_class.return_value = mock_serialiser
        mock_resolve.return_value = tmp_path
        
        # Create conceptual_mappings.xlsx
        conceptual_path = tmp_path / mssdk_config.MPV3_CONCEPTUAL_MAPPING_FILE_ASSET_PATH
        conceptual_path.parent.mkdir(parents=True, exist_ok=True)
        conceptual_path.write_bytes(b"fake xlsx")
        assert conceptual_path.exists()
        
        # Convert to lightweight
        lightweight_package = convert_mapping_package_v3_to_v3_lightweight(fixture_mapping_package_v3_model)
        metadata_dir = tmp_path / lightweight_package.metadata.path.parent
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        serialise_mapping_package(Version.V3L, tmp_path, lightweight_package)
        
        # Verify conceptual_mappings.xlsx was removed
        assert not conceptual_path.exists()
        mock_resolve.assert_called_with(tmp_path)

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package._resolve_package_root')
    @patch('mapping_suite_sdk.tools.services.convert_mapping_package._get_context_jsonld_path')
    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.MappingPackageV3LightweightSerialiser')
    def test_serialise_v3l_package_removes_folders(
        self,
        mock_serialiser_class,
        mock_get_context,
        mock_resolve,
        tmp_path: Path,
        fixture_mapping_package_v3_model: MappingPackageV3
    ):
        """Test that serializing V3L package removes test_data, output, and validation folders."""
        from mapping_suite_sdk import mssdk_config
        from mapping_suite_sdk.tools.services.convert_mapping_package_v3_to_v3_lightweight import convert_mapping_package_v3_to_v3_lightweight
        
        # Create mock context file
        schema_context = tmp_path / "schema" / "context.jsonld"
        schema_context.parent.mkdir(parents=True)
        schema_context.write_text('{"@context": {}}')
        mock_get_context.return_value = schema_context
        
        mock_serialiser = Mock()
        mock_serialiser_class.return_value = mock_serialiser
        mock_resolve.return_value = tmp_path
        
        # Create test_data, output, and validation folders with some content
        test_data_path = tmp_path / mssdk_config.MPV3_TEST_DATA_COLLECTION_ASSET_PATH
        test_data_path.mkdir(parents=True, exist_ok=True)
        (test_data_path / "test_file.xml").write_text("test data")
        
        output_path = tmp_path / mssdk_config.MPV3_TEST_RESULT_COLLECTION_ASSET_PATH
        output_path.mkdir(parents=True, exist_ok=True)
        (output_path / "result.ttl").write_text("result data")
        
        validation_path = tmp_path / "validation"
        validation_path.mkdir(parents=True, exist_ok=True)
        (validation_path / "sparql").mkdir()
        (validation_path / "shacl").mkdir()
        (validation_path / "sparql" / "query.rq").write_text("SELECT *")
        
        assert test_data_path.exists()
        assert output_path.exists()
        assert validation_path.exists()
        
        # Convert to lightweight
        lightweight_package = convert_mapping_package_v3_to_v3_lightweight(fixture_mapping_package_v3_model)
        metadata_dir = tmp_path / lightweight_package.metadata.path.parent
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        serialise_mapping_package(Version.V3L, tmp_path, lightweight_package)
        
        # Verify folders were removed
        assert not test_data_path.exists()
        assert not output_path.exists()
        assert not validation_path.exists()
        mock_resolve.assert_called_with(tmp_path)

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


class TestHelperFunctions:
    """Tests for private helper functions in convert_mapping_package service."""

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package._get_context_jsonld_path')
    def test_get_context_jsonld_path_called_when_copying(
        self,
        mock_get_context,
        tmp_path: Path,
        fixture_mapping_package_v3_model: MappingPackageV3
    ):
        """Test _get_context_jsonld_path is called when copying context.jsonld."""
        # Create mock context file
        schema_context = tmp_path / "schema" / "context.jsonld"
        schema_context.parent.mkdir(parents=True)
        schema_context.write_text('{"@context": {}}')
        mock_get_context.return_value = schema_context
        
        package_path = tmp_path / "package"
        package_path.mkdir(exist_ok=True)
        metadata_dir = package_path / fixture_mapping_package_v3_model.metadata.path.parent
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        _copy_context_jsonld_to_package(package_path, fixture_mapping_package_v3_model)
        
        # Verify _get_context_jsonld_path was called
        mock_get_context.assert_called_once()
        # Verify file was copied
        assert (metadata_dir / "context.jsonld").exists()

    def test_get_context_jsonld_path_file_not_found_error(self, tmp_path: Path):
        """Test that _get_context_jsonld_path raises FileNotFoundError when context.jsonld missing."""
        # Create a fake package structure where context.jsonld doesn't exist
        fake_package_path = tmp_path / "mapping_suite_sdk"
        fake_package_path.mkdir()
        
        # Mock importlib.resources.files to return something that Path() can convert
        mock_package_ref = Mock()
        # Use a context manager to patch Path only for the specific call
        with patch('mapping_suite_sdk.tools.services.convert_mapping_package.importlib.resources.files', return_value=mock_package_ref):
            # Patch Path constructor to return our fake path
            original_path = Path
            def mock_path_constructor(path_arg):
                if path_arg == mock_package_ref:
                    return fake_package_path
                return original_path(path_arg)
            
            with patch('mapping_suite_sdk.tools.services.convert_mapping_package.Path', side_effect=mock_path_constructor):
                with pytest.raises(FileNotFoundError, match="context.jsonld not found"):
                    _get_context_jsonld_path()

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.importlib.resources.files')
    def test_get_context_jsonld_path_success_when_file_exists(self, mock_files, tmp_path: Path):
        """Test that _get_context_jsonld_path returns path when context.jsonld exists."""
        # Create the expected file structure
        package_path = tmp_path / "mapping_suite_sdk"
        package_path.mkdir()
        project_root = tmp_path
        context_path = project_root / "resources" / "schema" / "mapping_package_v3" / "models" / "context.jsonld"
        context_path.parent.mkdir(parents=True, exist_ok=True)
        context_path.write_text('{"@context": {}}')
        
        # Mock importlib.resources.files
        mock_package_ref = Mock()
        mock_files.return_value = mock_package_ref
        
        # Mock Path() to return our test package path when called with mock_package_ref
        original_path = Path
        def mock_path_constructor(path_arg):
            if path_arg == mock_package_ref:
                return package_path
            return original_path(path_arg)
        
        with patch('mapping_suite_sdk.tools.services.convert_mapping_package.Path', side_effect=mock_path_constructor):
            result = _get_context_jsonld_path()
            
            assert result == context_path
            assert result.exists()
            mock_files.assert_called_once_with("mapping_suite_sdk")

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package._get_context_jsonld_path')
    @patch('mapping_suite_sdk.tools.services.convert_mapping_package.shutil.copy2')
    def test_copy_context_jsonld_to_package_success(
        self,
        mock_copy,
        mock_get_context,
        tmp_path: Path,
        fixture_mapping_package_v3_model: MappingPackageV3
    ):
        """Test that _copy_context_jsonld_to_package copies context.jsonld correctly."""
        schema_context = tmp_path / "schema" / "context.jsonld"
        schema_context.parent.mkdir(parents=True)
        schema_context.write_text('{"@context": {}}')
        mock_get_context.return_value = schema_context
        
        package_path = tmp_path / "package"
        package_path.mkdir(exist_ok=True)
        metadata_dir = package_path / fixture_mapping_package_v3_model.metadata.path.parent
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        _copy_context_jsonld_to_package(package_path, fixture_mapping_package_v3_model)
        
        mock_get_context.assert_called_once()
        mock_copy.assert_called_once()
        # Verify copy was called with correct paths
        call_args = mock_copy.call_args[0]
        assert call_args[0] == schema_context
        assert call_args[1] == metadata_dir / "context.jsonld"

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package._get_context_jsonld_path')
    def test_copy_context_jsonld_to_package_hard_fail_on_missing_file(
        self,
        mock_get_context,
        tmp_path: Path,
        fixture_mapping_package_v3_model: MappingPackageV3
    ):
        """Test that _copy_context_jsonld_to_package raises FileNotFoundError when context.jsonld missing."""
        mock_get_context.side_effect = FileNotFoundError("context.jsonld not found")
        
        with pytest.raises(FileNotFoundError, match="context.jsonld not found"):
            _copy_context_jsonld_to_package(tmp_path, fixture_mapping_package_v3_model)

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package._resolve_package_root')
    def test_remove_old_metadata_json_when_exists(self, mock_resolve, tmp_path: Path):
        """Test that _remove_old_metadata_json removes metadata.json when it exists."""
        package_path = tmp_path / "package"
        package_path.mkdir()
        mock_resolve.return_value = package_path
        
        old_metadata = package_path / "metadata.json"
        old_metadata.write_text('{"test": "data"}')
        assert old_metadata.exists()
        
        _remove_old_metadata_json(package_path)
        
        assert not old_metadata.exists()
        mock_resolve.assert_called_once_with(package_path)

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package._resolve_package_root')
    def test_remove_old_metadata_json_when_not_exists(self, mock_resolve, tmp_path: Path):
        """Test that _remove_old_metadata_json handles missing metadata.json gracefully."""
        package_path = tmp_path / "package"
        package_path.mkdir()
        mock_resolve.return_value = package_path
        
        # metadata.json doesn't exist - should not raise error
        _remove_old_metadata_json(package_path)
        
        mock_resolve.assert_called_once_with(package_path)

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package._resolve_package_root')
    def test_remove_old_metadata_json_uses_original_path_when_resolve_returns_none(
        self,
        mock_resolve,
        tmp_path: Path
    ):
        """Test that _remove_old_metadata_json uses original path when _resolve_package_root returns None."""
        package_path = tmp_path / "package"
        package_path.mkdir()
        mock_resolve.return_value = None
        
        old_metadata = package_path / "metadata.json"
        old_metadata.write_text('{"test": "data"}')
        
        _remove_old_metadata_json(package_path)
        
        assert not old_metadata.exists()

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package._resolve_package_root')
    def test_remove_conceptual_mapping_file_when_exists(self, mock_resolve, tmp_path: Path):
        """Test that _remove_conceptual_mapping_file removes conceptual_mappings.xlsx when it exists."""
        from mapping_suite_sdk import mssdk_config
        
        package_path = tmp_path / "package"
        package_path.mkdir()
        mock_resolve.return_value = package_path
        
        conceptual_path = package_path / mssdk_config.MPV3_CONCEPTUAL_MAPPING_FILE_ASSET_PATH
        conceptual_path.parent.mkdir(parents=True, exist_ok=True)
        conceptual_path.write_bytes(b"fake xlsx")
        assert conceptual_path.exists()
        
        _remove_conceptual_mapping_file(package_path)
        
        assert not conceptual_path.exists()
        mock_resolve.assert_called_once_with(package_path)

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package._resolve_package_root')
    def test_remove_conceptual_mapping_file_when_not_exists(self, mock_resolve, tmp_path: Path):
        """Test that _remove_conceptual_mapping_file handles missing file gracefully."""
        package_path = tmp_path / "package"
        package_path.mkdir()
        mock_resolve.return_value = package_path
        
        # conceptual_mappings.xlsx doesn't exist - should not raise error
        _remove_conceptual_mapping_file(package_path)
        
        mock_resolve.assert_called_once_with(package_path)

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package._resolve_package_root')
    def test_remove_conceptual_mapping_file_uses_original_path_when_resolve_returns_none(
        self,
        mock_resolve,
        tmp_path: Path
    ):
        """Test that _remove_conceptual_mapping_file uses original path when _resolve_package_root returns None."""
        from mapping_suite_sdk import mssdk_config
        
        package_path = tmp_path / "package"
        package_path.mkdir()
        mock_resolve.return_value = None
        
        conceptual_path = package_path / mssdk_config.MPV3_CONCEPTUAL_MAPPING_FILE_ASSET_PATH
        conceptual_path.parent.mkdir(parents=True, exist_ok=True)
        conceptual_path.write_bytes(b"fake xlsx")
        
        _remove_conceptual_mapping_file(package_path)
        
        assert not conceptual_path.exists()

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package._resolve_package_root')
    def test_remove_folder_when_exists(self, mock_resolve, tmp_path: Path):
        """Test that _remove_folder removes folder when it exists."""
        package_path = tmp_path / "package"
        package_path.mkdir()
        mock_resolve.return_value = package_path
        
        test_folder = package_path / "test_folder"
        test_folder.mkdir()
        (test_folder / "file.txt").write_text("content")
        assert test_folder.exists()
        
        _remove_folder(package_path, "test_folder", "test_folder")
        
        assert not test_folder.exists()
        mock_resolve.assert_called_once_with(package_path)

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package._resolve_package_root')
    def test_remove_folder_when_not_exists(self, mock_resolve, tmp_path: Path):
        """Test that _remove_folder handles missing folder gracefully."""
        package_path = tmp_path / "package"
        package_path.mkdir()
        mock_resolve.return_value = package_path
        
        # Folder doesn't exist - should not raise error
        _remove_folder(package_path, "nonexistent", "nonexistent")
        
        mock_resolve.assert_called_once_with(package_path)

    @patch('mapping_suite_sdk.tools.services.convert_mapping_package._resolve_package_root')
    def test_remove_folder_uses_original_path_when_resolve_returns_none(
        self,
        mock_resolve,
        tmp_path: Path
    ):
        """Test that _remove_folder uses original path when _resolve_package_root returns None."""
        package_path = tmp_path / "package"
        package_path.mkdir()
        mock_resolve.return_value = None
        
        test_folder = package_path / "test_folder"
        test_folder.mkdir()
        (test_folder / "file.txt").write_text("content")
        
        _remove_folder(package_path, "test_folder", "test_folder")
        
        assert not test_folder.exists()

