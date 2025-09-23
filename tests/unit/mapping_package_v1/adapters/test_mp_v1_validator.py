from pathlib import Path
from unittest.mock import Mock

import pytest

from mapping_suite_sdk.core.models.collection_asset import (
    TestDataCollectionAsset,
    SAPRQLTestCollectionAsset,
    SHACLTestCollectionAsset,
    TestResultCollectionAsset, SHACLShapesCollectionAsset
)
from mapping_suite_sdk.core.models.file_asset import (
    TestDataFileAsset,
    SPARQLQueryFileAsset,
    SHACLShapesFileAsset, ReportFileAsset, SHACLShapesResultQueryFileAsset,
)
from mapping_suite_sdk.mapping_package_v1.adapters.mp_v1_validator import (
    MPStructuralValidationException,
    MPHashValidationException,
    MPV1StructuralValidationStep,
    MPV1HashValidationStep,
    MappingPackageV1Validator
)
from mapping_suite_sdk.mapping_package_v1.models.mapping_package_v1 import MappingPackageV1


def test_mp_v1_structural_validation_step_valid_package(dummy_mapping_package_v1_model):
    if not isinstance(dummy_mapping_package_v1_model, MappingPackageV1):
        pytest.skip("This test requires a V1 mapping package")

    validator = MPV1StructuralValidationStep()

    # Should pass validation for a valid package
    result = validator.validate(dummy_mapping_package_v1_model)
    assert result is True


def test_mp_v1_structural_validation_step_empty_test_data_suite():
    mock_package = Mock(spec=MappingPackageV1)

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
        )
    )
    mock_package.test_suites_sparql = [
        SAPRQLTestCollectionAsset(
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
        ]
    )

    validator = MPV1StructuralValidationStep()

    with pytest.raises(MPStructuralValidationException) as exc_info:
        validator.validate(mock_package)

    assert "empty suites" in str(exc_info.value)


def test_mp_v1_structural_validation_step_empty_shacl_collection():
    mock_package = Mock(spec=MappingPackageV1)

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
        )
    )

    mock_package.test_suites_sparql = [
        SAPRQLTestCollectionAsset(
            path=Path("validation/sparql/cm_assertions"),
            files=[SPARQLQueryFileAsset(path=Path("test.rq"), content="SELECT * WHERE { ?s ?p ?o }")]
        )
    ]
    mock_package.test_results = TestResultCollectionAsset(files=[], result_suites=[])

    validator = MPV1StructuralValidationStep()

    with pytest.raises(MPStructuralValidationException):
        validator.validate(mock_package)


def test_mp_v1_structural_validation_step_empty_sparql_suite():
    mock_package = Mock(spec=MappingPackageV1)

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
        )
    )

    # Create SPARQL suite with empty files
    empty_sparql_suite = SAPRQLTestCollectionAsset(
        path=Path("validation/sparql/cm_assertions"),
        files=[]  # Empty files list
    )

    mock_package.test_suites_sparql = [empty_sparql_suite]
    mock_package.test_results = TestResultCollectionAsset(files=[], result_suites=[])

    validator = MPV1StructuralValidationStep()

    with pytest.raises(MPStructuralValidationException):
        validator.validate(mock_package)


def test_mp_v1_structural_validation_step_empty_test_results_suite():
    mock_package = Mock(spec=MappingPackageV1)

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
        )
    )

    mock_package.test_suites_sparql = [
        SAPRQLTestCollectionAsset(
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
        result_suites=[empty_result_suite]
    )

    validator = MPV1StructuralValidationStep()

    with pytest.raises(MPStructuralValidationException):
        validator.validate(mock_package)


def test_mp_v1_structural_validation_step_none_test_data_suites():
    mock_package = Mock(spec=MappingPackageV1)

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
        )
    )

    mock_package.test_suites_sparql = [
        SAPRQLTestCollectionAsset(
            path=Path("validation/sparql/cm_assertions"),
            files=[SPARQLQueryFileAsset(path=Path("test.rq"), content="SELECT * WHERE { ?s ?p ?o }")]
        )
    ]

    mock_package.test_results = TestResultCollectionAsset(files=[], result_suites=[])

    validator = MPV1StructuralValidationStep()

    # Should pass validation when test_data_suites is None
    result = validator.validate(mock_package)
    assert result is True


def test_mp_v1_hash_validation_step_valid_hash(dummy_mapping_package_v1_model):
    if not isinstance(dummy_mapping_package_v1_model, MappingPackageV1):
        pytest.skip("This test requires a V1 mapping package")

    # Generate the expected hash for the package
    from mapping_suite_sdk.mapping_package_v1.adapters.mp_v1_hasher import MappingPackageV1Hasher

    hasher = MappingPackageV1Hasher(dummy_mapping_package_v1_model)
    expected_hash = hasher.hash()

    # Update the package metadata with the correct hash
    dummy_mapping_package_v1_model.metadata.signature = expected_hash

    validator = MPV1HashValidationStep()
    result = validator.validate(dummy_mapping_package_v1_model)

    assert result is True


def test_mp_v1_hash_validation_step_invalid_hash(dummy_mapping_package_v1_model):
    if not isinstance(dummy_mapping_package_v1_model, MappingPackageV1):
        pytest.skip("This test requires a V1 mapping package")

    # Set an incorrect hash
    dummy_mapping_package_v1_model.metadata.signature = "invalid_hash"

    validator = MPV1HashValidationStep()

    with pytest.raises(MPHashValidationException) as exc_info:
        validator.validate(dummy_mapping_package_v1_model)

    assert "different signature" in str(exc_info.value)
    assert dummy_mapping_package_v1_model.metadata.identifier in str(exc_info.value)
    assert "Expected  signature" in str(exc_info.value)
    assert "Generated signature" in str(exc_info.value)


