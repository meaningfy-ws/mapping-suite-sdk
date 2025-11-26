import json
import tempfile
from pathlib import Path

import pytest

from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_metadata_loader import MappingPackageV3MetadataLoader


def test_mp_v3_metadata_loader_handles_missing_file() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        loader = MappingPackageV3MetadataLoader()

        with pytest.raises(FileNotFoundError):
            loader.load(temp_dir_path, relative_asset_path=Path("non_existing_path.json"))


def test_mp_v3_metadata_loader_handles_invalid_json() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        metadata_path = temp_dir_path / "metadata.json"
        metadata_path.write_text("invalid json content")

        loader = MappingPackageV3MetadataLoader()

        with pytest.raises(json.JSONDecodeError):
            loader.load(temp_dir_path, relative_asset_path=metadata_path)
