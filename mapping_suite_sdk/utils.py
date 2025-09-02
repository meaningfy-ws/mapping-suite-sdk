from pathlib import Path
from typing import Tuple, NoReturn, Union, Optional

from mapping_suite_sdk.vars import SUPPORTED_TEXT_FILE_EXTENSIONS, SUPPORTED_BYTES_FILE_EXTENSIONS


def load_file_by_extensions(file_path: Path,
                            str_extensions: Tuple = SUPPORTED_TEXT_FILE_EXTENSIONS,
                            bytes_extensions: Tuple = SUPPORTED_BYTES_FILE_EXTENSIONS) -> str | bytes | None:
    """
    Load content from a file based on its extension.

    Args:
        file_path: Path to the file
        str_extensions: List of extensions to read as string (text mode)
        bytes_extensions: List of extensions to read as bytes (binary mode)

    Returns:
        File content as string or bytes depending on the extension,
        or None if the extension is not in either list
    """
    if not file_path.exists():
        return None

    if not file_path.is_file():
        return None

    extension = file_path.suffix.lower()

    if extension in str_extensions:
        return file_path.read_text()
    elif extension in bytes_extensions:
        with open(file_path, 'rb') as file:
            return file.read()
    else:
        return None


def write_file_by_content_type(file_path: Path, content: Union[str, bytes]) -> Optional[NoReturn]:
    """
    Write content to a file based on its content type (str or bytes).
    Raises exceptions if any errors occur during the process.

    Args:
        file_path: Path to the file
        content: Content to write, either string or bytes

    Returns:
        None if successful

    Raises:
        TypeError: If content is neither string nor bytes
        OSError: If file operations fail (permission issues, disk full, etc.)
        Exception: For any other unexpected errors
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(content, str):
        file_path.write_text(content)
    elif isinstance(content, bytes):
        file_path.write_bytes(content)
    else:
        raise TypeError(f"Content must be str or bytes, got {type(content).__name__}")

    return None
