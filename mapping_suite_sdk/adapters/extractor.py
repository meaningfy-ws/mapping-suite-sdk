import tempfile
import zipfile
from abc import ABC, abstractmethod
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Any, List, Optional

from git import Repo

from mapping_suite_sdk.adapters.tracer import traced_class


class MappingPackageExtractorABC(ABC):
    """Abstract base class defining the interface for mapping package extract operations.

    This abstract class establishes a contract for classes that provide file
    extraction capabilities. The interface is designed to be flexible, allowing
    implementations to define their own argument structure for both permanent
    and temporary extraction operations.
    """

    @abstractmethod
    def extract(self, *args: Any, **kwargs: Any) -> Any:
        """Extract content to a specified destination.

        This method should be implemented to handle the extraction of content
        according to the specific needs of the implementing class. The argument
        structure is deliberately flexible to allow different implementations
        to define their own parameter requirements.

        Args:
            *args: Variable positional arguments specific to the implementation
            **kwargs: Variable keyword arguments specific to the implementation

        Returns:
            Implementation-specific return type

        Raises:
            NotImplementedError: When the method is not implemented by a concrete class
        """
        raise NotImplementedError

    @contextmanager
    @abstractmethod
    def extract_temporary(self, *args: Any, **kwargs: Any) -> Generator[Any, None, None]:
        """Extract content to a temporary location and yield its path.

        This context manager should handle the extraction of content to a temporary
        location and ensure proper cleanup after use. The argument structure is
        deliberately flexible to allow different implementations to define their
        own parameter requirements.

        Args:
            *args: Variable positional arguments specific to the implementation
            **kwargs: Variable keyword arguments specific to the implementation

        Yields:
            Implementation-specific yield type

        Raises:
            NotImplementedError: When the method is not implemented by a concrete class
        """
        raise NotImplementedError


