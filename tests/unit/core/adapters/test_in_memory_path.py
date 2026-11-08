import io
import zipfile
from pathlib import Path, PurePosixPath

import pytest

from mapping_suite_sdk.core.adapters.in_memory_path import InMemoryPath


def _zip(files: dict[str, bytes | str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


@pytest.fixture
def root() -> InMemoryPath:
    return InMemoryPath.from_zip(
        _zip(
            {
                "metadata.json": "{}",
                "a.ttl": "a",
                "b.txt": "b",
                "test_data/s1/x.xml": "<x/>",
                "test_data/s1/y.txt": "y",
                "test_data/s2/z.xml": "<z/>",
                "logo.bin": b"\x00\xff",
                "empty/": b"",
            }
        )
    )


def test_from_zip_root_is_slash_when_files_are_at_the_top_level(root: InMemoryPath) -> None:
    assert str(root) == "/"


def test_from_zip_wrapping_folder_becomes_the_root() -> None:
    wrapped = InMemoryPath.from_zip(_zip({"pkg/metadata.json": "{}", "pkg/sub/a.txt": "a"}))

    assert str(wrapped) == "/pkg"
    assert (wrapped / "metadata.json").is_file()


def test_from_zip_ignores_macos_metadata_folder() -> None:
    wrapped = InMemoryPath.from_zip(_zip({"pkg/metadata.json": "{}", "__MACOSX/pkg/._metadata.json": "x"}))

    assert str(wrapped) == "/pkg"


def test_from_zip_two_top_level_folders_keep_slash_as_root() -> None:
    assert str(InMemoryPath.from_zip(_zip({"a/x.txt": "x", "b/y.txt": "y"}))) == "/"


def test_from_zip_accepts_a_binary_stream() -> None:
    from_stream = InMemoryPath.from_zip(io.BytesIO(_zip({"pkg/a.txt": "a"})))

    assert str(from_stream) == "/pkg"
    assert (from_stream / "a.txt").read_text() == "a"


def test_from_zip_not_a_zip_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Failed to extract ZIP file"):
        InMemoryPath.from_zip(b"not a zip")


def test_derived_paths_keep_the_archive(root: InMemoryPath) -> None:
    derived = root / "test_data" / "s1" / "x.xml"

    assert derived.is_file()
    assert derived.read_text() == "<x/>"
    assert derived.parent.is_dir()


def test_exists_is_file_is_dir(root: InMemoryPath) -> None:
    assert root.exists() and root.is_dir() and not root.is_file()
    assert (root / "a.ttl").exists() and (root / "a.ttl").is_file() and not (root / "a.ttl").is_dir()
    assert (root / "test_data").is_dir()
    assert not (root / "missing").exists()


def test_iterdir_lists_direct_children_only(root: InMemoryPath) -> None:
    assert {p.name for p in root.iterdir()} == {"metadata.json", "a.ttl", "b.txt", "test_data", "logo.bin"}
    assert {p.name for p in (root / "test_data").iterdir()} == {"s1", "s2"}
    assert all(isinstance(p, InMemoryPath) for p in root.iterdir())


def test_iterdir_of_a_file_is_empty(root: InMemoryPath) -> None:
    assert list((root / "a.ttl").iterdir()) == []


@pytest.mark.parametrize(
    ("pattern", "expected"),
    [
        ("*.ttl", {"/a.ttl"}),
        ("test_data/*/*.xml", {"/test_data/s1/x.xml", "/test_data/s2/z.xml"}),
        ("test_data/s1/*", {"/test_data/s1/x.xml", "/test_data/s1/y.txt"}),
        ("*.nothing", set()),
    ],
)
def test_glob_matches_segment_wise(root: InMemoryPath, pattern: str, expected: set[str]) -> None:
    assert {str(p) for p in root.glob(pattern)} == expected


def test_glob_is_lazy(root: InMemoryPath) -> None:
    assert next(root.glob("*.ttl"), None) == root / "a.ttl"
    assert next(root.glob("*.nothing"), None) is None


def test_read_bytes_and_read_text(root: InMemoryPath) -> None:
    assert (root / "logo.bin").read_bytes() == b"\x00\xff"
    assert (root / "a.ttl").read_text() == "a"
    assert (root / "a.ttl").read_text(encoding="utf-8") == "a"


def test_read_missing_file_raises_file_not_found(root: InMemoryPath) -> None:
    with pytest.raises(FileNotFoundError):
        (root / "missing").read_bytes()
    with pytest.raises(FileNotFoundError):
        (root / "missing").read_text()


def test_open_text_and_binary(root: InMemoryPath) -> None:
    with (root / "metadata.json").open(encoding="utf-8") as stream:
        assert stream.read() == "{}"
    with (root / "logo.bin").open("rb") as stream:
        assert stream.read() == b"\x00\xff"


def test_open_other_modes_are_rejected(root: InMemoryPath) -> None:
    with pytest.raises(ValueError, match="mode"):
        (root / "a.ttl").open("w")


def test_relative_to_returns_a_real_path(root: InMemoryPath) -> None:
    relative = (root / "test_data" / "s1" / "x.xml").relative_to(root)

    assert relative == Path("test_data/s1/x.xml")
    assert type(relative) is type(Path())


def test_suffix_and_name_come_from_pure_posix_path(root: InMemoryPath) -> None:
    assert (root / "a.TTL").suffix == ".TTL"
    assert (root / "a.ttl").name == "a.ttl"
    assert isinstance(root, PurePosixPath)
