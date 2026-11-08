"""Services for writing a MappingPackageV3 as ZIP bytes, a ZIP file or a folder."""

from pathlib import Path
from typing import cast

from mapping_suite_sdk.core.adapters.in_memory_path import InMemoryPath
from mapping_suite_sdk.core.adapters.tracer import traced_routine
from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_hasher import MappingPackageV3Hasher
from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_package_serialiser import MappingPackageV3Serialiser
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3


def _update_hash(package: MappingPackageV3) -> None:
    package.metadata.mapping_suite_hash_digest = MappingPackageV3Hasher(package).hash()


def _serialise_in_memory(package: MappingPackageV3) -> InMemoryPath:
    """Serialise into an empty in-memory archive; this also rejects asset paths that would leave the package."""
    root = InMemoryPath.empty()
    MappingPackageV3Serialiser().serialise(cast(Path, root), package)  # InMemoryPath implements the Path API used
    return root


@traced_routine
def mapping_package_to_zip_bytes(package: MappingPackageV3, *, update_hash: bool = True) -> bytes:
    """Serialise a v3 package to the bytes of a package ZIP, without touching the disk.

    Args:
        package: The package to serialise.
        update_hash: If True, set ``package.metadata.mapping_suite_hash_digest`` to the hash computed by MSSDK
            **on the passed package** before writing, so the caller holds the hash that was written.

    Returns:
        The bytes of the ZIP, with the package files at the archive root.
    """
    if update_hash:
        _update_hash(package)
    return _serialise_in_memory(package).to_zip()


@traced_routine
def save_mapping_package_v3_to_folder(package: MappingPackageV3, path: Path, *, update_hash: bool = True) -> None:
    """Write a v3 package into the folder ``path`` (created if missing).

    Nothing is written if an asset path is unsafe (absolute, ``..``, backslash): the package is serialised in memory first.

    Args:
        package: The package to write.
        path: The destination folder.
        update_hash: If True, set the package hash on the passed package first (see ``mapping_package_to_zip_bytes``).
    """
    if update_hash:
        _update_hash(package)
    root = _serialise_in_memory(package)
    for name, content in root.files().items():
        target = path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


@traced_routine
def save_mapping_package_v3_to_archive(package: MappingPackageV3, path: Path, *, update_hash: bool = True) -> None:
    """Write a v3 package as a ZIP file at ``path``.

    Args:
        package: The package to write.
        path: The destination ZIP file.
        update_hash: If True, set the package hash on the passed package first (see ``mapping_package_to_zip_bytes``).
    """
    path.write_bytes(mapping_package_to_zip_bytes(package, update_hash=update_hash))
