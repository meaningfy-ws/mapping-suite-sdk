from mapping_suite_sdk.mapping_package_v1.models.mapping_package_v1 import MappingPackageV1

# Add id property if it doesn't exist (survives model regeneration)
if not hasattr(MappingPackageV1, 'id'):
    def _id_property(self) -> str:
        """Unique identifier for the mapping package, computed from nested metadata."""
        return self.metadata.identifier
    
    MappingPackageV1.id = property(_id_property)

__all__ = ['MappingPackageV1']
