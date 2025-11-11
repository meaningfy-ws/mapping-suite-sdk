import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from mapping_suite_sdk.mapping_package_v3.adapters.metadata_serialiser import MappingPackageV3MetadataSerialiser
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_metadata import MappingPackageV3Metadata


def test_mp_v3_metadata_serialiser_creates_metadata_file(tmp_path: Path,
                                                         fixture_mapping_package_v3_model: MappingPackageV3) -> None:
    serialiser = MappingPackageV3MetadataSerialiser()
    serialiser.serialise(tmp_path, fixture_mapping_package_v3_model.metadata)

    metadata_path = tmp_path / fixture_mapping_package_v3_model.metadata.path
    assert metadata_path.exists()
    assert metadata_path.is_file()


def test_mp_v3_metadata_serialiser_creates_parent_directories(tmp_path: Path,
                                                              fixture_mapping_package_v3_model: MappingPackageV3) -> None:
    metadata = fixture_mapping_package_v3_model.metadata

    serialiser = MappingPackageV3MetadataSerialiser()
    serialiser.serialise(tmp_path, metadata)

    metadata_path = tmp_path / metadata.path
    assert metadata_path.exists()
    assert metadata_path.parent.exists()


def test_mp_v3_metadata_serialiser_jsonld_format(tmp_path: Path,
                                                 fixture_mapping_package_v3_model: MappingPackageV3) -> None:
    serialiser = MappingPackageV3MetadataSerialiser()
    serialiser.serialise(tmp_path, fixture_mapping_package_v3_model.metadata)
    metadata_path = tmp_path / fixture_mapping_package_v3_model.metadata.path
    content = metadata_path.read_text()

    parsed_json = json.loads(content)

    assert metadata_path.suffix == ".jsonld"

    assert isinstance(parsed_json, dict)


def test_mp_v3_metadata_serialiser_excludes_path_field(tmp_path: Path,
                                                       fixture_mapping_package_v3_model: MappingPackageV3) -> None:
    serialiser = MappingPackageV3MetadataSerialiser()
    serialiser.serialise(tmp_path, fixture_mapping_package_v3_model.metadata)

    metadata_path = tmp_path / fixture_mapping_package_v3_model.metadata.path
    content = metadata_path.read_text()
    parsed_json = json.loads(content)

    assert "path" not in parsed_json


def test_mp_v3_metadata_serialiser_pretty_formatted(tmp_path: Path,
                                                    fixture_mapping_package_v3_model: MappingPackageV3) -> None:
    serialiser = MappingPackageV3MetadataSerialiser()
    serialiser.serialise(tmp_path, fixture_mapping_package_v3_model.metadata)

    metadata_path = tmp_path / fixture_mapping_package_v3_model.metadata.path
    content = metadata_path.read_text()

    assert "\n" in content
    assert "  " in content


def test_mp_v3_metadata_serialiser_excludes_none_values(tmp_path: Path,
                                                        fixture_mapping_package_v3_model: MappingPackageV3) -> None:
    metadata = fixture_mapping_package_v3_model.metadata

    serialiser = MappingPackageV3MetadataSerialiser()
    serialiser.serialise(tmp_path, metadata)

    metadata_path = tmp_path / metadata.path
    content = metadata_path.read_text()
    parsed_json = json.loads(content)

    for value in parsed_json.values():
        assert value is not None


def test_mp_v3_metadata_serialiser_rejects_mock_asset(tmp_path: Path) -> None:
    """Test that MappingPackageV3MetadataSerialiser rejects MagicMock assets."""
    serialiser = MappingPackageV3MetadataSerialiser()
    mock_asset = MagicMock()

    with pytest.raises(TypeError) as excinfo:
        serialiser.serialise(tmp_path, mock_asset)
    
    assert "Expected MappingPackageV3MetadataJSONLD" in str(excinfo.value)
    assert "MagicMock" in str(excinfo.value) or "got" in str(excinfo.value)


def test_mp_v3_metadata_serialiser_rejects_mock_path(tmp_path: Path,
                                                     fixture_mapping_package_v3_model: MappingPackageV3) -> None:
    """Test that MappingPackageV3MetadataSerialiser rejects assets with mock paths."""
    serialiser = MappingPackageV3MetadataSerialiser()
    metadata = fixture_mapping_package_v3_model.metadata
    
    # Use object.__setattr__ to bypass Pydantic validation
    object.__setattr__(metadata, 'path', MagicMock())  # Replace path with mock

    with pytest.raises(TypeError) as excinfo:
        serialiser.serialise(tmp_path, metadata)
    
    assert "Expected path to be str or Path" in str(excinfo.value)
    assert "MagicMock" in str(excinfo.value) or "got" in str(excinfo.value)


def test_mp_v3_metadata_serialiser_rejects_wrong_type(tmp_path: Path,
                                                      fixture_mapping_package_v3_model: MappingPackageV3) -> None:
    """Test that MappingPackageV3MetadataSerialiser rejects wrong asset types."""
    serialiser = MappingPackageV3MetadataSerialiser()
    
    # Create a MappingPackageV3Metadata (not JSONLD) instance
    # We need to get the base metadata and try to use it
    # Since we can't easily create a MappingPackageV3Metadata from JSONLD, 
    # we'll use model_construct to create a minimal instance
    metadata_dict = fixture_mapping_package_v3_model.metadata.model_dump()
    wrong_metadata = MappingPackageV3Metadata.model_construct(**metadata_dict)

    with pytest.raises(TypeError) as excinfo:
        serialiser.serialise(tmp_path, wrong_metadata)  # type: ignore
    
    assert "Expected MappingPackageV3MetadataJSONLD" in str(excinfo.value)
    assert "MappingPackageV3Metadata" in str(excinfo.value)
