import logging
from enum import Enum

try:
    import typer  # noqa: F401  - the CLI modules need it; fail here with one line instead of a traceback
except ImportError:  # pragma: no cover - runs in tests/core_only (no [cli] extra)
    raise SystemExit("The mssdk command needs: pip install mapping-suite-sdk[cli]") from None


class MappingPackageVersion(str, Enum):
    V1 = "v1"
    V2 = "v2"
    V3 = "v3"
    V3L = "v3L"

    @classmethod
    def list(cls):
        """Return a list of all enum values."""
        return [member.value for member in cls]


def typer_verbose_callback(show_verbose: bool) -> None:
    if show_verbose:
        logging.getLogger().setLevel(logging.DEBUG)
