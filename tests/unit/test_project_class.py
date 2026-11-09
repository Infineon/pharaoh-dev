from __future__ import annotations

import os
import runpy
from contextlib import contextmanager

import pytest
from click.testing import CliRunner

from pharaoh.cli import cli
from pharaoh.plugins.api import impl
from pharaoh.plugins.plugin_manager import PM, clear_cache
from pharaoh.project import PharaohProject, get_project


@contextmanager
def project_class_plugin(result):
    class Plugin:
        @impl
        def pharaoh_get_project_class(self):
            return result

    plugin = Plugin()
    PM.pm.register(plugin)
    try:
        yield
    finally:
        PM.pm.unregister(plugin)
        clear_cache()


class CustomProject(PharaohProject):
    def _load_default_settings(self):
        settings = super()._load_default_settings()
        settings.custom_project_default = "custom"
        return settings


def test_default_project_class():
    assert PM.pharaoh_get_project_class() is PharaohProject
    with project_class_plugin(None):
        assert PM.pharaoh_get_project_class() is PharaohProject


@pytest.mark.parametrize("invalid", [object, 123, lambda: CustomProject])
def test_invalid_project_class(invalid):
    with project_class_plugin(invalid), pytest.raises(TypeError, match="PharaohProject subclass"):
        PM.pharaoh_get_project_class()


def test_custom_class_for_cli_discovery_and_sphinx(tmp_path):
    with project_class_plugin(CustomProject):
        result = CliRunner().invoke(cli, ["--path", str(tmp_path), "new"], catch_exceptions=False)
        assert result.exit_code == 0, result.output
        project = get_project(tmp_path)
        assert isinstance(project, CustomProject)
        assert project.get_setting("custom_project_default") == "custom"
        assert get_project() is project
        child = tmp_path / "nested"
        child.mkdir()
        assert isinstance(get_project(child), CustomProject)
        assert isinstance(get_project(tmp_path / "pharaoh.yaml"), CustomProject)
        config = runpy.run_path(str(project.sphinx_report_project / "conf.py"))
        assert isinstance(config["proj"], CustomProject)
        assert project.build_report() == 0


def test_custom_class_for_asset_generation(tmp_path):
    from pharaoh.assetlib.generation import generate_assets

    with project_class_plugin(CustomProject):
        project = CustomProject(tmp_path)
        source = tmp_path / "asset.py"
        source.write_text(
            "from pharaoh.api import get_project\n"
            "assert type(get_project()).__name__ == 'CustomProject'\n"
            "assert get_project().get_setting('custom_project_default') == 'custom'\n"
        )
        generate_assets(project.project_root, source)
        assert isinstance(get_project(), CustomProject)


def test_discovered_project_class_in_worker(tmp_path, monkeypatch):
    import nbformat

    from pharaoh.assetlib.generation import generate_assets, generate_assets_parallel

    plugin_path = tmp_path / "plugin"
    plugin_path.mkdir()
    (plugin_path / "plugin.py").write_text(
        "from pharaoh.plugins.api import impl\n"
        "@impl\n"
        "def pharaoh_get_project_class():\n"
        "    from pharaoh.project import PharaohProject\n"
        "    class WorkerProject(PharaohProject):\n"
        "        pass\n"
        "    return WorkerProject\n"
    )
    original = os.environ.get("PHARAOH_PLUGINS", "")
    monkeypatch.setenv("PHARAOH_PLUGINS", str(plugin_path))
    try:
        PM.reload_plugins()
        project = PM.pharaoh_get_project_class()(tmp_path / "project")
        source = project.project_root / "asset.py"
        source.write_text(
            "from pathlib import Path\n"
            "from pharaoh.api import get_project\n"
            "assert type(get_project()).__name__ == 'WorkerProject'\n"
            "Path(__file__).with_suffix('.proof').write_text('worker used custom class')\n"
        )
        results = generate_assets_parallel(project.project_root, [("", source)], workers=1)
        assert len(results) == 1
        assert results[0][1] is None
        assert source.with_suffix(".proof").read_text() == "worker used custom class"
        notebook = project.project_root / "asset.ipynb"
        nbformat.write(
            nbformat.v4.new_notebook(
                cells=[
                    nbformat.v4.new_code_cell(
                        "from pharaoh.api import get_project\nassert type(get_project()).__name__ == 'WorkerProject'\n"
                    )
                ]
            ),
            notebook,
        )
        generate_assets(project.project_root, notebook)
    finally:
        monkeypatch.setenv("PHARAOH_PLUGINS", original)
        PM.reload_plugins()
