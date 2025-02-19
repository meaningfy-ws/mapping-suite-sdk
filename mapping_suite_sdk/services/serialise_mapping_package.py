import tempfile
from pathlib import Path
from typing import Optional

from mapping_suite_sdk.adapters.serialiser import MappingPackageSerialiser
from mapping_suite_sdk.adapters.extractor import ArchiveExtractor
from mapping_suite_sdk.models.mapping_package import MappingPackage


def serialise_mapping_package(mapping_package: MappingPackage,
                              serialisation_folder_path: Path,
                              archive_unpacker: Optional[ArchiveExtractor] = None) -> None:
    """Serializes a MappingPackage object and packages it into an archive.

    This function takes a MappingPackage object, serializes its contents to a temporary
    directory, and then packages the serialized content into an archive at the specified
    destination path. The serialization process is handled by MappingPackageSerialiser,
    while the archiving is managed by an ArchiveUnpacker instance.

    Args:
        mapping_package (MappingPackage): The mapping package object to be serialized.
        serialisation_folder_path (Path): The destination path where the archived package
            will be stored.
        archive_unpacker (Optional[ArchiveUnpacker], optional): Custom archive unpacker
            instance. If not provided, a new ArchiveUnpacker instance will be created.

    Returns:
        None

    Side Effects:
        - Creates a temporary directory during execution (automatically cleaned up)
        - Writes serialized package data to the specified serialisation_folder_path

    Example:
        >>> from pathlib import Path
        >>> from mapping_suite_sdk.models.mapping_package import MappingPackage
        >>>
        >>> package = MappingPackage(...)  # Create your mapping package
        >>> output_path = Path("./output/package")
        >>> serialise_mapping_package(package, output_path)

    Notes:
        The function uses a temporary directory for intermediate storage of serialized
        content before packaging. This directory is automatically cleaned up after the
        function completes, regardless of success or failure.
    """
    archive_unpacker = archive_unpacker or ArchiveExtractor()

    with tempfile.TemporaryDirectory() as temp_directory:
        temp_directory_path = Path(temp_directory)

        MappingPackageSerialiser().serialize(temp_directory_path, mapping_package)

        archive_unpacker.pack_directory(temp_directory_path, serialisation_folder_path)
