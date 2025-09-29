import hashlib
import logging
import re
from abc import ABC, abstractmethod
from typing import Optional, Union

logger = logging.getLogger(__name__)


def normalize_content(content: Union[str, bytes]) -> bytes:
    """
    Normalize content by removing different types of line endings.

    This function removes all variations of line endings (CR, LF, CRLF) from the content
    to ensure consistent hashing across different operating systems.

    Args:
        content (Union[str, bytes]): The content to normalize.

    Returns:
        bytes: The normalized content as bytes with line endings removed.
    """
    new_line_pattern = re.compile(b'\r\n|\r|\n')

    if isinstance(content, str):
        return re.sub(new_line_pattern, b'', content.encode('utf-8'))
    else:
        return re.sub(new_line_pattern, b'', content)


class HasherABC(ABC):
    """
    Abstract base class defining a hasher that can generate a hash for a given content.

    Any class inheriting from this must implement a 'hash' method that accepts
    content (bytes) and returns a hash string.
    """

    @abstractmethod
    def hash(self, content: bytes) -> str:
        """
        Generate a hash for the given content.

        Args:
            content (bytes): The content to hash.

        Returns:
            str: The generated hash as a hexadecimal string.
        """
        pass


class SHA256Hasher(HasherABC):
    """
    A hasher implementation that uses the SHA-256 algorithm.
    """

    def hash(self, content: bytes) -> str:
        """
        Generate a SHA-256 hash for the given content.

        Args:
            content (bytes): The content to hash.

        Returns:
            str: The SHA-256 hash as a hexadecimal string.
        """
        return hashlib.sha256(content).hexdigest()


class MappingPackageHasher(ABC):
    """
    Abstract base class defining a hasher for mapping packages.

    Any class inheriting from this must implement a 'hash' method that
    generates a signature for a mapping package.
    """

    @abstractmethod
    def hash(self, with_version: Optional[str] = None) -> str:
        """
        Generate a comprehensive hash for a mapping package.

        Args:
            with_version (Optional[str], optional): Override the version used in the hash.
                If not provided, the package's mapping_version will be used.

        Returns:
            str: The final hash signature for the mapping package.
        """
        pass
