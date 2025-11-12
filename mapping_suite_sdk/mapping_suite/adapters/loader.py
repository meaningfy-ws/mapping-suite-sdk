import json
from pathlib import Path

from mapping_suite_sdk import mssdk_config
from mapping_suite_sdk.core.adapters.loader import AssetLoader, Loader
from mapping_suite_sdk.core.adapters.tracer import traced_class
from mapping_suite_sdk.mapping_suite.models.mapping_suite import (
    MappingSuite,
    MappingSuiteConfig,
    ResourcesCollection,
)


class MappingSuiteConfigLoader(AssetLoader):
    """Loader for mapping suite configuration.

    Handles loading and parsing of the mapping suite config JSON file.
    This file contains metadata, extraction rules, probing specs, and eligibility mappings.
    """

    def load(self, package_folder_path: Path, relative_asset_path: Path) -> MappingSuiteConfig:
        """Load mapping suite configuration from JSON file.

        Args:
            package_folder_path (Path): Path to the mapping suite package folder.
            relative_asset_path (Path): Path to the config file relative to the package folder.

        Returns:
            MappingSuiteConfig: Parsed configuration object.

        Raises:
            FileNotFoundError: If the config file does not exist.
            json.JSONDecodeError: If the config file is not valid JSON.
            ValueError: If the config does not match the expected schema.
        """
        # Handle nested folder structure (like v3 does)
        root_folder: Path = package_folder_path / package_folder_path.name
        asset_path: Path = package_folder_path / relative_asset_path

        if root_folder.exists():
            asset_path = root_folder / relative_asset_path

        if not asset_path.exists():
            raise FileNotFoundError(f"Mapping suite config file not found: {asset_path}")

        # Load and parse JSON
        config_dict: dict = json.loads(asset_path.read_text())

        # Extract the mapping_suite_config section if it exists (handle full file structure)
        if "mapping_suite_config" in config_dict:
            config_dict = config_dict["mapping_suite_config"]

        # Validate and return Pydantic model
        return MappingSuiteConfig.model_validate(config_dict)


class ResourcesCollectionLoader(AssetLoader):
    """Loader for resources collection.

    Scans the resources directory and builds a ResourcesCollection model
    containing all resource file paths. Follows the same pattern as VocabularyMappingSuiteLoader.
    """

    def load(self, package_folder_path: Path, relative_asset_path: Path) -> ResourcesCollection:
        """Load resources collection from directory.

        Args:
            package_folder_path (Path): Path to the mapping suite package folder.
            relative_asset_path (Path): Path to the resources folder relative to the package folder.

        Returns:
            ResourcesCollection: Collection model with list of resource file paths.
        """
        # Handle nested folder structure (like v3 does)
        root_folder: Path = package_folder_path / package_folder_path.name
        asset_path: Path = package_folder_path / relative_asset_path

        if root_folder.exists():
            asset_path = root_folder / relative_asset_path
            package_folder_path = root_folder

        # If resources directory doesn't exist, return empty collection
        if not asset_path.exists() or not asset_path.is_dir():
            return ResourcesCollection(resource_files=None)

        # Collect all file paths relative to the package folder
        resource_files = []
        for file_path in asset_path.rglob("*"):
            if file_path.is_file():
                relative_path = str(file_path.relative_to(package_folder_path))
                resource_files.append(relative_path)

        # Sort for consistent ordering
        resource_files.sort()

        return ResourcesCollection(resource_files=resource_files if resource_files else None)


@traced_class
class MappingSuiteLoader(Loader):
    """Main loader for mapping suite packages.

    Coordinates the loading of all components of a mapping suite:
    - Configuration (metadata, extraction rules, eligibility mappings)
    - Resources collection (vocabulary, code lists, normalization tables)
    """

    def __init__(
        self,
        include_resources: bool = True,
    ):
        """Initialize the mapping suite loader.

        Args:
            include_resources (bool): Whether to scan and include resource files.
                Defaults to True.
        """
        self.include_resources = include_resources

    def __eq__(self, other):
        """Check equality based on configuration parameters."""
        if isinstance(other, MappingSuiteLoader):
            return self.include_resources == other.include_resources
        return False

    def load(self, package_folder_path: Path) -> MappingSuite:
        """Load all components of a mapping suite package.

        This method orchestrates the loading of:
        - Mapping suite configuration (metadata, extraction rules, eligibility mappings)
        - Resources collection (vocabulary files, code lists, etc.)

        Args:
            package_folder_path (Path): Path to the mapping suite package folder.

        Returns:
            MappingSuite: Complete mapping suite with all loaded components.

        Raises:
            FileNotFoundError: If required files are missing.
            json.JSONDecodeError: If JSON files are malformed.
            ValueError: If data does not match expected schemas.
        """
        # Load configuration
        mapping_suite_config = MappingSuiteConfigLoader().load(
            package_folder_path=package_folder_path,
            relative_asset_path=mssdk_config.MAPPING_SUITE_CONFIG_FILE_ASSET_PATH,
        )

        # Load resources collection
        if self.include_resources:
            resources_collection = ResourcesCollectionLoader().load(
                package_folder_path=package_folder_path,
                relative_asset_path=mssdk_config.MAPPING_SUITE_RESOURCES_COLLECTION_ASSET_PATH,
            )
        else:
            resources_collection = ResourcesCollection(resource_files=None)

        return MappingSuite(
            mapping_suite_config=mapping_suite_config,
            resources_collection=resources_collection,
        )