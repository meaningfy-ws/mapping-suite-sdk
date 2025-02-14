import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Protocol


class Unpacker(Protocol):

    @staticmethod
    @contextmanager
    def extract_temporary(source_path: Path) -> Generator[Path, None, None]:
        raise NotImplementedError


class ArchiveUnpacker(Unpacker):

    @staticmethod
    @contextmanager
    def extract_temporary(archive_path: Path) -> Generator[Path, None, None]:

        if not archive_path.exists():
            raise FileNotFoundError(f"Archive file not found: {archive_path}")

        if not archive_path.is_file():
            raise ValueError(f"Specified path is not a file: {archive_path}")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)

            try:
                shutil.unpack_archive(archive_path, temp_dir_path)

                yield temp_dir_path

            except Exception as e:  # unpack_archive may raises multiple exceptions like BadZipFile
                raise ValueError(f"Failed to extract archive: {e}")