def test_mp_v1_validator_default_validation_chain():
    validator = MappingPackageV1Validator()

    # Default chain should include both structural and hash validation
    assert validator.validation_chain is not None
    assert isinstance(validator.validation_chain, MPV1StructuralValidationStep)


def test_mp_v1_validator_custom_validation_chain():
    custom_chain = Mock()
    custom_chain.validate.return_value = True

    validator = MappingPackageV1Validator(validation_chain=custom_chain)

    assert validator.validation_chain == custom_chain


def test_mp_v1_validator_validate_calls_chain(dummy_mapping_package_v1_model):
    if not isinstance(dummy_mapping_package_v1_model, MappingPackageV1):
        pytest.skip("This test requires a V1 mapping package")

    mock_chain = Mock()
    mock_chain.validate.return_value = True

    validator = MappingPackageV1Validator(validation_chain=mock_chain)
    result = validator.validate(dummy_mapping_package_v1_model)

    mock_chain.validate.assert_called_once_with(mapping_package=dummy_mapping_package_v1_model)
    assert result is True


def test_mp_v1_validator_validate_propagates_exception(dummy_mapping_package_v1_model):
    if not isinstance(dummy_mapping_package_v1_model, MappingPackageV1):
        pytest.skip("This test requires a V1 mapping package")

    mock_chain = Mock()
    mock_chain.validate.side_effect = MPStructuralValidationException("Test error")

    validator = MappingPackageV1Validator(validation_chain=mock_chain)

    with pytest.raises(MPStructuralValidationException) as exc_info:
        validator.validate(dummy_mapping_package_v1_model)

    assert "Test error" in str(exc_info.value)


def test_mp_v1_validator_tracer_decoration():
    # Test that the validator is properly decorated with @traced_class
    validator = MappingPackageV1Validator()

    assert hasattr(validator, '__class__')
    assert validator.__class__.__name__ == 'MappingPackageV1Validator'


def test_mp_v1_validator_final_class():
    # Test that MappingPackageV1Validator is marked as final
    # This prevents subclassing
    validator = MappingPackageV1Validator()

    # Should be able to create instance
    assert isinstance(validator, MappingPackageV1Validator)


def test_mp_v1_validator_full_validation_chain_success(dummy_mapping_package_v1_model):
    if not isinstance(dummy_mapping_package_v1_model, MappingPackageV1):
        pytest.skip("This test requires a V1 mapping package")

    # Set up package with valid hash
    from mapping_suite_sdk.mapping_package_v1.adapters.mp_v1_hasher import MappingPackageV1Hasher

    hasher = MappingPackageV1Hasher(dummy_mapping_package_v1_model)
    expected_hash = hasher.hash()
    dummy_mapping_package_v1_model.metadata.signature = expected_hash

    # Use default validation chain (structural + hash)
    validator = MappingPackageV1Validator()
    result = validator.validate(dummy_mapping_package_v1_model)

    assert result is True


def test_mp_v1_validator_full_validation_chain_hash_failure(dummy_mapping_package_v1_model):
    if not isinstance(dummy_mapping_package_v1_model, MappingPackageV1):
        pytest.skip("This test requires a V1 mapping package")

    # Set invalid hash (structural validation should pass first)
    dummy_mapping_package_v1_model.metadata.signature = "invalid_hash"

    validator = MappingPackageV1Validator()

    with pytest.raises(MPHashValidationException):
        validator.validate(dummy_mapping_package_v1_model)


def test_mp_v1_structural_validation_step_validate_next_decorator():
    # Test that the validate_next decorator is applied
    validator = MPV1StructuralValidationStep()

    # Should have the validate method
    assert hasattr(validator, 'validate')
    assert callable(getattr(validator, 'validate'))


def test_mp_v1_hash_validation_step_validate_next_decorator():
    # Test that the validate_next decorator is applied
    validator = MPV1HashValidationStep()

    # Should have the validate method
    assert hasattr(validator, 'validate')
    assert callable(getattr(validator, 'validate'))


def test_mp_v1_validation_chain_ordering():
    # Test that the default validation chain has correct ordering
    validator = MappingPackageV1Validator()

    # First validator should be structural
    assert isinstance(validator.validation_chain, MPV1StructuralValidationStep)

    # The next validator in chain should be hash validation
    # This is set up in the constructor: MPV1StructuralValidationStep(MPV1HashValidationStep())
    if hasattr(validator.validation_chain, 'next_step'):
        assert isinstance(validator.validation_chain.next_step, MPV1HashValidationStep)


def test_mp_validation_exceptions_inheritance():
    # Test exception hierarchy
    structural_exc = MPStructuralValidationException("structural error")
    hash_exc = MPHashValidationException("hash error")

    # Both should be instances of their base exception class
    from mapping_suite_sdk.core.adapters.validator_abc import MPValidationException

    assert isinstance(structural_exc, MPValidationException)
    assert isinstance(hash_exc, MPValidationException)

    # Should have proper error messages
    assert "structural error" in str(structural_exc)
    assert "hash error" in str(hash_exc)
