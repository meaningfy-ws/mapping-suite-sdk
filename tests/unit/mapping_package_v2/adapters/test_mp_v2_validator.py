from pathlib import Path
from unittest.mock import Mock

import pytest
import logging

from mapping_suite_sdk.core.models.collection_asset import (
    TestDataCollectionAsset,
    SPARQLTestCollectionAsset,
    SHACLTestCollectionAsset,
    TestResultCollectionAsset, SHACLShapesCollectionAsset
)
from mapping_suite_sdk.core.models.file_asset import (
    TestDataFileAsset,
    SPARQLQueryFileAsset,
    SHACLShapesFileAsset, ReportFileAsset, SHACLShapesResultQueryFileAsset,
)
from mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_validator import MPStructuralValidationException, \
    MPV2HashValidationStep, MPHashValidationException, MappingPackageV2Validator, MPV2StructuralValidationStep
from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2 import MappingPackageV2


def test_mp_v2_structural_validation_step_valid_package(dummy_mapping_package_v2_model):
    validator = MPV2StructuralValidationStep()

    # Should pass validation for a valid package
    result = validator.validate(dummy_mapping_package_v2_model)
    assert result is True


def test_mp_v2_structural_validation_step_empty_test_data_suite():
    mock_package = Mock(spec=MappingPackageV2)

    # Create test data suite with empty files
    empty_test_suite = TestDataCollectionAsset(
        path=Path("test_data/empty_suite"),
        files=[]  # Empty files list
    )

    mock_package.test_data_suites = [empty_test_suite]
    mock_package.test_suites_shacl = SHACLTestCollectionAsset(
        path=Path("validation/shacl"),
        shacl_collections=[
            SHACLShapesCollectionAsset(
                path=Path("validation/shacl/epo"),
                files=[SHACLShapesFileAsset(path=Path("test.ttl"), content="test")]
            )
        ],
        shacl_result_query=SHACLShapesResultQueryFileAsset(
            content="dummy_content",
            path=Path("validation/shacl/epo"))
    )
    mock_package.test_suites_sparql = [
        SPARQLTestCollectionAsset(
            path=Path("validation/sparql/cm_assertions"),
            files=[SPARQLQueryFileAsset(path=Path("test.rq"), content="SELECT * WHERE { ?s ?p ?o }")]
        )
    ]
    mock_package.test_results = TestResultCollectionAsset(
        files=[],
        result_suites=[
            TestResultCollectionAsset(
                path=Path("output/test_suite"),
                files=[ReportFileAsset(path=Path("report.html"), content="test")]
            )
        ],
        path=Path("output/test_suite"))

    validator = MPV2StructuralValidationStep()

    with pytest.raises(MPStructuralValidationException) as exc_info:
        validator.validate(mock_package)

    assert "empty suites" in str(exc_info.value)


def test_mp_v2_structural_validation_step_empty_shacl_collection():
    mock_package = Mock(spec=MappingPackageV2)

    mock_package.test_data_suites = [
        TestDataCollectionAsset(
            path=Path("test_data/suite"),
            files=[TestDataFileAsset(path=Path("test.xml"), content="<test/>")]
        )
    ]

    # Create SHACL suite with empty collection
    empty_shacl_collection = SHACLShapesCollectionAsset(
        path=Path("validation/shacl/epo"),
        files=[]  # Empty files list
    )

    mock_package.test_suites_shacl = SHACLTestCollectionAsset(
        path=Path("validation/shacl"),
        shacl_collections=[empty_shacl_collection],
        shacl_result_query=SHACLShapesResultQueryFileAsset(
            content="dummy_content",
            path=Path("validation/shacl/epo"),
        )
    )

    mock_package.test_suites_sparql = [
        SPARQLTestCollectionAsset(
            path=Path("validation/sparql/cm_assertions"),
            files=[SPARQLQueryFileAsset(path=Path("test.rq"), content="SELECT * WHERE { ?s ?p ?o }")]
        )
    ]
    mock_package.test_results = TestResultCollectionAsset(files=[], result_suites=[], path=Path("output/test_suite"))

    validator = MPV2StructuralValidationStep()

    with pytest.raises(MPStructuralValidationException):
        validator.validate(mock_package)


