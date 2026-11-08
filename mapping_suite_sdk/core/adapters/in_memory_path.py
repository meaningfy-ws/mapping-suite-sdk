"""An in-memory stand-in for ``pathlib.Path`` over the files of a ZIP archive.

The loaders, the version detector and the serialisers use a small part of the ``Path`` API; this class implements
exactly that part on a ``dict[str, bytes]`` so a package can be loaded or written without touching the disk.
"""

import io
import zipfile
from collections.abc import Iterator
from fnmatch import fnmatchcase
from pathlib import Path, PurePosixPath
from typing import BinaryIO, ClassVar, TextIO


class InMemoryPath(PurePosixPath):
    """A path into the files of one archive, keyed by absolute posix path.

    ``from_zip`` makes a fresh subclass per archive, so paths derived with ``/`` (which build ``type(self)``
    on Python 3.10-3.13) keep sharing that archive's files.
    """

    _files: ClassVar[dict[str, bytes]] = {}

    @classmethod
    def from_zip(cls, data: bytes | BinaryIO) -> "InMemoryPath":
        """Read a ZIP and return its root: the one top-level folder holding every file, else ``/``.

        ``__MACOSX/`` entries are skipped.

        Raises:
            ValueError: If ``data`` is not a ZIP archive.
        """
        try:
            with zipfile.ZipFile(io.BytesIO(data) if isinstance(data, bytes) else data) as archive:
                files = {
                    "/" + name: archive.read(name)
                    for name in archive.namelist()
                    # macOS Finder adds __MACOSX/ metadata next to the package folder
                    if not name.endswith("/") and not name.startswith("__MACOSX/")
                }
        except zipfile.BadZipFile as e:
            raise ValueError(f"Failed to extract ZIP file: {e}") from e

        archive_class = type(cls.__name__, (cls,), {"_files": files})
        top_levels = {name.split("/")[1] for name in files}
        wrapped = len(top_levels) == 1 and all(name.count("/") > 1 for name in files)
        return archive_class("/" + top_levels.pop() if wrapped else "/")

    @classmethod
    def empty(cls) -> "InMemoryPath":
        """Return the root (``/``) of a new, empty archive to write into."""
        return type(cls.__name__, (cls,), {"_files": {}})("/")

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
