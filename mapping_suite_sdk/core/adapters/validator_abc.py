from abc import ABC, abstractmethod
from types import FunctionType
from typing import Optional, Literal, NoReturn

from mapping_suite_sdk.core.models.mapping_package import MappingPackage


class MPValidationException(Exception): pass

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
        validate(mapping_package: MappingPackageABC) -> Literal[True] | NoReturn:
            Validates the given Mapping Package. If the validation passes, it returns True. If the validation fails, it raises an exception.
    """

    def __init__(self, next_validator: Optional["MPValidationStepABC"] = None):
        self.next_validator = next_validator

    @abstractmethod
    @validate_next
    def validate(self, mapping_package: MappingPackage) -> Literal[True] | NoReturn:
        raise NotImplementedError
