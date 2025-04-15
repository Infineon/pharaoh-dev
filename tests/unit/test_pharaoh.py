from __future__ import annotations

from typing import TYPE_CHECKING

import omegaconf
import pytest
from attr import asdict, astuple

import pharaoh.errors
import pharaoh.log
import pharaoh.project as pharaoh_proj
from pharaoh.project import Component

if TYPE_CHECKING:
    from pytest_mock import MockFixture


def test_get_app(tmp_path):
    pharaoh_proj.LRU_PHARAOH_PROJECT = None
    with pytest.raises(RuntimeError):
        pharaoh_proj.get_project()

    proj = pharaoh_proj.PharaohProject(project_root=tmp_path)
    assert pharaoh_proj.get_project() is proj


def test_del(tmp_path):
    import gc

    proj = pharaoh_proj.PharaohProject(project_root=tmp_path)
    assert len(pharaoh.log.log.handlers) == 3
    pharaoh_proj.LRU_PHARAOH_PROJECT = proj = None  # noqa: F841
    gc.collect()
    assert len(pharaoh.log.log.handlers) == 1


def test_create_project_in_empty_dir(tmp_path):
    pharaoh_proj.PharaohProject(tmp_path)


def test_create_project_in_non_empty_dir(tmp_path):
    (tmp_path / "bla.txt").touch()
    with pytest.raises(pharaoh.errors.ProjectInconsistentError):
        pharaoh_proj.PharaohProject(tmp_path, overwrite=False)


def test_reuse_existing_project(tmp_path, mocker: MockFixture):
    from pharaoh.plugins.plugin_manager import PM

    pharaoh_project_created = mocker.spy(PM, "pharaoh_project_created")
    pharaoh_proj.PharaohProject(tmp_path)
    pharaoh_project_created.assert_called_once()
    pharaoh_project_created.reset_mock()
    pharaoh_proj.PharaohProject(tmp_path)
    pharaoh_project_created.assert_not_called()


def test_overwrite_existing_project(tmp_path, mocker: MockFixture):
    from pharaoh.plugins.plugin_manager import PM

    pharaoh_proj.PharaohProject(tmp_path)
    shutil_rmtree = mocker.patch("shutil.rmtree")
    pharaoh_project_created = mocker.spy(PM, "pharaoh_project_created")
    pharaoh_proj.PharaohProject(tmp_path, overwrite=True)
    shutil_rmtree.assert_called_once()
    pharaoh_project_created.assert_called_once()


def test_find_app(new_proj):
    subdir = new_proj.project_root / "a/b/c"
    proj = pharaoh_proj.get_project(subdir)
    assert proj.project_root == new_proj.project_root

    with pytest.raises(LookupError, match="Cannot find a Pharaoh project file"):
        pharaoh_proj.get_project(new_proj.project_root.parent / "a/b/c")


def test_find_components(new_proj):
    new_proj.add_component("empty1", "pharaoh_testing.simple", metadata={"foo": "bar"})
    new_proj.add_component("empty2", "pharaoh_testing.simple", metadata={"foo": "baz"})

    assert len(new_proj.find_components("name.startswith('empty')")) == 2
    assert new_proj.find_components("metadata.foo == 'bar'")[0].name == "empty1"
    assert new_proj.find_components("metadata.foo == 'baz'")[0].name == "empty2"
    assert new_proj.find_components("metadata.foo == 123'") == []

    assert len(new_proj.find_components()) == 2


def test_archive_report(new_proj, tmp_path):
    assert new_proj.build_report() == 0

    new_proj.put_setting("report.archive_name", "archive1.zip")
    new_proj.archive_report()
    assert (new_proj.project_root / "archive1.zip").exists()

    new_proj.archive_report("archive2.zip")
    assert (new_proj.project_root / "archive2.zip").exists()

    new_proj.archive_report(tmp_path / "archives/archive3.zip")
    assert (tmp_path / "archives/archive3.zip").exists()

    new_proj.put_setting("report.archive_name", "archive4.zip")
    assert new_proj.build_report() == 0
    assert not (new_proj.project_root / "archive4.zip").exists()


