import pytest

from mapping_suite_sdk.adapters.validator import MappingPackageValidator, MPStructuralValidationStep, \
    MPHashValidationStep, MPHashValidationException, MPStructuralValidationException
from mapping_suite_sdk.models.full_mapping_package import FullMappingPackage
from tests.conftest import _get_random_string


def test_mapping_package_validator_runs_with_success(dummy_mapping_package_model: FullMappingPackage):
    validator = MappingPackageValidator()
    is_valid: bool = validator.validate(dummy_mapping_package_model)
    assert is_valid


def test_mapping_package_validator_has_necessary_steps():
    validator = MappingPackageValidator()

    assert isinstance(validator.validation_chain, MPStructuralValidationStep)
    assert isinstance(validator.validation_chain.next_validator, MPHashValidationStep)


def test_mp_hash_validator_step_runs_with_success(dummy_mapping_package_model: FullMappingPackage):
    step = MPHashValidationStep()

    is_valid: bool = step.validate(dummy_mapping_package_model)

    assert is_valid


def test_mp_hash_validator_step_fails_on_different_hash(dummy_mapping_package_model: FullMappingPackage):
    random_string = _get_random_string()
    assert dummy_mapping_package_model.metadata.signature != random_string

    dummy_mapping_package_model.metadata.signature = random_string

    step = MPHashValidationStep()

    with pytest.raises(MPHashValidationException):
        step.validate(dummy_mapping_package_model)


def test_mp_structural_validator_step_runs_with_success(dummy_mapping_package_model: FullMappingPackage):
    step = MPStructuralValidationStep()

    is_valid: bool = step.validate(dummy_mapping_package_model)

    assert is_valid


def test_mp_structural_validator_step_fails_on_different_hash(dummy_mapping_package_model: FullMappingPackage):
    dummy_mapping_package_model.test_suites_shacl = []

    step = MPStructuralValidationStep()

    with pytest.raises(MPStructuralValidationException):
        step.validate(dummy_mapping_package_model)
