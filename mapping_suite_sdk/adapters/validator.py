from abc import ABC, abstractmethod
from types import FunctionType
from typing import final, Optional, NoReturn, Literal

from mapping_suite_sdk.adapters.hasher import MappingPackageHasher
from mapping_suite_sdk.adapters.tracer import traced_class
from mapping_suite_sdk.models.mapping_package import MappingPackage


class MPStructuralValidationException(Exception): pass


class MPHashValidationException(Exception): pass


def validate_next(func: FunctionType):
    def wrapper(self, mapping_package: MappingPackage):
        result = func(self, mapping_package)
        if self.next_validator:
            return self.next_validator.validate(mapping_package)
        return result

    return wrapper


class MPValidationStepABC(ABC):
    def __init__(self, next_validator: Optional["MPValidationStepABC"] = None):
        self.next_validator = next_validator

    @abstractmethod
    @validate_next
    def validate(self, mapping_package: MappingPackage) -> Literal[True] | NoReturn:
        raise NotImplementedError


class MPStructuralValidationStep(MPValidationStepABC):

    @validate_next
    def validate(self, mapping_package: MappingPackage) -> Literal[True] | NoReturn:
        # Most of structural validation where done by model itself (using Pydantic)

        try:
            assert mapping_package.test_data_suites
            for suite in mapping_package.test_data_suites:
                assert suite.files

            assert mapping_package.test_suites_shacl
            for suite in mapping_package.test_suites_shacl:
                assert suite.files

            assert mapping_package.test_suites_sparql
            for suite in mapping_package.test_suites_sparql:
                assert suite.files

        except AssertionError:
            raise MPStructuralValidationException("nMapping Package validation error:\nThere are empty suites")
        return True


class MPHashValidationStep(MPValidationStepABC):

    @validate_next
    def validate(self, mapping_package: MappingPackage) -> Literal[True] | NoReturn:
        hasher = MappingPackageHasher(mapping_package=mapping_package)
        generated_hash: str = hasher.hash_mapping_package()

        try:
            assert generated_hash == mapping_package.metadata.signature
        except AssertionError:
            raise MPHashValidationException("\nMapping Package validation error: different signature:\n"
                                            f"Expected signature: {mapping_package.metadata.signature}\n"
                                            f"Generated signature: {generated_hash}")

        return True


@final
@traced_class
class MappingPackageValidator:

    def __init__(self, validation_chain: Optional[MPValidationStepABC] = None):
        self.validation_chain = validation_chain or MPStructuralValidationStep(MPHashValidationStep())

    def validate(self, mapping_package: MappingPackage) -> Literal[True] | NoReturn:
        return self.validation_chain.validate(mapping_package=mapping_package)
