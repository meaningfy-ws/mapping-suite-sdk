from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3_lightweight import MappingPackageV3Lightweight

# Add id property to MappingPackageV3 if it doesn't exist
if not hasattr(MappingPackageV3, 'id'):
    def _id_property_v3(self) -> str:
        """Unique identifier for the mapping package, computed from nested metadata."""
        return self.metadata.id
    
    MappingPackageV3.id = property(_id_property_v3)

# Add id property to MappingPackageV3Lightweight if it doesn't exist
if not hasattr(MappingPackageV3Lightweight, 'id'):
    def _id_property_v3l(self) -> str:
        """Unique identifier for the mapping package, computed from nested metadata."""
        return self.metadata.id
    
    MappingPackageV3Lightweight.id = property(_id_property_v3l)

__all__ = ['MappingPackageV3', 'MappingPackageV3Lightweight']
