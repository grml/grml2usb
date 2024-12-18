import os

import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "require_root: mark test to run only as root")


def pytest_runtest_setup(item):
    if "require_root" in {mark.name for mark in item.iter_markers()}:
        if os.getuid() != 0:
            pytest.skip("must be root")