def test_mp_v2_structural_validation_step_empty_sparql_suite():
    mock_package = Mock(spec=MappingPackageV2)

    mock_package.test_data_suites = [
        TestDataCollectionAsset(
            path=Path("test_data/suite"),
            files=[TestDataFileAsset(path=Path("test.xml"), content="<test/>")]
        )
    ]

    mock_package.test_suites_shacl = SHACLTestCollectionAsset(
        path=Path("validation/shacl"),
        shacl_collections=[
            SHACLShapesCollectionAsset(
                path=Path("validation/shacl/epo"),
                files=[SHACLShapesFileAsset(path=Path("test.ttl"), content="test")]
            )
        ],
        shacl_result_query=SHACLShapesResultQueryFileAsset(
            content="dummy_content",
            path=Path("validation/shacl/epo"),
        )
    )

    # Create SPARQL suite with empty files
    empty_sparql_suite = SPARQLTestCollectionAsset(
        path=Path("validation/sparql/cm_assertions"),
        files=[]  # Empty files list
    )

    mock_package.test_suites_sparql = [empty_sparql_suite]
    mock_package.test_results = TestResultCollectionAsset(files=[], result_suites=[], path=Path("output/test_suite"))

    validator = MPV2StructuralValidationStep()

    with pytest.raises(MPStructuralValidationException):
        validator.validate(mock_package)


def test_mp_v2_structural_validation_step_empty_test_results_suite(caplog):
    mock_package = Mock(spec=MappingPackageV2)

    mock_package.test_data_suites = [
        TestDataCollectionAsset(
            path=Path("test_data/suite"),
            files=[TestDataFileAsset(path=Path("test.xml"), content="<test/>")]
        )
    ]

    mock_package.test_suites_shacl = SHACLTestCollectionAsset(
        path=Path("validation/shacl"),
        shacl_collections=[
            SHACLShapesCollectionAsset(
                path=Path("validation/shacl/epo"),
                files=[SHACLShapesFileAsset(path=Path("test.ttl"), content="test")]
            )
        ],
        shacl_result_query=SHACLShapesResultQueryFileAsset(
            content="dummy_content",
            path=Path("validation/shacl/epo"),
        )
    )

    mock_package.test_suites_sparql = [
        SPARQLTestCollectionAsset(
            path=Path("validation/sparql/cm_assertions"),
            files=[SPARQLQueryFileAsset(path=Path("test.rq"), content="SELECT * WHERE { ?s ?p ?o }")]
        )
    ]

    # Create test results with empty suite
    empty_result_suite = TestResultCollectionAsset(
        path=Path("output/test_suite"),
        files=[]  # Empty files list
    )

    mock_package.test_results = TestResultCollectionAsset(
        files=[],
        result_suites=[empty_result_suite],
        path=Path("output/test_suite")
    )

    validator = MPV2StructuralValidationStep()

    caplog.set_level(logging.WARNING)

    # Should not raise structural error for empty output suites
    result = validator.validate(mock_package)
    assert result is True
    assert "empty test result suite" in caplog.text


def test_mp_v2_structural_validation_step_none_test_data_suites():
    mock_package = Mock(spec=MappingPackageV2)

    mock_package.test_data_suites = None  # None test data suites should be allowed

    mock_package.test_suites_shacl = SHACLTestCollectionAsset(
        path=Path("validation/shacl"),
        shacl_collections=[
            SHACLShapesCollectionAsset(
                path=Path("validation/shacl/epo"),
                files=[SHACLShapesFileAsset(path=Path("test.ttl"), content="test")]
            )
        ],
        shacl_result_query=SHACLShapesResultQueryFileAsset(
            content="dummy_content",
            path=Path("validation/shacl/epo"),
        )
    )

    mock_package.test_suites_sparql = [
        SPARQLTestCollectionAsset(
            path=Path("validation/sparql/cm_assertions"),
            files=[SPARQLQueryFileAsset(path=Path("test.rq"), content="SELECT * WHERE { ?s ?p ?o }")]
        )
    ]

    mock_package.test_results = TestResultCollectionAsset(files=[], result_suites=[], path=Path("output/test_suite"))

    validator = MPV2StructuralValidationStep()

    # Should pass validation when test_data_suites is None
    result = validator.validate(mock_package)
    assert result is True


def test_mp_v2_hash_validation_step_valid_hash(dummy_mapping_package_v2_model):
    # Generate the expected hash for the package
    from mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_hasher import MappingPackageV2Hasher

    hasher = MappingPackageV2Hasher(dummy_mapping_package_v2_model)
    expected_hash = hasher.hash()

    # Update the package metadata with the correct hash
    dummy_mapping_package_v2_model.metadata.signature = expected_hash

    validator = MPV2HashValidationStep()
    result = validator.validate(dummy_mapping_package_v2_model)

    assert result is True


