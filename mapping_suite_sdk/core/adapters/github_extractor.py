"""Extract mapping packages from GitHub repositories (needs the [github] extra)."""

import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from mapping_suite_sdk.core.adapters.extractor import ExtractorABC
from mapping_suite_sdk.core.adapters.optional_dependency import require
from mapping_suite_sdk.core.adapters.tracer import traced_class


@traced_class
class GitHubExtractor(ExtractorABC):
    """A mapping package extractor for GitHub repositories.

    This class provides functionality to clone and extract mapping packages from GitHub
    repositories. It supports:
    - Cloning specific packages from a repository
    - Pattern-based matching to find multiple packages
    - Branch, tag, and commit specific checkouts
    - Temporary and permanent extraction modes
    - Automatic cleanup of temporary files

    The extractor uses shallow cloning (depth=1) to minimize download size and time.

    Example:
        >>> extractor = GitHubExtractor()
        >>> # Extract a specific package
        >>> package_path = extractor.extract(
        ...     repository_url="https://github.com/org/repo",
        ...     destination_path=Path("/local/path"),
        ...     package_path=Path("mappings/package_v1"),
        ...     branch_or_tag_name="main"
        ... )
        >>>
        >>> # Extract multiple packages matching a pattern
        >>> with extractor.extract_temporary(
        ...     repository_url="https://github.com/org/repo",
        ...     packages_path_pattern="mappings/package*",
        ...     branch_or_tag_name="v1.0.0"
        ... ) as package_paths:
        ...     for path in package_paths:
        ...         # Process each package
        ...         pass
    """

    def extract(
        self,
        repository_url: str,
        destination_path: Path,
        package_path: Path,  # Relative to repo folder. Example: /mappings/package_can_v1.3
        branch_or_tag_name: str | None = None,
    ) -> Path:
        """Extract a specific package from a GitHub repository.

        This method clones a GitHub repository to a specified destination and returns
        the path to a specific package within that repository. The cloning operation
        uses depth=1 (shallow clone) to minimize download size and time.

        Args:
            repository_url: The URL of the GitHub repository
                (e.g., "https://github.com/org/repo")
            destination_path: Local path where the repository should be cloned
            package_path: Relative path to the package within the repository
                (e.g., Path("mappings/package_can_v1.3"))
            branch_or_tag_name: Name of the branch, tag, or commit to checkout
                (e.g., "main", "v1.0.0", "feature/new-mapping")

        Returns:
            Path: Path to the extracted package directory

        Raises:
            ValueError: If cloning fails or if any parameters are invalid
            git.exc.GitCommandError: If there are Git-specific errors
                (e.g., repository not found, invalid branch)

        Example:
            >>> extractor = GitHubExtractor()
            >>> package_path = extractor.extract(
            ...     repository_url="https://github.com/org/repo",
            ...     destination_path=Path("/local/path"),
            ...     package_path=Path("mappings/package_v1"),
            ...     branch_or_tag_name="main"
            ... )
            >>> # Package is now available at package_path
        """

        repo_class = require("git", "github", "GitHub").Repo
        if not destination_path.exists():
            raise ValueError(f"Failed to clone repository: Folder {destination_path} does not exist")

        try:
            if branch_or_tag_name:
                repo_class.clone_from(repository_url, destination_path, branch=branch_or_tag_name, depth=1)
            else:
                repo_class.clone_from(repository_url, destination_path, depth=1)
            return destination_path / package_path
        except Exception as e:
            raise ValueError(f"Failed to clone repository: {e}") from e

    @contextmanager
    def extract_temporary(
        self,
        repository_url: str,
        packages_path_pattern: str,  # Example: /mappings/package* or /mappings/*_can_*
        branch_or_tag_name: str | None = None,
    ) -> Generator[list[Path], None, None]:
        """Temporarily extract matching packages from a GitHub repository.

        This context manager clones a GitHub repository to a temporary location and yields
        paths to all packages matching the specified pattern. The temporary files are
        automatically cleaned up when the context manager exits.

        The packages_path_pattern supports glob-style patterns for flexible package matching.
        The cloning operation uses depth=1 (shallow clone) to minimize download size and time.

        Args:
            repository_url: The URL of the GitHub repository
                (e.g., "https://github.com/org/repo")
            packages_path_pattern: Glob pattern to match package paths within the repository
                (e.g., "mappings/package*" or "mappings/*_can_*")
            branch_or_tag_name: Name of the branch, tag, or commit to checkout
                (e.g., "main", "v1.0.0", "feature/new-mapping")

        Yields:
            List[Path]: List of paths to directories matching the package pattern.
                Each path is guaranteed to exist and be a directory.

        Raises:
            ValueError: If cloning fails or if any parameters are invalid
            git.exc.GitCommandError: If there are Git-specific errors
                (e.g., repository not found, invalid branch)

        Example:
            >>> extractor = GitHubExtractor()
            >>> with extractor.extract_temporary(
            ...     repository_url="https://github.com/org/repo",
            ...     packages_path_pattern="mappings/package*",
            ...     branch_or_tag_name="v1.0.0"
            ... ) as package_paths:
            ...     for path in package_paths:
            ...         # Process each package
            ...         print(f"Found package at: {path}")
            ...     # Temporary files are automatically cleaned up after the with block
        """
        if not repository_url:
            raise ValueError("Repository URL is required. Example: https://github.com/org/repo")

        if not packages_path_pattern:
            raise ValueError("Packages path pattern is required. Example: /mappings/package*")

        repo_class = require("git", "github", "GitHub").Repo
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            try:
                # TODO: Can be optimised: before cloning, to check the path pattern by yielding all top level files by using GitHub API
                if branch_or_tag_name:
                    repo_class.clone_from(repository_url, temp_dir_path, branch=branch_or_tag_name, depth=1)
                else:
                    repo_class.clone_from(repository_url, temp_dir_path, depth=1)
                yield [package_path for package_path in temp_dir_path.glob(packages_path_pattern) if package_path.is_dir()]
            except Exception as e:
                raise ValueError(f"Failed to get packages from repository: {e}") from e
