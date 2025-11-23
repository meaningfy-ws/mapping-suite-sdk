from pathlib import Path

from mapping_suite_sdk.core.adapters.serialiser import MappingPackageAssetSerialiser, \
    TechnicalMappingCollectionAssetSerialiser, VocabularyMappingCollectionAssetSerialiser
from mapping_suite_sdk.core.adapters.tracer import traced_class
from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_metadata_serialiser import MappingPackageV3MetadataSerialiser
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_lightweight import MappingPackageV3Lightweight


@traced_class
class MappingPackageV3LightweightSerialiser(MappingPackageAssetSerialiser):
    """Main serialiser for complete mapping packages."""

    def serialise(self, package_folder_path: Path, asset: MappingPackageV3Lightweight) -> None:
        """Serialize all components of a mapping package.

        This method orchestrates the serialization of:
        - Package metadata
        - Technical mapping suite
        - Vocabulary mapping suite

        Args:
            package_folder_path (Path): Path to the mapping package folder.
            asset (MappingPackageABC): Complete mapping package to serialize.
        """

        # Serialize each component
        MappingPackageV3MetadataSerialiser().serialise(package_folder_path, asset.metadata)
        TechnicalMappingCollectionAssetSerialiser().serialise(package_folder_path, asset.technical_mapping_suite)
        VocabularyMappingCollectionAssetSerialiser().serialise(package_folder_path, asset.vocabulary_mapping_suite)