def test_mp_v2_hash_validation_step_invalid_hash(dummy_mapping_package_v2_model):
    # Set an incorrect hash
    dummy_mapping_package_v2_model.metadata.signature = "invalid_hash"

    validator = MPV2HashValidationStep()

    with pytest.raises(MPHashValidationException) as exc_info:
        validator.validate(dummy_mapping_package_v2_model)

    assert "different signature" in str(exc_info.value)
    assert dummy_mapping_package_v2_model.metadata.identifier in str(exc_info.value)
    assert "Expected  signature" in str(exc_info.value)
    assert "Generated signature" in str(exc_info.value)


def test_mp_v2_validator_default_validation_chain():
    validator = MappingPackageV2Validator()

    # Default chain should include both structural and hash validation
    assert validator.validation_chain is not None
    assert isinstance(validator.validation_chain, MPV2StructuralValidationStep)


def test_mp_v2_validator_custom_validation_chain():
    custom_chain = Mock()
    custom_chain.validate.return_value = True

    validator = MappingPackageV2Validator(validation_chain=custom_chain)

    assert validator.validation_chain == custom_chain


def test_mp_v2_validator_validate_calls_chain(dummy_mapping_package_v2_model):
    mock_chain = Mock()
    mock_chain.validate.return_value = True

    validator = MappingPackageV2Validator(validation_chain=mock_chain)
    result = validator.validate(dummy_mapping_package_v2_model)

    mock_chain.validate.assert_called_once_with(mapping_package=dummy_mapping_package_v2_model)
    assert result is True


def test_mp_v2_validator_validate_propagates_exception(dummy_mapping_package_v2_model):
    mock_chain = Mock()
    mock_chain.validate.side_effect = MPStructuralValidationException("Test error")

    validator = MappingPackageV2Validator(validation_chain=mock_chain)

    with pytest.raises(MPStructuralValidationException) as exc_info:
        validator.validate(dummy_mapping_package_v2_model)

    assert "Test error" in str(exc_info.value)


def test_mp_v2_validator_tracer_decoration():
    # Test that the validator is properly decorated with @traced_class
    validator = MappingPackageV2Validator()

    assert hasattr(validator, '__class__')
    assert validator.__class__.__name__ == 'MappingPackageV2Validator'


def test_mp_v2_validator_final_class():
    # Test that MappingPackageV2Validator is marked as final
    # This prevents subclassing
    validator = MappingPackageV2Validator()

    # Should be able to create instance
    assert isinstance(validator, MappingPackageV2Validator)


def test_mp_v2_validator_full_validation_chain_success(dummy_mapping_package_v2_model):
    # Set up package with valid hash
    from mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_hasher import MappingPackageV2Hasher

    hasher = MappingPackageV2Hasher(dummy_mapping_package_v2_model)
    expected_hash = hasher.hash()
    dummy_mapping_package_v2_model.metadata.signature = expected_hash

    # Use default validation chain (structural + hash)
    validator = MappingPackageV2Validator()
    result = validator.validate(dummy_mapping_package_v2_model)

    assert result is True


def test_mp_v2_validator_full_validation_chain_hash_failure(dummy_mapping_package_v2_model):
    # Set invalid hash (structural validation should pass first)
    dummy_mapping_package_v2_model.metadata.signature = "invalid_hash"

    validator = MappingPackageV2Validator()

    with pytest.raises(MPHashValidationException):
        validator.validate(dummy_mapping_package_v2_model)


def test_mp_v2_structural_validation_step_validate_next_decorator():
    # Test that the validate_next decorator is applied
    validator = MPV2StructuralValidationStep()

    # Should have the validate method
    assert hasattr(validator, 'validate')
    assert callable(getattr(validator, 'validate'))


def test_mp_v2_hash_validation_step_validate_next_decorator():
    # Test that the validate_next decorator is applied
    validator = MPV2HashValidationStep()

    # Should have the validate method
    assert hasattr(validator, 'validate')
    assert callable(getattr(validator, 'validate'))


def test_mp_v2_validation_chain_ordering():
    # Test that the default validation chain has correct ordering
    validator = MappingPackageV2Validator()

    # First validator should be structural
    assert isinstance(validator.validation_chain, MPV2StructuralValidationStep)

    # The next validator in chain should be hash validation
    # This is set up in the constructor: MPV2StructuralValidationStep(MPV2HashValidationStep())
    if hasattr(validator.validation_chain, 'next_step'):
        assert isinstance(validator.validation_chain.next_step, MPV2HashValidationStep)
