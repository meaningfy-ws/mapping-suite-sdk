import sys

import mapping_suite_sdk


def test_module_imports():
    """Test that all modules imported in __init__.py can be imported correctly."""
    # Test that the module itself can be imported (already done by importing it above)
    assert "mapping_suite_sdk" in sys.modules

    # Test that each component mentioned in __all__ can be accessed
    for component in mapping_suite_sdk.__all__:
        # Verify the component is accessible as an attribute of the module
        assert hasattr(mapping_suite_sdk, component), f"Component {component} is in __all__ but not accessible"

        # Verify the component is not None
        assert getattr(mapping_suite_sdk, component) is not None, f"Component {component} is None"


def test_all_list_consistency():
    """Test that __all__ list is consistent with the actual exports."""
    # This test ensures that everything in __all__ is actually importable from the package
    for item in mapping_suite_sdk.__all__:
        # Should be able to import each item from mapping_suite_sdk
        imported_item = getattr(mapping_suite_sdk, item)
        assert imported_item is not None, f"Failed to import {item} from mapping_suite_sdk"
