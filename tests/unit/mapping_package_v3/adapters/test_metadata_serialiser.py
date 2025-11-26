import json
from pathlib import Path

import pytest

from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_metadata_serialiser import MappingPackageV3MetadataSerialiser
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


