import logging
from typing import final, Optional, NoReturn, Literal

from mapping_suite_sdk.core.adapters.hasher import HasherABC
from mapping_suite_sdk.core.adapters.tracer import traced_class
from mapping_suite_sdk.core.adapters.validator import MPValidationException, MPValidationStepABC, validate_next
from mapping_suite_sdk.mapping_package_v2.adapters.mp_v2_hasher import MappingPackageV2Hasher
from mapping_suite_sdk.mapping_package_v2.models.mapping_package_v2 import MappingPackageV2

logger = logging.getLogger(__name__)


class MPStructuralValidationException(MPValidationException): pass


class MPHashValidationException(MPValidationException): pass


class MPV2StructuralValidationStep(MPValidationStepABC):
    """
    Validates the structural integrity of a Mapping Package, such as ensuring non-empty test suites.
    """

    @validate_next
    def validate(self, mapping_package: MappingPackageV2) -> Literal[True] | NoReturn:
        # Most of structural validation where done by model itself (using Pydantic)

        try:
            if mapping_package.test_data_suites:
                for suite in mapping_package.test_data_suites:
                    assert suite.files

            assert mapping_package.test_suites_shacl
            for suite in mapping_package.test_suites_shacl.shacl_collections:
                assert suite.files

            assert mapping_package.test_suites_sparql
            for suite in mapping_package.test_suites_sparql:
                assert suite.files

            if mapping_package.test_results:
                # Outputs (test results) are not required for a package to be loadable.
                # Some production packages may contain unexpected/partial output structures.
                suites = getattr(mapping_package.test_results, "result_suites", None) or []
                for suite in suites:
                    if not getattr(suite, "files", None):
                        suite_path = getattr(suite, "path", "<unknown>")
                        logger.warning(
                            "Mapping Package structural warning: empty test result suite at %s",
                            suite_path,
                        )

        # TODO: structural validation also must check relation between test data and results

        except AssertionError:
            raise MPStructuralValidationException("Mapping Package validation error:\nThere are empty suites")
        return True


class MPV2HashValidationStep(MPValidationStepABC):
    """
    Validates the hash-based signature of a Mapping Package to ensure its integrity.
    """

    @validate_next
    def validate(self,
                 mapping_package: MappingPackageV2,
                 hasher: Optional[HasherABC] = None) -> Literal[True] | NoReturn:

        mp_hasher = MappingPackageV2Hasher(mapping_package=mapping_package, hasher=hasher)
        generated_hash: str = mp_hasher.hash()

        try:
            assert generated_hash == mapping_package.metadata.signature
        except AssertionError:
            raise MPHashValidationException(
                f"Mapping Package validation error: Package with identifier {mapping_package.metadata.identifier} has different signature:\n"
                f"Expected  signature for {mapping_package.metadata.identifier}: {mapping_package.metadata.signature}\n"
                f"Generated signature for {mapping_package.metadata.identifier}: {generated_hash}")

        return True


@final
@traced_class
class MappingPackageV2Validator:
    """
    The main class that orchestrates the validation process by chaining the validation steps.

    Attributes:
        validation_chain (MPValidationStepABC): The chain of validation steps to be executed.

    Methods:
        validate(mapping_package: MappingPackageV2) -> Literal[True] | NoReturn:
            Executes the validation chain to validate the given Mapping Package.
    """

    def __init__(self, validation_chain: Optional[MPValidationStepABC] = None):
        self.validation_chain = validation_chain or MPV2StructuralValidationStep(MPV2HashValidationStep())

    def validate(self, mapping_package: MappingPackageV2) -> Literal[True] | NoReturn:
        return self.validation_chain.validate(mapping_package=mapping_package)
