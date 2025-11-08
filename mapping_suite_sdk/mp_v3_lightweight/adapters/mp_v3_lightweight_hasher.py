import json
from typing import Optional

from mapping_suite_sdk.core.adapters.hasher import MappingPackageHasher, HasherABC, SHA256Hasher, normalize_content
from mapping_suite_sdk.core.models.pydantic import fields
from mapping_suite_sdk.mp_v3_lightweight.models.mapping_package_v3_lightweight import MappingPackageV3Lightweight
from mapping_suite_sdk.mp_v3_lightweight.models.mapping_package_v3_lightweight_metadata import MappingPackageV3LightweightMetadata


class MappingPackageV3LightweightHasher(MappingPackageHasher):
    """
    Generates signature for an eforms-specific Mapping Package V3.

    This class provides functionality to hash a MappingPackageV3Lightweight instance for unified mapping packages,
    including its files and metadata, to produce a unique signature.

    Args:
        mapping_package (MappingPackageV3Lightweight): The Mapping Package instance to hash.
        hasher (HasherABC): The hasher implementation to use for generating hashes.
    """

    def __init__(self, mapping_package: MappingPackageV3Lightweight, hasher: Optional[HasherABC] = None):
        self.mapping_package = mapping_package
        self.hasher = hasher or SHA256Hasher()

    def hash(self, with_version: Optional[str] = None) -> str:
        """
        Generate a comprehensive hash for an Mapping Package V3 Lightweight.

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
        file_hashes = []

        # Hash technical mapping files
        for asset in self.mapping_package.technical_mapping_suite.files:
            normalized_content = normalize_content(asset.content)
            hashed_line = self.hasher.hash(normalized_content)
            file_hashes.append((str(asset.path), hashed_line))

        # Hash vocabulary mapping files
        for asset in self.mapping_package.vocabulary_mapping_suite.files:
            normalized_content = normalize_content(asset.content)
            hashed_line = self.hasher.hash(normalized_content)
            file_hashes.append((str(asset.path), hashed_line))

        # Sort by file path for consistent ordering
        file_hashes.sort(key=lambda x: x[0])

        # Step 2: Collect all hash signatures
        signatures = [signature[1] for signature in file_hashes]

        # Step 3: Add metadata (only package specific metadata, without Linked Data part
        only_metadata = MappingPackageV3LightweightMetadata.model_construct(**self.mapping_package.metadata.model_dump())

        model_str = only_metadata.model_dump_json(
            by_alias=True,
            exclude={fields(MappingPackageV3LightweightMetadata).mapping_suite_hash_digest}
        )
        metadata_hash = self.hasher.hash(json.dumps(model_str).encode('utf-8'))
        signatures.append(metadata_hash)

        # Step 4: Add version information
        version = with_version if with_version else self.mapping_package.metadata.mapping_version
        signatures.append(version)

        # Step 5: Generate final hash from all signatures
        return self.hasher.hash(str.encode(",".join(signatures)))
