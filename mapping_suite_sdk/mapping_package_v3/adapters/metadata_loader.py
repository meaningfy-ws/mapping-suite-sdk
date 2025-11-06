import json
from pathlib import Path

from mapping_suite_sdk.core.adapters.loader import MappingPackageAssetLoader
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3MetadataJSONLD


class MappingPackageV3MetadataLoader(MappingPackageAssetLoader):
    """Loader for mapping package metadata.

    Handles loading and parsing of the package metadata JSON file.
    """

    def load(self, package_folder_path: Path, relative_asset_path: Path) -> MappingPackageV3MetadataJSONLD:
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
        return MappingPackageV3MetadataJSONLD.model_validate(model_dict)