@traced_class
class ArchivePackageExtractor(MappingPackageExtractorABC):
    """Implementation of MappingPackageExtractorABC for ZIP file operations.

    This class provides functionality to:
    - Extract ZIP files to a temporary directory with automatic cleanup
    - Extract ZIP files to a specified destination
    - Pack directories into ZIP files without including the root directory name
    """

    def extract(self, source_path: Path, destination_path: Path) -> Path:
        """Extract a ZIP archive to a specified destination directory.

        Args:
            source_path: Path to the ZIP file to extract
            destination_path: Path where the content should be extracted

        Returns:
            Path: Path to the directory containing the extracted contents

        Raises:
            FileNotFoundError: If the archive file doesn't exist
            ValueError: If the path is not a file
            zipfile.BadZipFile: If the file is not a valid ZIP archive

        Example:
            >>> from pathlib import Path
            >>> archive_path = Path("example.zip")
            >>> dest_path = Path("output_dir")
            >>> extracted_path = ArchivePackageExtractor().extract(archive_path, dest_path)
        """
        if not source_path.exists():
            raise FileNotFoundError(f"ZIP file not found: {source_path}")

        if not source_path.is_file():
            raise ValueError(f"Specified path is not a file: {source_path}")

        # Ensure the destination directory exists
        destination_path.mkdir(parents=True, exist_ok=True)
        destination_path = destination_path / source_path.stem

        try:
            with zipfile.ZipFile(source_path) as zip_ref:
                zip_ref.extractall(destination_path)
            return destination_path

        except Exception as e:
            raise ValueError(f"Failed to extract ZIP file: {e}")

    @contextmanager
    def extract_temporary(self, source_path: Path) -> Generator[Path, None, None]:
        """Extract a ZIP archive to a temporary directory and yield its path.

        This context manager handles the extraction of ZIP files to a temporary
        location and ensures proper cleanup after use.

        Args:
            source_path: Path to the ZIP file to extract

        Yields:
            Path: Path to the temporary directory containing the extracted contents

        Raises:
            FileNotFoundError: If the archive file doesn't exist
            ValueError: If the path is not a file
            zipfile.BadZipFile: If the file is not a valid ZIP archive

        Example:
            >>> from pathlib import Path
            >>> archive_path = Path("example.zip")
            >>> extractor = ArchivePackageExtractor()
            >>> with extractor.extract_temporary(archive_path) as temp_path:
            ...     # Work with extracted files in temp_path
            ...     pass  # Cleanup is automatic after the with block
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            try:
                yield self.extract(source_path, temp_dir_path)
            except Exception as e:
                raise ValueError(f"Failed to extract ZIP file {source_path}: {e}")

    def pack_directory(self, source_dir: Path, output_path: Path) -> Path:
        """Pack a directory's contents into a ZIP file without including the root directory name.

        Creates a ZIP file containing the contents of the specified directory.
        Files and subdirectories will be packed without the root directory name.
        For example, if packing a directory 'my_folder' containing 'file1.txt' and
        'subfolder/file2.txt', the ZIP will contain 'file1.txt' and 'subfolder/file2.txt'
        directly, without 'my_folder' at the start.

        Args:
            source_dir: Path to the directory to pack
            output_path: Path where the ZIP file should be created.
                        If it doesn't end with '.zip', the extension will be added.

        Returns:
            Path: Path to the created ZIP file

        Raises:
            FileNotFoundError: If the source directory doesn't exist
            ValueError: If the source is not a directory or if ZIP creation fails

        Example:
            >>> from pathlib import Path
            >>> source_dir = Path("folder_to_archive")
            >>> output_path = Path("output/archive")
            >>> zip_path = ArchivePackageExtractor.pack_directory(source_dir, output_path)
        """
        if not source_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {source_dir}")

        if not source_dir.is_dir():
            raise ValueError(f"Specified path is not a directory: {source_dir}")

        # Ensure the output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Ensure the output path has .zip extension
        if not str(output_path).endswith('.zip'):
            output_path = output_path.with_suffix('.zip')

        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
                # Get all files in the directory
                for file_path in source_dir.rglob('*'):
                    if file_path.is_file():  # Skip directories, they're created automatically
                        # Calculate the path relative to the source directory
                        relative_path = file_path.relative_to(source_dir)
                        # Add the file to the ZIP with the relative path as its name
                        zip_ref.write(file_path, relative_path)

            return output_path

        except Exception as e:
            raise ValueError(f"Failed to create ZIP file: {e}")


@traced_class
class GithubPackageExtractor(MappingPackageExtractorABC):
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
        >>> extractor = GithubPackageExtractor()
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
            branch_or_tag_name: Optional[str] = None
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
            >>> extractor = GithubPackageExtractor()
            >>> package_path = extractor.extract(
            ...     repository_url="https://github.com/org/repo",
            ...     destination_path=Path("/local/path"),
            ...     package_path=Path("mappings/package_v1"),
            ...     branch_or_tag_name="main"
            ... )
            >>> # Package is now available at package_path
        """

        if not destination_path.exists():
            raise ValueError(f"Failed to clone repository: Folder {destination_path} does not exist")

        try:
            if branch_or_tag_name:
                Repo.clone_from(repository_url, destination_path, branch=branch_or_tag_name, depth=1)
            else:
                Repo.clone_from(repository_url, destination_path, depth=1)
            return destination_path / package_path
        except Exception as e:
            raise ValueError(f"Failed to clone repository: {e}")

    @contextmanager
    def extract_temporary(
            self,
            repository_url: str,
            packages_path_pattern: str,  # Example: /mappings/package* or /mappings/*_can_*
            branch_or_tag_name: Optional[str] = None
    ) -> Generator[List[Path], None, None]:
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
            >>> extractor = GithubPackageExtractor()
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

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            try:
                # TODO: Can be optimised: before cloning, to check the path pattern by yielding all top level files by using GitHub API
                if branch_or_tag_name:
                    Repo.clone_from(repository_url, temp_dir_path, branch=branch_or_tag_name, depth=1)
                else:
                    Repo.clone_from(repository_url, temp_dir_path, depth=1)
                yield [package_path for package_path in temp_dir_path.glob(packages_path_pattern) if
                       package_path.is_dir()]
            except Exception as e:
                raise ValueError(f"Failed to get packages from repository: {e}")
