from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

import attrs
import pytest

from pharaoh.plugins.plugin_manager import PharaohPluginManager, clear_cache
from pharaoh.plugins.template import ContextVar, L1Template


def test_context_var_model():
    assert attrs.astuple(ContextVar("foo", "str", "default", True, "help")) == ("foo", str, "default", True, "help")
    assert attrs.astuple(ContextVar("foo", str, "", False)) == ("foo", str, "", False, "")

    with pytest.raises(ValueError, match="'notype' is not a builtin type"):
        ContextVar("foo", "notype", "")


def test_l1template_model():
    assert attrs.astuple(L1Template("foo", __file__)) == ("foo", Path(__file__), [], [])

    t = L1Template("foo", __file__, ["foo.bar"], [ContextVar("foo", str, "")])
    assert attrs.astuple(t) == ("foo", Path(__file__), ["foo.bar"], [("foo", str, "", True, "")])


# PHARAOH_PLUGINS set in conftest.py
@mock.patch.dict(os.environ, {"PHARAOH_PLUGINS": ""})
def test_plugin_discovery():
    try:
        pm = PharaohPluginManager()
        l1 = pm.pharaoh_collect_l1_templates()

        assert "pharaoh.default_project" in l1
        assert "pharaoh_testing.test_project" not in l1
    finally:
        # Instantiating the plugin manager a second time will overwrite the caches of the global singleton, so
        # we have to reset the cache here so following tests are working with the singleton plugin manager instance.
        clear_cache()
