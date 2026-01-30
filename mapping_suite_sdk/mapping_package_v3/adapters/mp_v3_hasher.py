import json
from typing import Optional, List, Tuple, Protocol

from mapping_suite_sdk.core.adapters.hasher import (
    MappingPackageHasher, HasherABC, SHA256Hasher, normalize_content
)
from mapping_suite_sdk.core.models.pydantic import fields
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_lightweight import MappingPackageV3Lightweight
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_metadata import MappingPackageV3Metadata


def _hash_file_assets(file_assets: List, hasher: HasherABC) -> List[Tuple[str, str]]:
    """
    Hash a list of file assets and return sorted list of (path, hash) tuples.

    This helper function extracts the common pattern of hashing file assets
    to reduce code duplication in the hasher implementation.

    Args:
        file_assets: List of file assets with 'path' and 'content' attributes.
        hasher: The hasher implementation to use for generating hashes.

    Returns:
        List[Tuple[str, str]]: Sorted list of (file_path, hash) tuples.
    """
    file_hashes = []
    for asset in file_assets:
        normalized_content = normalize_content(asset.content)
        hashed_line = hasher.hash(normalized_content)
        file_hashes.append((str(asset.path), hashed_line))
    # Sort by file path for consistent ordering
    file_hashes.sort(key=lambda x: x[0])
    return file_hashes


class _V3HashableMetadata(Protocol):
    mapping_version: str
    mapping_suite_hash_digest: str

    def model_dump(self, *args, **kwargs): ...  # pragma: no cover


class V3HashableMappingPackage(Protocol):
    """
    Protocol for mapping packages that can be hashed with V3 hashing rules.

    Both full V3 packages and V3 lightweight packages expose the same essential
    attributes required for hash computation: metadata, technical mapping suite,
    and vocabulary mapping suite.
    """

    metadata: _V3HashableMetadata
    technical_mapping_suite: object
    vocabulary_mapping_suite: object


class MappingPackageV3Hasher(MappingPackageHasher):
    """
    Generates signature for an eforms-specific Mapping Package V3 or V3 Lightweight.

    This class provides functionality to hash a MappingPackageV3 or V3 Lightweight instance for unified mapping packages,
    including its files and metadata, to produce a unique signature.

    Args:
        mapping_package (MappingPackageV3 | MappingPackageV3Lightweight): The Mapping Package instance to hash.
        hasher (HasherABC): The hasher implementation to use for generating hashes.
    """

    def __init__(self, mapping_package: MappingPackageV3 | MappingPackageV3Lightweight, hasher: Optional[HasherABC] = None):
        self.mapping_package = mapping_package
        self.hasher = hasher or SHA256Hasher()

    def hash(self, with_version: Optional[str] = None) -> str:
        """
        Generate a comprehensive hash for an Mapping Package V3.

        This method creates a signature by:
        1. Collecting and hashing all critical files from the package
        2. Hashing metadata (specific to v3 packages)
        3. Combining these hashes with the version information

        Args:
            with_version (Optional[str], optional): Override the version used in the hash.
                If not provided, the package's mapping_version will be used.

        Returns:
            str: The final hash signature for the mapping package.
        """
        # Step 1: Hash all critical files
        # Combine all file assets from technical and vocabulary mapping suites
        all_file_assets = (
            list(self.mapping_package.technical_mapping_suite.files) +
            list(self.mapping_package.vocabulary_mapping_suite.files)
        )
        file_hashes = _hash_file_assets(all_file_assets, self.hasher)

        # Step 2: Collect all hash signatures
        signatures = [signature[1] for signature in file_hashes]

        # Step 3: Add metadata (only package specific metadata, without Linked Data part)
        only_metadata = MappingPackageV3Metadata.model_construct(**self.mapping_package.metadata.model_dump())

        model_str = only_metadata.model_dump_json(
            by_alias=True,
            exclude={fields(MappingPackageV3Metadata).mapping_suite_hash_digest}
        )
        metadata_hash = self.hasher.hash(json.dumps(model_str).encode('utf-8'))
        signatures.append(metadata_hash)

        # Step 4: Add version information
        version = with_version if with_version else self.mapping_package.metadata.mapping_version
        signatures.append(version)

        # Step 5: Generate final hash from all signatures
        return self.hasher.hash(str.encode(",".join(signatures)))
