import logging

import pytest


@pytest.fixture(autouse=True)
def _capture_info_logs(caplog):
    # the CLI reports results at INFO; the library no longer sets the root logger to INFO on import (DEC-6)
    caplog.set_level(logging.INFO)
