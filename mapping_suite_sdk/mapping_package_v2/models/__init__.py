from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2 import MappingPackageV2

# Add id property if it doesn't exist (survives model regeneration)
if not hasattr(MappingPackageV2, 'id'):
    def _id_property(self) -> str:
        """Unique identifier for the mapping package, computed from nested metadata."""
        return self.metadata.identifier
    
    MappingPackageV2.id = property(_id_property)

__all__ = ['MappingPackageV2']
