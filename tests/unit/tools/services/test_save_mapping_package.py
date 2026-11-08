"""mongodb-persistence: save a loaded package to MongoDB."""

from pathlib import Path
from unittest.mock import MagicMock, Mock

import mongomock
import pytest
from bson import json_util

from mapping_suite_sdk.tools.services.convert_mapping_package import UnsupportedConversionError
from mapping_suite_sdk.tools.services.load_mapping_package import load_mapping_package
from mapping_suite_sdk.tools.services.save_mapping_package import save_mapping_package_to_mongodb
from tests import TEST_DATA_EXAMPLE_V3_MAPPING_PACKAGE_FOLDER_PATH, TEST_DATA_EXAMPLE_V3L_MAPPING_PACKAGE_FOLDER_PATH

GOLDEN = Path(__file__).parents[3] / "test_data" / "mongodb_golden"


@pytest.mark.parametrize(
    "golden, folder, include_test_data",
    [
        ("v3", TEST_DATA_EXAMPLE_V3_MAPPING_PACKAGE_FOLDER_PATH, True),
        ("v3L", TEST_DATA_EXAMPLE_V3L_MAPPING_PACKAGE_FOLDER_PATH, False),
    ],
)
def test_same_document_as_1x(golden, folder, include_test_data):
    client = mongomock.MongoClient()
    package = load_mapping_package(folder, include_test_data=include_test_data)

    save_mapping_package_to_mongodb(package, client, "golden")

    stored = list(client["golden"]["mapping_package"].find())
    assert stored == [json_util.loads((GOLDEN / f"{golden}.json").read_text())]


def test_saving_twice_updates_in_place():
    client = mongomock.MongoClient()
    package = load_mapping_package(TEST_DATA_EXAMPLE_V3L_MAPPING_PACKAGE_FOLDER_PATH)

    save_mapping_package_to_mongodb(package, client, "db", "coll")
    save_mapping_package_to_mongodb(package, client, "db", "coll")

    assert client["db"]["coll"].count_documents({}) == 1


def test_unsupported_package_type_raises():
    with pytest.raises(UnsupportedConversionError, match="unsupported package type"):
        save_mapping_package_to_mongodb(Mock(), MagicMock(), "db")
