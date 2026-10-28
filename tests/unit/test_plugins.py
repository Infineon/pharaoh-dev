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


@pytest.mark.parametrize("keyword", [False, True])
@pytest.mark.parametrize(("first", "second"), [("image", "raw_txt"), ("raw_txt", "image")])
def test_asset_template_cache_distinguishes_names(keyword, first, second):
    try:
        pm = PharaohPluginManager()

        def lookup(name):
            if keyword:
                return pm.pharaoh_find_asset_render_template(template_name=name)
            return pm.pharaoh_find_asset_render_template(name)

        with mock.patch.object(
            pm.pm.hook,
            "pharaoh_find_asset_render_template",
            wraps=pm.pm.hook.pharaoh_find_asset_render_template,
        ) as hook:
            first_result = lookup(first)
            second_result = lookup(second)

            assert [path.name for path in first_result] == [f"{first}.rst.jinja2"]
            assert [path.name for path in second_result] == [f"{second}.rst.jinja2"]
            assert lookup(first) is first_result
            assert hook.call_count == 2
    finally:
        clear_cache()


def test_missing_keyword_template_is_not_hidden_by_cache():
    try:
        pm = PharaohPluginManager()
        pm.pharaoh_find_asset_render_template(template_name="image")

        with pytest.raises(LookupError, match="Cannot find template 'missing_template'"):
            pm.pharaoh_find_asset_render_template(template_name="missing_template")
    finally:
        clear_cache()


def test_multiple_plugin_directories(tmp_path, monkeypatch):
    first = tmp_path / "first"
    second = tmp_path / "second"
    for directory, marker in ((first, "first"), (second, "second")):
        directory.mkdir()
        (directory / "plugin.py").write_text(
            "from pharaoh.plugins.api import impl\n"
            "@impl\n"
            "def pharaoh_collect_default_settings():\n"
            f"    return {{'directory': '{marker}'}}\n"
        )
    monkeypatch.setenv("PHARAOH_PLUGINS", f"{first};{second}")
    try:
        manager = PharaohPluginManager()
        settings = manager.pharaoh_collect_default_settings()
        assert {entry["directory"] for entry in settings if isinstance(entry, dict)} == {"first", "second"}
        assert manager.pm.get_plugin("plugin").__file__ == str(first / "plugin.py")
        manager.reload_plugins()
        settings = manager.pharaoh_collect_default_settings()
        assert len([entry for entry in settings if isinstance(entry, dict)]) == 2
    finally:
        clear_cache()


def test_duplicate_plugin_directory_is_loaded_once(tmp_path, monkeypatch):
    (tmp_path / "plugin.py").write_text(
        "from pharaoh.plugins.api import impl\n"
        "@impl\n"
        "def pharaoh_collect_default_settings():\n"
        "    return {'directory': 'only'}\n"
    )
    monkeypatch.setenv("PHARAOH_PLUGINS", f"{tmp_path};{tmp_path}/../{tmp_path.name}")
    try:
        manager = PharaohPluginManager()
        settings = manager.pharaoh_collect_default_settings()
        assert len([entry for entry in settings if isinstance(entry, dict)]) == 1
    finally:
        clear_cache()
