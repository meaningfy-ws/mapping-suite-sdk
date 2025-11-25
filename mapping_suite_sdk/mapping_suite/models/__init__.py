# Patch: Add id property to MappingSuite after model generation
# This property is computed from nested metadata and is needed for MongoDB operations
# This survives model regeneration because __init__.py is not generated
from mapping_suite_sdk.mapping_suite.models.mapping_suite import MappingSuite

# Add id property if it doesn't exist (survives model regeneration)
if not hasattr(MappingSuite, 'id'):
    def _id_property(self) -> str:
        """Unique identifier for the mapping suite, computed from nested metadata."""
        return self.mapping_suite_config.mapping_suite_metadata.mapping_suite_identifier
    
    MappingSuite.id = property(_id_property)

__all__ = ['MappingSuite']
