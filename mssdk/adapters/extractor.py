import tempfile
import zipfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Protocol


class Extractor(Protocol):
    """Protocol defining the interface for file extract operations.

    This protocol establishes a contract for classes that provide temporary file
    extraction capabilities with automatic cleanup. Implementations must provide
    a context manager that handles the extraction process and cleanup.
    """

    @staticmethod
    @contextmanager
    def extract_temporary(source_path: Path) -> Generator[Path, None, None]:
        """Extract content to a temporary directory and yield its path.

        This context manager should handle the extraction of files to a temporary
        location and ensure proper cleanup after use.

        Args:
            source_path: Path to the source file to extract

        Yields:
            Path: Path to the temporary directory containing the extracted contents

        Raises:
            NotImplementedError: When the method is not implemented by a concrete class
        """
        raise NotImplementedError


class ArchiveExtractor(Extractor):
    """Implementation of Extractor protocol for ZIP file operations.

    This class provides functionality to:
    - Extract ZIP files to a temporary directory with automatic cleanup
    - Pack directories into ZIP files without including the root directory name
    """

    @staticmethod
    @contextmanager
    def extract_temporary(archive_path: Path) -> Generator[Path, None, None]:
        """Extract a ZIP archive to a temporary directory and yield its path.

        This context manager handles the extraction of ZIP files to a temporary
        location and ensures proper cleanup after use.

        Args:
            archive_path: Path to the ZIP file to extract

        Yields:
            Path: Path to the temporary directory containing the extracted contents

        Raises:
            FileNotFoundError: If the archive file doesn't exist
            ValueError: If the path is not a file
            zipfile.BadZipFile: If the file is not a valid ZIP archive

        Example:
            >>> from pathlib import Path
            >>> archive_path = Path("example.zip")
            >>> with ArchiveExtractor.extract_temporary(archive_path) as temp_path:
            ...     # Work with extracted files in temp_path
            ...     pass  # Cleanup is automatic after the with block
        """
        if not archive_path.exists():
            raise FileNotFoundError(f"ZIP file not found: {archive_path}")

        if not archive_path.is_file():
            raise ValueError(f"Specified path is not a file: {archive_path}")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)

            try:
                with zipfile.ZipFile(archive_path) as zip_ref:
                    zip_ref.extractall(temp_dir_path)
                yield temp_dir_path

            except Exception as e:
                raise ValueError(f"Failed to extract ZIP file: {e}")

    @staticmethod
    def pack_directory(source_dir: Path, output_path: Path) -> Path:
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
            >>> zip_path = ArchiveExtractor.pack_directory(source_dir, output_path)
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
