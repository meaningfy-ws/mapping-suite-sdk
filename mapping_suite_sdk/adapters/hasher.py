import hashlib
import json
import logging
import re
from typing import Tuple, List, Optional

from mapping_suite_sdk.models.asset import PackageAsset
from mapping_suite_sdk.models.core import fields
from mapping_suite_sdk.models.mapping_package import MappingPackage, MappingPackageMetadata

logger = logging.getLogger(__name__)


# TODO: This is a class from MWB and TED_SWS adopted for SDK Models. It must be improved then documented in future
class MappingPackageHasher:
    """
    Generates signature for a Mapping Package (used in metadata.json).

    Args:
        mapping_package (MappingPackage): The Mapping Package instance to hash.

    Methods:
        hash_mapping_package(with_version: Optional[str] = None) -> str:
            Generates a comprehensive hash for the entire Mapping Package, including files and metadata.
    """

    def __init__(self, mapping_package: MappingPackage):
        self.mapping_package = mapping_package

    def hash_a_file(self, package_asset: PackageAsset) -> Tuple[str, str]:
        # remove new-lines to align content generated on different operating systems
        new_line_pattern = re.compile(b'\r\n|\r|\n')
        if isinstance(package_asset.content, str):
            file_content = re.sub(new_line_pattern, b'', package_asset.content.encode('utf-8'))
        else:
            file_content = re.sub(new_line_pattern, b'', package_asset.content)
        hashed_line = hashlib.sha256(file_content).hexdigest()
        return str(package_asset.path), hashed_line

    def hash_critical_mapping_files(self) -> List[Tuple[str, str]]:
        files_to_hash: List[PackageAsset] = [
            *[asset for asset in self.mapping_package.technical_mapping_suite.files],
            *[asset for asset in self.mapping_package.vocabulary_mapping_suite.files],
        ]

        if self.mapping_package.metadata.type != "eforms": # TODO: Temporary solution. Depends on metadata model update
            files_to_hash.append(self.mapping_package.conceptual_mapping_asset)

        result = [self.hash_a_file(item) for item in files_to_hash]
        result.sort(key=lambda x: x[0])

        return result

    def hash_mapping_metadata(self) -> str:
        model_dict = self.mapping_package.metadata.model_dump(by_alias=True,
                                                              exclude={fields(MappingPackageMetadata).signature, fields(MappingPackageMetadata).path})

        return hashlib.sha256(
            json.dumps(model_dict).encode('utf-8')
        ).hexdigest()

    def hash_mapping_package(self, with_version: Optional[str] = None) -> str:
        list_of_hashes = self.hash_critical_mapping_files()
        signatures = [signature[1] for signature in list_of_hashes]
        signatures.append(self.hash_mapping_metadata())
        if with_version:
            signatures += with_version
        else:
            signatures += self.mapping_package.metadata.mapping_version
        return hashlib.sha256(str.encode(",".join(signatures))).hexdigest()
