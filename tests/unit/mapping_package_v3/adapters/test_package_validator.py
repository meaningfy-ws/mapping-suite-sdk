from unittest.mock import Mock

import pytest

from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_hasher import MappingPackageV3Hasher
from mapping_suite_sdk.mapping_package_v3.adapters.mp_v3_validator import MappingPackageV3Validator, \
    MPV3HashValidationException, MPV3StructuralValidationException
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3


def test_mp_v3_validator_full_validation_chain_success(fixture_mapping_package_v3_model: MappingPackageV3) -> None:
    hasher = MappingPackageV3Hasher(fixture_mapping_package_v3_model)
    expected_hash = hasher.hash()
    fixture_mapping_package_v3_model.metadata.mapping_suite_hash_digest = expected_hash

    validator = MappingPackageV3Validator()
    result = validator.validate(fixture_mapping_package_v3_model)

    assert result is True


def test_mp_v3_validator_full_validation_chain_hash_failure(fixture_mapping_package_v3_model: MappingPackageV3) -> None:
    fixture_mapping_package_v3_model.metadata.mapping_suite_hash_digest = "invalid_hash"

    validator = MappingPackageV3Validator()

    with pytest.raises(MPV3HashValidationException):
        validator.validate(fixture_mapping_package_v3_model)


def test_mp_v3_validator_validate_propagates_exception(fixture_mapping_package_v3_model: MappingPackageV3) -> None:
    mock_chain = Mock()
    mock_chain.validate.side_effect = MPV3StructuralValidationException("Test error")

    validator = MappingPackageV3Validator(validation_chain=mock_chain)

    with pytest.raises(MPV3StructuralValidationException) as exc_info:
        validator.validate(fixture_mapping_package_v3_model)

    assert "Test error" in str(exc_info.value)
