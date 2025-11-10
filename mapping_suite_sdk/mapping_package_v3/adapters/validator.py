from typing import final, Optional, NoReturn, Literal

from mapping_suite_sdk.core.adapters.hasher import HasherABC
from mapping_suite_sdk.core.adapters.tracer import traced_class
from mapping_suite_sdk.core.adapters.validator_abc import MPValidationException, MPValidationStepABC, validate_next
from mapping_suite_sdk.mapping_package_v3.adapters.hasher import MappingPackageV3Hasher
from mapping_suite_sdk.mapping_package_v3.models.mapping_package_v3 import MappingPackageV3


class MPV3StructuralValidationException(MPValidationException): pass


class MPV3HashValidationException(MPValidationException): pass


class MPV3HashValidationStep(MPValidationStepABC):
    """
    Validates the hash-based signature of a Mapping Package V3 to ensure its integrity.
    """

    @validate_next
    def validate(self,
                 mapping_package: MappingPackageV3,
                 hasher: Optional[HasherABC] = None) -> Literal[True] | NoReturn:

        mp_hasher = MappingPackageV3Hasher(mapping_package=mapping_package, hasher=hasher)
        generated_hash: str = mp_hasher.hash()

        try:
            assert generated_hash == mapping_package.metadata.mapping_suite_hash_digest
        except AssertionError:
            raise MPV3HashValidationException(
                f"Mapping Package validation error: Package with identifier {mapping_package.metadata.id} has different signature:\n"
                f"Expected  signature for {mapping_package.metadata.id}: {mapping_package.metadata.mapping_suite_hash_digest}\n"
                f"Generated signature for {mapping_package.metadata.id}: {generated_hash}")

        return True


@final
@traced_class
class MappingPackageV3Validator:
    """
    The main class that orchestrates the validation process of MappingPackageV3 by chaining the validation steps.

    Attributes:
        validation_chain (MPValidationStepABC): The chain of validation steps to be executed.

    Methods:
        validate(mapping_package: MappingPackageV3) -> Literal[True] | NoReturn:
            Executes the validation chain to validate the given Mapping Package.
    """

    def __init__(self, validation_chain: Optional[MPValidationStepABC] = None):
        self.validation_chain = validation_chain or MPV3HashValidationStep()

    def validate(self, mapping_package: MappingPackageV3) -> Literal[True] | NoReturn:
        return self.validation_chain.validate(mapping_package=mapping_package)
