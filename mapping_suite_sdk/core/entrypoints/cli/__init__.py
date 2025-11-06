import logging

from enum import Enum


class MappingPackageVersion(str, Enum):
    V1 = "v1"
    V2 = "v2"
    V3 = "v3"

    @classmethod
    def list(cls):
        """Return a list of all enum values."""
        return [member.value for member in cls]


def typer_verbose_callback(show_verbose: bool) -> None:
    if show_verbose:
        logging.getLogger().setLevel(logging.DEBUG)
