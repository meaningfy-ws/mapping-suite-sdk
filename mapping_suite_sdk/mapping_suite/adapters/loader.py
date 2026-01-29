import csv
import json
import logging
from pathlib import Path

from mapping_suite_sdk import mssdk_config
from mapping_suite_sdk.core.adapters.loader import AssetLoader, Loader
from mapping_suite_sdk.core.adapters.tracer import traced_class
from mapping_suite_sdk.mapping_suite.models.mapping_suite import (
    MappingSuite,
    MappingSuiteConfig,
    ResourceReferences,
)

logger = logging.getLogger(__name__)


class MappingSuiteConfigLoader(AssetLoader):
    """Loader for mapping suite configuration.

    Handles loading and parsing of the mapping suite config JSON file.
    This file contains metadata, extraction rules, probing specs, and eligibility mappings.
    """

    def load(self, project_folder_path: Path, relative_asset_path: Path) -> MappingSuiteConfig:
        """Load mapping suite configuration from JSON file.

        Args:
            project_folder_path (Path): Path to the mapping suite folder.
            relative_asset_path (Path): Path to the asset relative to the mapping suite folder.

        Returns:
            MappingSuiteConfig: Parsed configuration object.

        Raises:
            FileNotFoundError: If the config file does not exist.
            json.JSONDecodeError: If the config file is not valid JSON.
            ValueError: If the config does not match the expected schema.
        """
        metadata_asset_path: Path = project_folder_path / relative_asset_path

        if not metadata_asset_path.exists():
            raise FileNotFoundError(f"Mapping suite config file not found: {metadata_asset_path}")

        # Load and parse JSON
        config_dict: dict = json.loads(metadata_asset_path.read_text())

        # Validate and return Pydantic model
        return MappingSuiteConfig.model_validate(config_dict)


class ResourceReferencesLoader(AssetLoader):
    """Loader for resource references.

    Loads and parses resource files from the mapping suite config object.
    """

    def load(self, package_folder_path: Path, config: MappingSuiteConfig) -> list[dict] | None:
        """Load and parse resources from config object.

        Args:
            package_folder_path (Path): Path to the mapping suite package folder.
            config (MappingSuiteConfig): Already loaded mapping suite config.

        Returns:
            list[dict]: List of dicts with file_name and object (parsed content).
        """
        file_paths = config.resource_references.file_paths if config.resource_references else []

        resource_file_contents = []
        for rel_path in file_paths:
            abs_path = package_folder_path / rel_path.lstrip("/")
            if abs_path.exists():
                try:
                    if abs_path.suffix == ".json":
                        obj = json.loads(abs_path.read_text())
                    elif abs_path.suffix == ".csv":
                        with abs_path.open(newline='', encoding='utf-8') as csvfile:
                            reader = csv.DictReader(csvfile)
                            obj = list(reader)
                    else:
                        obj = abs_path.read_text()
                    resource_file_contents.append({
                        "file_name": rel_path,
                        "object": obj
                    })
                except (json.JSONDecodeError, UnicodeDecodeError, csv.Error) as e:
                    logger.warning(f"Failed to load resource file '{rel_path}': {type(e).__name__}: {e}")  # pragma: no cover
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error loading resource file '{rel_path}': {type(e).__name__}: {e}")  # pragma: no cover
                    continue
            else:
                logger.warning(f"Resource file not found: '{rel_path}' (expected at {abs_path})")  # pragma: no cover
        resource_file_contents.sort(key=lambda x: x["file_name"])
        return resource_file_contents if resource_file_contents else None


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
            project_folder_path=package_folder_path,
            relative_asset_path=mssdk_config.mapping_suite_config_file_asset_path,
        )

        # Load resource file contents if requested
        if self.include_resources:
            resource_file_contents = ResourceReferencesLoader().load(
                package_folder_path=package_folder_path,
                config=mapping_suite_config,
            )
        else:
            resource_file_contents = None

        return MappingSuite(
            mapping_suite_config=mapping_suite_config,
            resource_file_contents=resource_file_contents,
        )
