"""public-api: the root exports and leaves application logging alone."""

import json
import subprocess
import sys

import mapping_suite_sdk


def test_every_root_export_resolves():
    for name in mapping_suite_sdk.__all__:
        assert getattr(mapping_suite_sdk, name) is not None, name


def test_application_logging_unchanged():
    # a fresh interpreter: the test session has already imported mapping_suite_sdk
    script = (
        "import json, logging, sys\n"
        "handler = logging.StreamHandler(sys.stderr)\n"
        "root = logging.getLogger()\n"
        "root.setLevel(logging.WARNING)\n"
        "root.addHandler(handler)\n"
        "import mapping_suite_sdk\n"
        "print(json.dumps([root.level, len(root.handlers), root.handlers[0] is handler]))\n"
    )
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=True)
    assert json.loads(result.stdout) == [30, 1, True]


def test_in_memory_package_io_is_exported():
    for name in (
        "load_mapping_package_from_bytes",
        "mapping_package_to_zip_bytes",
        "save_mapping_package_v3_to_folder",
        "save_mapping_package_v3_to_archive",
    ):
        assert name in mapping_suite_sdk.__all__, name