def test_get_current_component(new_proj):
    COMP = "component_1"
    new_proj.add_component(COMP, "pharaoh_testing.simple")

    code = f"""
from pharaoh.assetlib.api import get_current_component
assert get_current_component() == "{COMP}"
"""
    # Execute the code in a context of a file inside the component
    exec(compile(code, new_proj.sphinx_report_project_components / COMP / "asset_scripts/dummy.py", "exec"))
    exec(compile(code, new_proj.sphinx_report_project_components / COMP / "asset_scripts/subdir/dummy.py", "exec"))
    with pytest.raises(LookupError, match="was not executed from inside a component"):
        exec(compile(code, new_proj.sphinx_report_project_components / "dummy.py", "exec"))


def test_add_components(new_proj):
    new_proj.add_component("component_1", "pharaoh_testing.simple", metadata={"foo": 1})
    new_proj.add_component("component_2", "pharaoh_testing.complex", metadata={"foo": 2})
    with pytest.raises(ValueError, match="Not a valid template"):
        new_proj.add_component("component_3", "not_existing", metadata={"foo": 4})

    with pytest.raises(ValueError, match="No templates specified"):
        new_proj.add_component("component_3", [])


def test_overwrite_components(new_proj):
    new_proj.add_component("component_1", "pharaoh_testing.simple")
    new_proj.add_component("component_2", "pharaoh_testing.simple")

    with pytest.raises(KeyError):
        new_proj.add_component("component_1", "pharaoh_testing.simple", overwrite=False)

    new_proj.add_component("component_1", "pharaoh_testing.simple", overwrite=True)
    assert new_proj._project_settings.components[0].name == "component_2"
    assert new_proj._project_settings.components[1].name == "component_1"

    new_proj.add_component("component_1", "pharaoh_testing.simple", overwrite=True, index=0, metadata={"foo": "bar"})
    assert new_proj._project_settings.components[0].name == "component_1"
    assert new_proj._project_settings.components[0].metadata.foo == "bar"
    assert new_proj._project_settings.components[1].name == "component_2"


def test_remove_component(new_proj):
    new_proj.add_component("component_A1", "pharaoh_testing.simple")
    new_proj.add_component("component_a2", "pharaoh_testing.simple")
    new_proj.add_component("component_B1", "pharaoh_testing.simple")
    new_proj.add_component("component_C1", "pharaoh_testing.simple")
    new_proj.add_component("component_D4", "pharaoh_testing.simple")
    assert new_proj.remove_component("component_A", regex=True) == ["component_A1", "component_a2"]
    assert new_proj.remove_component("component_A", regex=False) == []
    assert new_proj.remove_component("component_.*1", regex=True) == ["component_B1", "component_C1"]
    assert new_proj._project_settings.components[0].name == "component_D4"
    assert new_proj.remove_component("component_D4") == ["component_D4"]


def test_template_composition(tmp_path):
    """
    Tests if templating with multiple templates at once is properly working
    """
    new_proj = pharaoh_proj.PharaohProject(
        project_root=tmp_path / "project",
        templates=("pharaoh.default_project", "pharaoh_testing.test_project"),
    )
    reportdir = new_proj.sphinx_report_project
    assert (reportdir / "conf.py").exists()
    assert (reportdir / "index.rst").exists()
    index_rst_content = (reportdir / "index.rst").read_text()
    # Make sure Jinja tags are not rendered
    assert "{{ h1(" in index_rst_content
    # Check that index.rst is coming from template "pharaoh_testing.test_project"
    assert index_rst_content.startswith("{# TESTING TEMPLATE #}")

    new_proj.add_component("component_1", ["pharaoh_testing.simple", "pharaoh_testing.simple_composition"])

    new_proj.generate_assets()
    # Since a second asset script was added by template pharaoh_testing.simple_composition we have 2 assets now
    assert len(list(new_proj.asset_finder.iter_assets())) == 2
    status = new_proj.build_report()
    # new_proj.open_report()
    assert status == 0


