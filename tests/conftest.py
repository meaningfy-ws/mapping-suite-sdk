from pathlib import Path

import pytest

from tests import TEST_DATA_EXAMPLE_MAPPING_PACKAGE_PATH


@pytest.fixture
def dummy_mapping_package_path() -> Path:
    return TEST_DATA_EXAMPLE_MAPPING_PACKAGE_PATH