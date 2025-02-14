import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Protocol


class Unpacker(Protocol):
    """Protocol defining the interface for file unpacking operations.

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


class ArchiveUnpacker(Unpacker):
    """Implementation of Unpacker protocol for archive file extraction.

    This class provides functionality to extract archive files (zip, tar, etc.)
    to a temporary directory with automatic cleanup. It supports various archive
    formats that are handled by shutil.unpack_archive.
    """

    @staticmethod
    @contextmanager
    def extract_temporary(archive_path: Path) -> Generator[Path, None, None]:
        """Extract an archive to a temporary directory and yield its path.

        This context manager handles the extraction of archive files to a temporary
        location and ensures proper cleanup after use. It supports various archive
        formats including zip, tar, and gztar.

        Args:
            archive_path: Path to the archive file to extract

        Yields:
            Path: Path to the temporary directory containing the extracted contents

        Raises:
            FileNotFoundError: If the archive file doesn't exist
            ValueError: If the path is not a file or if archive extraction fails
                       This includes cases of invalid or corrupted archives

        Example:
            >>> from pathlib import Path
            >>> archive_path = Path("example.zip")
            >>> with ArchiveUnpacker.extract_temporary(archive_path) as temp_path:
            ...     # Work with extracted files in temp_path
            ...     pass  # Cleanup is automatic after the with block
        """
        if not archive_path.exists():
            raise FileNotFoundError(f"Archive file not found: {archive_path}")

        if not archive_path.is_file():
            raise ValueError(f"Specified path is not a file: {archive_path}")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)

            try:
                shutil.unpack_archive(archive_path, temp_dir_path)
                yield temp_dir_path

            except Exception as e:  # unpack_archive may raise multiple exceptions like BadZipFile
                raise ValueError(f"Failed to extract archive: {e}")