def test_component_init():
    comp = Component("foo", ["bar"])
    assert astuple(comp) == ("foo", ["bar"], {}, [], {})
    assert comp.get_render_context() == {"component_name": "foo", "resources": [], "metadata": {}}

    with pytest.raises(TypeError, match="'name' must be"):
        Component(123, ["bar"])

    with pytest.raises(TypeError, match="'templates' must be"):
        Component("foo", [123])

    with pytest.raises(ValueError, match="'name' must match regex"):
        Component("-", ["bar"])

    dict_cfg = {
        "name": "dummy",
        "templates": ["foo.bar"],
        "render_context": {"a": "b"},
        "resources": [],
        "metadata": {"c": "d"},
    }
    cfg = omegaconf.OmegaConf.create(dict_cfg)
    comp = Component.from_dictconfig(cfg)
    assert cfg == asdict(comp)


def test_custom_settings(tmp_path):
    """
    Tests if templating with multiple templates at once is properly working
    """
    custom = tmp_path / "custom.yaml"
    custom.write_text(
        """
report:
  builder: "${oc.env:BUILDER,html}"
  author: hans
toolkits:
  bokeh:
    export_png:
      width: 10000
"""
    )
    new_proj = pharaoh_proj.PharaohProject(project_root=tmp_path / "project", custom_settings=custom)
    settings = new_proj.get_settings()
    settings_str = str(settings)

    assert "'builder': '${oc.env:BUILDER,html}'" in settings_str
    assert settings.report.builder == "html"
    assert settings.report.author == "hans"
    assert settings.toolkits.bokeh.export_png.width == 10000
    assert settings.logging.level == "DEBUG"  # Default set by tests/conftest.py


def test_template_by_path(new_proj):
    from pharaoh.plugins.plugin_manager import PM

    l1_templates = PM.pharaoh_collect_l1_templates()

    template_path = l1_templates["pharaoh_testing.simple"].path
    new_proj.add_component("dummy_1", template_path)
    assert new_proj._project_settings.components[0].templates[0] == str(template_path)

    new_proj.generate_assets()
    new_proj.build_report()


def test_add_additional_templates(new_proj):
    new_proj.add_component("dummy", "pharaoh_testing.simple", render_context={"foo": "bar"})
    new_proj.add_template_to_component("dummy", ["pharaoh_testing.simple_composition"], {"bla": "blubb"})
    with pytest.raises(KeyError):
        new_proj.add_template_to_component("not a component", ["pharaoh_testing.simple_composition"])

    with pytest.raises(ValueError, match="No templates specified"):
        new_proj.add_template_to_component("dummy", [])

    assert new_proj._project_settings.components[0].templates == [
        "pharaoh_testing.simple",
        "pharaoh_testing.simple_composition",
    ]
    assert "PLOTLY2" in (new_proj.sphinx_report_project_components / "dummy/index.rst").read_text()
    assert (new_proj.sphinx_report_project_components / "dummy/asset_scripts/plotly_plots_2.py").exists()
    assert "foo" in new_proj._project_settings.components[0].render_context
    assert "bla" in new_proj._project_settings.components[0].render_context


def test_component_filtering(new_proj):
    new_proj.put_setting(
        "report.component_filter",
        {
            "include": ".*",
            "exclude": "bar2",
        },
    )
    new_proj.add_component("foo1", "pharaoh_testing.simple")
    new_proj.add_component("foo2", "pharaoh_testing.simple")
    new_proj.add_component("bar1", "pharaoh_testing.simple")
    new_proj.add_component("bar2", "pharaoh_testing.simple")
    new_proj.add_component("baz", "pharaoh_testing.simple")
    new_proj.save_settings()

    names = [c.name for c in new_proj.iter_components()]
    assert names == ["foo1", "foo2", "bar1", "bar2", "baz"]

    names = [c.name for c in new_proj.iter_components(filtered=True)]
    assert names == ["foo1", "foo2", "bar1", "baz"]
