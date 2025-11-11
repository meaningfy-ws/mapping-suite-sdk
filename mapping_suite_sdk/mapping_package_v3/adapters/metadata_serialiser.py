from pathlib import Path

from mapping_suite_sdk.core.adapters.serialiser import MappingPackageAssetSerialiser
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_metadata import MappingPackageV3Metadata
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_metadata_jsonld import \
    MappingPackageV3MetadataJSONLD


class MappingPackageV3MetadataSerialiser(MappingPackageAssetSerialiser):
    """Serialiser for mapping package metadata."""

    def serialise(self, package_folder_path: Path, asset: MappingPackageV3MetadataJSONLD) -> None:
        # Validate that asset is a proper model instance, not a mock
        if not isinstance(asset, MappingPackageV3MetadataJSONLD):
            raise TypeError(f"Expected MappingPackageV3MetadataJSONLD, got {type(asset).__name__}")
        
        # Validate that path is a string/Path, not a mock
        if not isinstance(asset.path, (str, Path)):
            raise TypeError(f"Expected path to be str or Path, got {type(asset.path).__name__}")
        
        metadata_path = package_folder_path / asset.path
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata = MappingPackageV3Metadata.model_construct(**asset.model_dump())
        metadata_path.write_text(metadata.model_dump_json(by_alias=True,
                                                          # For V3 (Unified)
                                                          exclude_none=True,
                                                          indent=4))
