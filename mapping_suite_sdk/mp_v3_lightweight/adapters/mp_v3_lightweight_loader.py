import json
from pathlib import Path

from mapping_suite_sdk.core.adapters.loader import MappingPackageAssetLoader
from mapping_suite_sdk.mp_v3_lightweight.models.mapping_package_v3_lightweight_metadata_jsonld import MappingPackageV3LightweightMetadataJSONLD


class MappingPackageV3LightweightMetadataLoader(MappingPackageAssetLoader):
    """Loader for mapping package metadata.

    Handles loading and parsing of the package metadata JSON file.
    """

    def load(self, package_folder_path: Path, relative_asset_path: Path) -> MappingPackageV3LightweightMetadataJSONLD:
        """Load metadata from the package's metadata.json file.

        Args:
            package_folder_path (Path): Path to the mapping package folder.
            relative_asset_path (Path): Path to the asset relative to the package folder.

        Returns:
            MappingPackageMetadata: Parsed metadata object.
        """

        # If the root folder persists
        root_folder: Path = package_folder_path / package_folder_path.name
        asset_path: Path = package_folder_path / relative_asset_path

        if root_folder.exists():
            asset_path = root_folder / relative_asset_path

        model_dict: dict = json.loads(asset_path.read_text())
        model_dict['path'] = asset_path.relative_to(package_folder_path)

        # return TypeAdapter(MappingPackageV3MetadataJSONLD).validate_python(model_dict)
        return MappingPackageV3LightweightMetadataJSONLD.model_validate(model_dict)
