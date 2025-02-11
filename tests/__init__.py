from pathlib import Path

TESTS_PATH = Path(__file__).parent.resolve()

TEST_DATA_PATH = TESTS_PATH / "test_data"
TEST_DATA_MAPPING_PACKAGES_PATH = TEST_DATA_PATH / "mapping_packages"
TEST_DATA_EXAMPLE_MAPPING_PACKAGE_PATH = TEST_DATA_MAPPING_PACKAGES_PATH / "package_eforms_29_v1.9.zip"

UNIT_TESTS_PATH = TESTS_PATH / "unit"