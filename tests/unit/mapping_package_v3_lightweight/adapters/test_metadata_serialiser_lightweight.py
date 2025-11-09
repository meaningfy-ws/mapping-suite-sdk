import json
from pathlib import Path

from mapping_suite_sdk.mp_v3_lightweight.adapters.mp_v3_serialiser_lightweight import MappingPackageV3LightweightMetadataSerialiser
from mapping_suite_sdk.mp_v3_lightweight.models.mapping_package_v3_lightweight import MappingPackageV3Lightweight


def test_mp_v3_metadata_serialiser_creates_metadata_file(tmp_path: Path,
                                                         fixture_mapping_package_v3_model: MappingPackageV3Lightweight) -> None:
    serialiser = MappingPackageV3LightweightMetadataSerialiser()
    serialiser.serialise(tmp_path, fixture_mapping_package_v3_model.metadata)

    metadata_path = tmp_path / fixture_mapping_package_v3_model.metadata.path
    assert metadata_path.exists()
    assert metadata_path.is_file()


def test_mp_v3_metadata_serialiser_creates_parent_directories(tmp_path: Path,
                                                              fixture_mapping_package_v3_model: MappingPackageV3Lightweight) -> None:
    metadata = fixture_mapping_package_v3_model.metadata

    serialiser = MappingPackageV3LightweightMetadataSerialiser()
    serialiser.serialise(tmp_path, metadata)

    metadata_path = tmp_path / metadata.path
    assert metadata_path.exists()
    assert metadata_path.parent.exists()


def test_mp_v3_metadata_serialiser_jsonld_format(tmp_path: Path,
                                                 fixture_mapping_package_v3_model: MappingPackageV3Lightweight) -> None:
    serialiser = MappingPackageV3LightweightMetadataSerialiser()
    serialiser.serialise(tmp_path, fixture_mapping_package_v3_model.metadata)
    metadata_path = tmp_path / fixture_mapping_package_v3_model.metadata.path
    content = metadata_path.read_text()

    parsed_json = json.loads(content)

    assert metadata_path.suffix == ".jsonld"

    assert isinstance(parsed_json, dict)


def test_mp_v3_metadata_serialiser_excludes_path_field(tmp_path: Path,
                                                       fixture_mapping_package_v3_model: MappingPackageV3Lightweight) -> None:
    serialiser = MappingPackageV3LightweightMetadataSerialiser()
    serialiser.serialise(tmp_path, fixture_mapping_package_v3_model.metadata)

    metadata_path = tmp_path / fixture_mapping_package_v3_model.metadata.path
    content = metadata_path.read_text()
    parsed_json = json.loads(content)

    assert "path" not in parsed_json


def test_mp_v3_metadata_serialiser_pretty_formatted(tmp_path: Path,
                                                    fixture_mapping_package_v3_model: MappingPackageV3Lightweight) -> None:
    serialiser = MappingPackageV3LightweightMetadataSerialiser()
    serialiser.serialise(tmp_path, fixture_mapping_package_v3_model.metadata)

    metadata_path = tmp_path / fixture_mapping_package_v3_model.metadata.path
    content = metadata_path.read_text()

    assert "\n" in content
    assert "  " in content


def test_mp_v3_metadata_serialiser_excludes_none_values(tmp_path: Path,
                                                        fixture_mapping_package_v3_model: MappingPackageV3Lightweight) -> None:
    metadata = fixture_mapping_package_v3_model.metadata

    serialiser = MappingPackageV3LightweightMetadataSerialiser()
    serialiser.serialise(tmp_path, metadata)

    metadata_path = tmp_path / metadata.path
    content = metadata_path.read_text()
    parsed_json = json.loads(content)

    for value in parsed_json.values():
        assert value is not None
