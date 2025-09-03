from abc import ABC, abstractmethod
from types import FunctionType
from typing import final, Optional, NoReturn, Literal

from mapping_suite_sdk.adapters.hasher import MappingPackageHasher
from mapping_suite_sdk.adapters.tracer import traced_class
from mapping_suite_sdk.models.mapping_package import MappingPackage


class MPValidationException(Exception): pass


class MPStructuralValidationException(MPValidationException): pass


class MPHashValidationException(MPValidationException): pass


def validate_next(func: FunctionType):
    def wrapper(self, mapping_package: MappingPackage):
        result = func(self, mapping_package)
        if self.next_validator:
            return self.next_validator.validate(mapping_package)
        return result

    return wrapper


class MPValidationStepABC(ABC):
    """
    An abstract base class that defines the interface for a Mapping Package validation step.

    Attributes:
        next_validator (Optional[MPValidationStepABC]): The next validation step in the chain.

    Methods:
        validate(mapping_package: MappingPackage) -> Literal[True] | NoReturn:
            Validates the given Mapping Package. If the validation passes, it returns True. If the validation fails, it raises an exception.
    """

    def __init__(self, next_validator: Optional["MPValidationStepABC"] = None):
        self.next_validator = next_validator

    @abstractmethod
    @validate_next
    def validate(self, mapping_package: MappingPackage) -> Literal[True] | NoReturn:
        raise NotImplementedError


class MPStructuralValidationStep(MPValidationStepABC):
    """
    Validates the structural integrity of a Mapping Package, such as ensuring non-empty test suites.
    """

    @validate_next
    def validate(self, mapping_package: MappingPackage) -> Literal[True] | NoReturn:
        # Most of structural validation where done by model itself (using Pydantic)

        try:
            if mapping_package.test_data_suites:
                for suite in mapping_package.test_data_suites:
                    assert suite.files

            assert mapping_package.test_suites_shacl
            for suite in mapping_package.test_suites_shacl:
                assert suite.files

            assert mapping_package.test_suites_sparql
            for suite in mapping_package.test_suites_sparql:
                assert suite.files

            if mapping_package.test_results:
                for suite in mapping_package.test_results.result_suites:
                    assert suite.files

        #TODO: structural validation also must check relation between test data and results

        except AssertionError:
            raise MPStructuralValidationException("Mapping Package validation error:\nThere are empty suites")
        return True


class MPHashValidationStep(MPValidationStepABC):
    """
    Validates the hash-based signature of a Mapping Package to ensure its integrity.
    """

    @validate_next
    def validate(self, mapping_package: MappingPackage) -> Literal[True] | NoReturn:
        hasher = MappingPackageHasher(mapping_package=mapping_package)
        generated_hash: str = hasher.hash_mapping_package()

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
class MappingPackageValidator:
    """
    The main class that orchestrates the validation process by chaining the validation steps.

    Attributes:
        validation_chain (MPValidationStepABC): The chain of validation steps to be executed.

    Methods:
        validate(mapping_package: MappingPackage) -> Literal[True] | NoReturn:
            Executes the validation chain to validate the given Mapping Package.
    """

    def __init__(self, validation_chain: Optional[MPValidationStepABC] = None):
        self.validation_chain = validation_chain or MPStructuralValidationStep(MPHashValidationStep())

    def validate(self, mapping_package: MappingPackage) -> Literal[True] | NoReturn:
        return self.validation_chain.validate(mapping_package=mapping_package)
