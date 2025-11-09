from pathlib import Path

from mapping_suite_sdk.core.adapters.serialiser import MappingPackageAssetSerialiser
from mapping_suite_sdk.mp_v3_lightweight.models.mapping_package_v3_lightweight_metadata import MappingPackageV3LightweightMetadata
from mapping_suite_sdk.mp_v3_lightweight.models.mapping_package_v3_lightweight_metadata_jsonld import \
    MappingPackageV3LightweightMetadataJSONLD


class MappingPackageV3LightweightMetadataSerialiser(MappingPackageAssetSerialiser):
    """Serialiser for mapping package metadata."""

    def serialise(self, package_folder_path: Path, asset: MappingPackageV3LightweightMetadataJSONLD) -> None:
        metadata_path = package_folder_path / asset.path
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata = MappingPackageV3LightweightMetadata.model_construct(**asset.model_dump())
        metadata_path.write_text(metadata.model_dump_json(by_alias=True,
                                                          # For V3 (Unified)
                                                          exclude_none=True,
                                                          indent=4))
