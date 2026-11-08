import json

import pytest

from mapping_suite_sdk.core.adapters.optional_dependency import require


def test_require_returns_the_module_when_installed():
    assert require("json", "any", "JSON") is json


def test_require_names_feature_and_extra_when_missing():
    with pytest.raises(ImportError, match=r"^MongoDB support needs: pip install mapping-suite-sdk\[mongodb\]$") as err:
        require("no_such_module_mssdk", "mongodb", "MongoDB")
    assert isinstance(err.value.__cause__, ImportError)
