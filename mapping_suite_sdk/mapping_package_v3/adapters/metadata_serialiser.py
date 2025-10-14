from pathlib import Path

from mapping_suite_sdk.core.adapters.serialiser import MappingPackageAssetSerialiser
from mapping_suite_sdk.core.models.pydantic import fields
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_metadata import MappingPackageV3Metadata


class MappingPackageV3MetadataSerialiser(MappingPackageAssetSerialiser):
    """Serialiser for mapping package metadata."""

    def serialise(self, package_folder_path: Path, asset: MappingPackageV3Metadata) -> None:
        metadata_path = package_folder_path / asset.path
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(asset.model_dump_json(by_alias=True,
                                                       exclude={fields(MappingPackageV3Metadata).path},
                                                       # For V3 (Unified)
                                                       exclude_none=True,
                                                       indent=4))
