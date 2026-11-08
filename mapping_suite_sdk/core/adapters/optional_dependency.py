"""Import an optional integration library at the point of use, naming the extra that provides it."""

import importlib
from types import ModuleType


def require(module: str, extra: str, feature: str) -> ModuleType:
    """Return ``module``, or raise an ImportError that tells the user which extra to install."""
    try:
        return importlib.import_module(module)
    except ImportError as err:
        raise ImportError(f"{feature} support needs: pip install mapping-suite-sdk[{extra}]") from err
