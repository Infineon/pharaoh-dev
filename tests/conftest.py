from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ["PHARAOH.LOGGING.LEVEL"] = "DEBUG"

test_plugin_path = (Path(__file__).parent / "templates/testing").absolute()
os.environ["PHARAOH_PLUGINS"] = str(test_plugin_path)


@pytest.fixture
def new_proj(tmp_path):
    from pharaoh.api import PharaohProject

    return PharaohProject(project_root=tmp_path / "project")
