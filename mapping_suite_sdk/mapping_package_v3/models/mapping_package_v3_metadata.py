from mapping_suite_sdk.core.models.jsonld import JSONLDModel
from mapping_suite_sdk.core.models.mapping_package_metadata import MappingPackageMetadata
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_linkml_metadata import \
    MappingPackageV3LinkMLMetadata


class MappingPackageV3Metadata(MappingPackageMetadata, MappingPackageV3LinkMLMetadata, JSONLDModel):
    """

    """
