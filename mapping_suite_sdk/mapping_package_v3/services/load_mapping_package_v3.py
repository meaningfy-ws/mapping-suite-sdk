import logging
from pathlib import Path
from typing import Optional, List

from pydantic import ValidationError

from mapping_suite_sdk import mssdk_config
from mapping_suite_sdk.core.adapters.extractor import ArchiveExtractor, GitHubExtractor
from mapping_suite_sdk.core.adapters.repository import MongoDBRepository
from mapping_suite_sdk.core.adapters.tracer import traced_routine
from mapping_suite_sdk.mapping_package_v3.adapters.package_loader import MappingPackageV3Loader
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3

logger = logging.getLogger(__name__)


@traced_routine
def load_mapping_package_v3_from_folder(
        mapping_package_folder_path: Path,
        mapping_package_loader: Optional[MappingPackageV3Loader] = None
) -> MappingPackageV3:
    if not mapping_package_folder_path.exists():
        raise FileNotFoundError(f"Mapping package folder not found: {mapping_package_folder_path}")
    if not mapping_package_folder_path.is_dir():
        raise NotADirectoryError(f"Specified path is not a directory: {mapping_package_folder_path}")

    mapping_package_loader = mapping_package_loader or MappingPackageV3Loader()

    return mapping_package_loader.load(mapping_package_folder_path)


@traced_routine
def load_mapping_package_v3_from_archive(
        mapping_package_archive_path: Path,
        mapping_package_loader: Optional[MappingPackageV3Loader] = None,
        archive_unpacker: Optional[ArchiveExtractor] = None
) -> MappingPackageV3:
    if not mapping_package_archive_path.exists():
        raise FileNotFoundError(f"Mapping package archive not found: {mapping_package_archive_path}")

    if not mapping_package_archive_path.is_file():
        raise ValueError(f"Specified path is not a file: {mapping_package_archive_path}")

    archive_unpacker: ArchiveExtractor = archive_unpacker or ArchiveExtractor()

    with archive_unpacker.extract_temporary(mapping_package_archive_path) as temp_mapping_package_folder_path:

        return load_mapping_package_v3_from_folder(mapping_package_folder_path=temp_mapping_package_folder_path,
                                                   mapping_package_loader=mapping_package_loader)


@traced_routine
def load_mapping_packages_v3_from_github(
        github_repository_url: str,
        packages_path_pattern: str,
        branch_or_tag_name: Optional[str] = None,
        github_package_extractor: Optional[GitHubExtractor] = None,
        mapping_package_loader: Optional[MappingPackageV3Loader] = None,
) -> List[MappingPackageV3]:
    if not github_repository_url:
        raise ValueError("Repository URL is required")

    if not packages_path_pattern:
        raise ValueError("Packages path pattern is required")

    github_extractor = github_package_extractor or GitHubExtractor()

    with github_extractor.extract_temporary(repository_url=github_repository_url,
                                            packages_path_pattern=packages_path_pattern,
                                            branch_or_tag_name=branch_or_tag_name
                                            ) as package_paths:
        if len(package_paths) < 1:
            raise ValueError(
                f"No mapping packages found matching pattern '{packages_path_pattern}' "
                f"in repository {github_repository_url} at {branch_or_tag_name}")

        mapping_packages: List[MappingPackageV3] = []
        for package_path in package_paths:
            try:
                package = load_mapping_package_v3_from_folder(
                    mapping_package_folder_path=package_path,
                    mapping_package_loader=mapping_package_loader
                )
                mapping_packages.append(package)
            except (ValidationError, Exception) as pydantic_validation_error:
                logger.warning(mssdk_config.MSSDK_LOGGING_MESSAGE_FORMAT.format(package_source=package_path,
                                                                                message=f"Cannot load package {package_path} from GitHub:\n{pydantic_validation_error}\nSkipping {package_path}"))
        return mapping_packages


@traced_routine
def load_mapping_package_v2_from_mongo_db(
        mapping_package_id: str,
        mapping_package_repository: MongoDBRepository[MappingPackageV3]
) -> MappingPackageV3:
    if not mapping_package_id:
        raise ValueError("Mapping package ID must be provided")

    if not mapping_package_repository:
        raise ValueError("MongoDB repository must be provided")

    return mapping_package_repository.read(mapping_package_id)
