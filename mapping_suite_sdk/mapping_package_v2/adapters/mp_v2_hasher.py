import json
from typing import Optional

from mapping_suite_sdk.core.adapters.hasher import MappingPackageHasher, HasherABC, SHA256Hasher
from mapping_suite_sdk.core.models.pydantic import fields
from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2 import MappingPackageV2
from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2_metadata import MappingPackageV2Metadata
from mapping_suite_sdk.utils import normalize_content


class MappingPackageV2Hasher(MappingPackageHasher):
    """
    Generates signature for an eforms-specific Mapping Package V2.

    This class provides functionality to hash a MappingPackageV1 instance for eforms,
    including its files and metadata, to produce a unique signature.

    Args:
        mapping_package (MappingPackageV1): The Mapping Package instance to hash.
        hasher (HasherABC): The hasher implementation to use for generating hashes.
    """

    def __init__(self, mapping_package: MappingPackageV2, hasher: Optional[HasherABC] = None):
        self.mapping_package = mapping_package
        self.hasher = hasher or SHA256Hasher()

    def hash(self, with_version: Optional[str] = None) -> str:
        """
        Generate a comprehensive hash for an eforms Mapping Package.

        This method creates a signature by:
        1. Collecting and hashing all critical files from the package
        2. Hashing metadata (specific to eforms packages)
        3. Combining these hashes with the version information

        Args:
            with_version (Optional[str], optional): Override the version used in the hash.
                If not provided, the package's mapping_version will be used.

        Returns:
            str: The final hash signature for the eforms mapping package.
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

        # Step 3: Add metadata hash (specific to eforms)
        model_dict = self.mapping_package.metadata.model_dump(
            by_alias=True,
            exclude={fields(MappingPackageV2Metadata).signature, fields(MappingPackageV2Metadata).path}
        )
        metadata_hash = self.hasher.hash(json.dumps(model_dict).encode('utf-8'))
        signatures.append(metadata_hash)

        # Step 4: Add version information
        version = with_version if with_version else self.mapping_package.metadata.mapping_version
        # TODO: This logic is taken from the previous implementations (SWS and MWB). But this behavior is different from
        #  signatures.append(version). In this case hashing is wrong
        signatures += version

        # Step 5: Generate final hash from all signatures
        return self.hasher.hash(str.encode(",".join(signatures)))
