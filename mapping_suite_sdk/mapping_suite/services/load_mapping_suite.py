import logging
from pathlib import Path
from typing import Optional

from mapping_suite_sdk.core.adapters.extractor import ArchiveExtractor, GitHubExtractor
from mapping_suite_sdk.core.adapters.repository import MongoDBRepository
from mapping_suite_sdk.core.adapters.tracer import traced_routine
from mapping_suite_sdk.mapping_suite.adapters.loader import MappingSuiteLoader
from mapping_suite_sdk.mapping_suite.models.mapping_suite import MappingSuite

logger = logging.getLogger(__name__)


@traced_routine
def load_mapping_suite_from_folder(
        mapping_suite_folder_path: Path,
        mapping_suite_loader: Optional[MappingSuiteLoader] = None
) -> MappingSuite:
    """Load a mapping suite (project-level configuration) from a folder.

    A mapping suite is a project-level configuration that contains:
    - mapping_suite_config.json: Core configuration with metadata, document probing rules,
      extraction specifications, and eligibility mappings for selecting mapping packages
    - resources/: Directory containing vocabulary resources, code lists, and auxiliary files

    This is distinct from a mapping package, which contains transformation rules and artifacts
    (RML mappings, test data, validation suites) for actual data transformation.

    Args:
        mapping_suite_folder_path (Path): Path to the mapping suite folder.
        mapping_suite_loader (Optional[MappingSuiteLoader]): Custom loader instance.
            If None, a default loader is created.

    Returns:
        MappingSuite: The loaded mapping suite (project configuration).

    Raises:
        FileNotFoundError: If the folder does not exist.
        NotADirectoryError: If the path is not a directory.
    """
    if not mapping_suite_folder_path.exists():
        raise FileNotFoundError(f"Mapping suite folder not found: {mapping_suite_folder_path}")
    if not mapping_suite_folder_path.is_dir():
        raise NotADirectoryError(f"Specified path is not a directory: {mapping_suite_folder_path}")

    mapping_suite_loader = mapping_suite_loader or MappingSuiteLoader()

    return mapping_suite_loader.load(mapping_suite_folder_path)


@traced_routine
def load_mapping_suite_from_archive(
        mapping_suite_archive_path: Path,
        mapping_suite_loader: Optional[MappingSuiteLoader] = None,
        archive_unpacker: Optional[ArchiveExtractor] = None
) -> MappingSuite:
    """Load a mapping suite (project-level configuration) from an archive file.

    A mapping suite is a project-level configuration (see load_mapping_suite_from_folder
    for details). This function extracts the archive and loads the suite from the
    extracted folder.

    Supports common archive formats (zip, tar, tar.gz, etc.).

    Args:
        mapping_suite_archive_path (Path): Path to the mapping suite archive file.
        mapping_suite_loader (Optional[MappingSuiteLoader]): Custom loader instance.
        archive_unpacker (Optional[ArchiveExtractor]): Custom archive extractor instance.

    Returns:
        MappingSuite: The loaded mapping suite (project configuration).

    Raises:
        FileNotFoundError: If the archive file does not exist.
        ValueError: If the path is not a file.
    """
    if not mapping_suite_archive_path.exists():
        raise FileNotFoundError(f"Mapping suite archive not found: {mapping_suite_archive_path}")

    if not mapping_suite_archive_path.is_file():
        raise ValueError(f"Specified path is not a file: {mapping_suite_archive_path}")

    archive_unpacker: ArchiveExtractor = archive_unpacker or ArchiveExtractor()

    with archive_unpacker.extract_temporary(mapping_suite_archive_path) as temp_mapping_suite_folder_path:
        return load_mapping_suite_from_folder(
            mapping_suite_folder_path=temp_mapping_suite_folder_path,
            mapping_suite_loader=mapping_suite_loader
        )


@traced_routine
def load_mapping_suites_from_github(
        github_repository_url: str,
        suites_path_pattern: str,
        branch_or_tag_name: Optional[str] = None,
        github_suite_extractor: Optional[GitHubExtractor] = None,
        mapping_suite_loader: Optional[MappingSuiteLoader] = None,
) -> list[MappingSuite]:
    """Load mapping suites (project-level configurations) from a GitHub repository.

    A mapping suite is a project-level configuration (see load_mapping_suite_from_folder
    for details), distinct from mapping packages which contain transformation rules.

    Extracts all suites matching the specified path pattern and loads them.

    Args:
        github_repository_url (str): GitHub repository URL (e.g., https://github.com/owner/repo).
        suites_path_pattern (str): Glob pattern to find suites (e.g., mapping_suites/my_suite).
        branch_or_tag_name (Optional[str]): Specific branch or tag to extract from.
            If None, uses default branch.
        github_suite_extractor (Optional[GitHubExtractor]): Custom GitHub extractor instance.
        mapping_suite_loader (Optional[MappingSuiteLoader]): Custom loader instance.

    Returns:
        list[MappingSuite]: The loaded mapping suites (project configurations).

    Raises:
        ValueError: If repository URL or pattern is empty/missing, or if no suites match the pattern.
    """
    if not github_repository_url:
        raise ValueError("Repository URL is required")

    if not suites_path_pattern:
        raise ValueError("Suites path pattern is required")

    github_extractor = github_suite_extractor or GitHubExtractor()

    # Note: GitHubExtractor.extract_temporary uses 'packages_path_pattern' parameter name,
    # but we're using it for suites. This is a conceptual conflation - the extractor is
    # package-oriented but being reused for suites. Consider refactoring to have separate
    # extractors or a more generic path_pattern parameter to properly distinguish packages
    # from suites.
    with github_extractor.extract_temporary(
            repository_url=github_repository_url,
            packages_path_pattern=suites_path_pattern,  # Note: parameter name suggests packages, but used for suites
            branch_or_tag_name=branch_or_tag_name
    ) as suite_paths:
        if len(suite_paths) < 1:
            raise ValueError(
                f"No mapping suites found matching pattern '{suites_path_pattern}' "
                f"in repository {github_repository_url} at {branch_or_tag_name}"
            )

        suites = []
        for suite_path in suite_paths:
            suite = (mapping_suite_loader or MappingSuiteLoader()).load(suite_path)
            suites.append(suite)

        return suites


@traced_routine
def load_mapping_suite_from_mongo_db(
        mapping_suite_id: str,
        mapping_suite_repository: MongoDBRepository[MappingSuite]
) -> MappingSuite:
    """Load a mapping suite from MongoDB.

    Args:
        mapping_suite_id (str): Unique identifier of the mapping suite in MongoDB.
        mapping_suite_repository (MongoDBRepository[MappingSuite]): Repository instance
            for accessing MongoDB.

    Returns:
        MappingSuite: The loaded mapping suite.

    Raises:
        ValueError: If suite ID or repository is missing/None.
        Exception: If database access fails (propagated from repository).
    """
    if not mapping_suite_id:
        raise ValueError("Mapping suite ID must be provided")

    if not mapping_suite_repository:
        raise ValueError("MongoDB repository must be provided")

    return mapping_suite_repository.read(mapping_suite_id)