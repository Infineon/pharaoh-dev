"""
Backport of contextlib.chdir stdlib class added in Python3.11.
"""

from __future__ import annotations

import os
from contextlib import AbstractContextManager
from pathlib import Path


class chdir(AbstractContextManager):
    """Non thread-safe context manager to change the current working directory."""

    def __init__(self, path):
        self.path = path
        self._old_cwd = None

    def __enter__(self) -> Path:
        self._old_cwd = os.getcwd()
        path = Path(self.path)
        path.mkdir(parents=True, exist_ok=True)
        os.chdir(self.path)
        return path

    def __exit__(self, *excinfo):
        if self._old_cwd:
            os.chdir(self._old_cwd)
