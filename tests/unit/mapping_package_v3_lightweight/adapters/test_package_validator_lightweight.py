from unittest.mock import Mock

import pytest

from mapping_suite_sdk.mp_v3_lightweight.adapters.mp_v3_lightweight_hasher import MappingPackageV3LightweightHasher
from mapping_suite_sdk.mp_v3_lightweight.adapters.validator_lightweight import MappingPackageV3LightweightValidator, \
    MPV3LightweightHashValidationException, MPV3LightweightStructuralValidationException
from mapping_suite_sdk.mp_v3_lightweight.models.mapping_package_v3_lightweight import MappingPackageV3Lightweight


def test_mp_v3_validator_full_validation_chain_success(fixture_mapping_package_v3_model: MappingPackageV3Lightweight) -> None:
    hasher = MappingPackageV3LightweightHasher(fixture_mapping_package_v3_model)
    expected_hash = hasher.hash()
    fixture_mapping_package_v3_model.metadata.mapping_suite_hash_digest = expected_hash

    validator = MappingPackageV3LightweightValidator()
    result = validator.validate(fixture_mapping_package_v3_model)

    assert result is True


def test_mp_v3_validator_full_validation_chain_hash_failure(fixture_mapping_package_v3_model: MappingPackageV3Lightweight) -> None:
    fixture_mapping_package_v3_model.metadata.mapping_suite_hash_digest = "invalid_hash"

    validator = MappingPackageV3LightweightValidator()

    with pytest.raises(MPV3LightweightHashValidationException):
        validator.validate(fixture_mapping_package_v3_model)


def test_mp_v3_validator_validate_propagates_exception(fixture_mapping_package_v3_model: MappingPackageV3Lightweight) -> None:
    mock_chain = Mock()
    mock_chain.validate.side_effect = MPV3LightweightStructuralValidationException("Test error")

    validator = MappingPackageV3LightweightValidator(validation_chain=mock_chain)

    with pytest.raises(MPV3LightweightStructuralValidationException) as exc_info:
        validator.validate(fixture_mapping_package_v3_model)

    assert "Test error" in str(exc_info.value)
