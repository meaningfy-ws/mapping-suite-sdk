"""An in-memory stand-in for ``pathlib.Path`` over the files of a ZIP archive.

The loaders, the version detector and the serialisers use a small part of the ``Path`` API; this class implements
exactly that part on a ``dict[str, bytes]`` so a package can be loaded or written without touching the disk.

Loaders and serialisers that run on it must not use ``isinstance(path, Path)``, the builtin ``open``, ``os`` or
``shutil``, nor ``stat``/``resolve``: none of these are implemented here.
"""

import io
import zipfile
import zlib
from collections.abc import Iterator
from fnmatch import fnmatchcase
from pathlib import Path, PurePosixPath
from typing import BinaryIO, ClassVar, TextIO

MAX_UNCOMPRESSED_BYTES = 1024**3  # guard against ZIP bombs: the whole archive is held in memory


def _is_unsafe(key: str) -> bool:
    """True if an absolute archive key is not a plain path below the root (``..``, backslash, empty segment)."""
    return "\\" in key or "//" in key or ".." in key.split("/")


class InMemoryPath(PurePosixPath):
    """A path into the files of one archive, keyed by absolute posix path.

    ``from_zip`` makes a fresh subclass per archive, so paths derived with ``/`` (which build ``type(self)``
    on Python 3.10-3.13) keep sharing that archive's files.
    """

    # set per archive by from_zip/empty; the base class has no store, so using it directly fails with AttributeError
    _files: ClassVar[dict[str, bytes]]

    @classmethod
    def from_zip(cls, data: bytes | BinaryIO) -> "InMemoryPath":
        """Read a ZIP and return its root: the one top-level folder holding every file, else ``/``.

        ``__MACOSX/`` entries are skipped.

        Raises:
            ValueError: If ``data`` is not a readable ZIP archive, an entry name is unsafe (absolute, ``..``,
                backslash) or the files add up to more than ``MAX_UNCOMPRESSED_BYTES``.
        """
        try:
            with zipfile.ZipFile(io.BytesIO(data) if isinstance(data, bytes) else data) as archive:
                # macOS Finder adds __MACOSX/ metadata next to the package folder
                infos = [i for i in archive.infolist() if not i.is_dir() and not i.filename.startswith("__MACOSX/")]
                for info in infos:
                    if _is_unsafe("/" + info.filename):
                        raise ValueError(f"Failed to extract ZIP file: unsafe entry name {info.filename!r}")
                if sum(i.file_size for i in infos) > MAX_UNCOMPRESSED_BYTES:
                    raise ValueError(f"Failed to extract ZIP file: more than {MAX_UNCOMPRESSED_BYTES} bytes uncompressed")
                files = {"/" + i.filename: archive.read(i) for i in infos}
        except (zipfile.BadZipFile, NotImplementedError, RuntimeError, EOFError, zlib.error, OSError) as e:
            raise ValueError(f"Failed to extract ZIP file: {e}") from e

        archive_class = type(cls.__name__, (cls,), {"_files": files})
        top_levels = {name.split("/")[1] for name in files}
        wrapped = len(top_levels) == 1 and all(name.count("/") > 1 for name in files)
        return archive_class("/" + top_levels.pop() if wrapped else "/")

    @classmethod
    def empty(cls) -> "InMemoryPath":
        """Return the root (``/``) of a new, empty archive to write into."""
        return type(cls.__name__, (cls,), {"_files": {}})("/")

    def files(self) -> dict[str, bytes]:
        """Return a copy of the archive's files, keyed by name relative to the root ``/``."""
        return {name.lstrip("/"): content for name, content in self._files.items()}

    def to_zip(self) -> bytes:
        """Return the archive's files as the bytes of a ZIP."""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, content in self._files.items():
                archive.writestr(name.lstrip("/"), content)
        return buffer.getvalue()

    def mkdir(self, parents: bool = False, exist_ok: bool = False) -> None:
        """Do nothing: folders exist only as the prefix of a file."""

    def write_bytes(self, data: bytes) -> int:  # type: ignore[override]
        if _is_unsafe(str(self)):
            raise ValueError(f"Unsafe path in package: {str(self)!r}")
        self._files[str(self)] = data
        return len(data)

    def write_text(self, data: str, encoding: str = "utf-8") -> int:  # type: ignore[override]
        self.write_bytes(data.encode(encoding))
        return len(data)

    def is_file(self) -> bool:
        return str(self) in self._files

    def is_dir(self) -> bool:
        prefix = str(self).rstrip("/") + "/"
        return any(name.startswith(prefix) for name in self._files)

    def exists(self) -> bool:
        return self.is_file() or self.is_dir()

    def iterdir(self) -> Iterator["InMemoryPath"]:
        children = {ancestor for name in self._files for ancestor in PurePosixPath(name).parents if ancestor.parent == self}
        children |= {PurePosixPath(name) for name in self._files if PurePosixPath(name).parent == self}
        children.discard(PurePosixPath(self))
        for child in sorted(children):
            yield type(self)(child)

    def glob(self, pattern: str) -> Iterator["InMemoryPath"]:
        """Match ``pattern`` segment by segment with ``fnmatch`` (no ``**``)."""
        matches = [self]
        for segment in pattern.split("/"):
            matches = [child for parent in matches for child in parent.iterdir() if fnmatchcase(child.name, segment)]
        yield from matches

    def read_bytes(self) -> bytes:
        try:
            return self._files[str(self)]
        except KeyError:
            raise FileNotFoundError(f"No such file in the archive: {self}") from None

    def read_text(self, encoding: str = "utf-8") -> str:  # type: ignore[override]
        return self.read_bytes().decode(encoding)

    def open(self, mode: str = "r", encoding: str = "utf-8") -> TextIO | BinaryIO:
        if mode == "rb":
            return io.BytesIO(self.read_bytes())
        if mode == "r":
            return io.StringIO(self.read_text(encoding))
        raise ValueError(f"Unsupported mode for a read-only in-memory path: {mode!r}")

    def relative_to(self, other: "PurePosixPath | str") -> Path:  # type: ignore[override]
        """Return a real ``Path``: asset models validate ``path`` as ``Path``."""
        return Path(super().relative_to(other))
