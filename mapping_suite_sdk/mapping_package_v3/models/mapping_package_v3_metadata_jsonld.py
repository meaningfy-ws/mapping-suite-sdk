from mapping_suite_sdk.core.models.jsonld import JSONLDModel
from mapping_suite_sdk.core.models.mapping_package_metadata import MappingPackageMetadata
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_metadata import MappingPackageV3Metadata


class MappingPackageV3MetadataJSONLD(MappingPackageMetadata, MappingPackageV3Metadata, JSONLDModel):
    """
        This class represents an aggregation of domain model and technical data of Mapping Package V3.
        This model must be used as Mapping Package V3 Metadata.
    """
