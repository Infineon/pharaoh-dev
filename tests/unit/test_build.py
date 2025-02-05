from __future__ import annotations

import os
from unittest import mock

import pytest

from pharaoh.api import FileResource, PharaohProject


def test_build_empty_project(new_proj):
    assert len(new_proj.generate_assets()) == 0
    status = new_proj.build_report()
    assert status == 0


def test_build_project_with_assets(new_proj):
    new_proj.add_component("dummy_1", "pharaoh_testing.complex", {"test_name": "Dummy 1"})
    new_proj.generate_assets()
    assert (
        len(list(new_proj.asset_finder.iter_assets())) >= 10
    )  # May be more in the future, but check if the assets were generated
    status = new_proj.build_report()
    # new_proj.open_report()
    assert status == 0


def test_build_project_with_notebook(new_proj):
    resource = new_proj.project_root / "data.txt"
    resource.touch()
    new_proj.add_component("mycomponent", "pharaoh_testing.ipynb", resources=[FileResource("mydata", resource)])
    new_proj.generate_assets()
    status = new_proj.build_report()
    new_proj.open_report()
    assert status == 0


def test_build_project_with_parallel_asset_gen(new_proj):
    new_proj.add_component("dummy_1", "pharaoh_testing.simple", {"test_name": "Dummy 1"})
    new_proj.put_setting("asset_gen.worker_processes", 2)
    scripts = new_proj.generate_assets()
    assert len(scripts) == 1
    assets = list(new_proj.asset_finder.iter_assets())
    assert len(assets) >= 1
    status = new_proj.build_report()
    assert status == 0


@mock.patch.dict(os.environ, {"PHARAOH.ASSET_GEN.FORCE_STATIC": "True"})
def test_build_project_with_assets_static(new_proj):
    new_proj.load_settings("env")
    assert new_proj.get_setting("asset_gen.force_static", True)

    new_proj.add_component("dummy_1", "pharaoh_testing.complex", {"test_name": "Dummy 1"})
    new_proj.generate_assets()
    status = new_proj.build_report()
    assert status == 0
    assert len(list(new_proj.asset_build_dir.rglob("*.html"))) == 6
    assert len(list(new_proj.asset_build_dir.rglob("dummy_table_*.html"))) == 3
    assert len(list(new_proj.asset_build_dir.rglob("raw_*.html"))) == 1


def test_build_project_with_multiple_components(new_proj):
    """
    Test if the "components" directive option properly limits the found assets to the invoking component
    """
    new_proj.add_component("dummy_1", "pharaoh_testing.simple", {"test_name": "Dummy 1", "all_components": True})
    new_proj.add_component("dummy_2", "pharaoh_testing.simple", {"test_name": "Dummy 2", "all_components": False})
    new_proj.generate_assets()
    assert (
        len(new_proj.asset_finder.discover_assets()) == 2
    )  # May be more in the future, but check if the assets were generated
    status = new_proj.build_report()
    # new_proj.open_report()
    c1_html = new_proj.sphinx_report_build / "components/dummy_1/index.html"
    c2_html = new_proj.sphinx_report_build / "components/dummy_2/index.html"
    assert status == 0
    assert c1_html.read_text(encoding="utf-8").count("plotly-graph-div") == 2
    assert c2_html.read_text(encoding="utf-8").count("plotly-graph-div") == 1


def test_build_project_with_dynamic_include(new_proj, tmp_path):
    tmpl_dir = tmp_path / "tmpl"
    (tmpl_dir / "subdir").mkdir(parents=True)
    (tmpl_dir / "subdir" / "dynamic_content.rst").write_text(
        '{{ heading("Dynamic Section", 3) }}\n\n'
        "Dynamically overwritten from PyTest test: test_build_project_with_dynamic_include\n"
    )

    new_proj.add_component("dummy", ("pharaoh_testing.dynamic_include", str(tmpl_dir)))
    new_proj.generate_assets()
    status = new_proj.build_report()
    assert status == 0
    # new_proj.open_report()
    assert "test_build_project_with_dynamic_include" in (
        new_proj.sphinx_report_build / "components/dummy/subdir/dynamic_content.html"
    ).read_text(encoding="utf-8")


def test_build_project_with_template_file(new_proj, tmp_path):
    tmpl_file = tmp_path / "mytemplate" / "tmpl.pharaoh.py"
    tmpl_file.parent.mkdir(parents=True)
    tmpl_file.write_text(
        '''
"""
{{ heading("My Plots", 2) }}

.. pharaoh-asset::
    :filter: label == "my_plot"
"""
from pharaoh.assetlib.api import metadata_context

import plotly.express as px


df = px.data.iris()
fig = px.scatter(
    df,
    x="sepal_width",
    y="sepal_length",
    color="species",
    symbol="species",
    title=r"A title",
)

with metadata_context(label="my_plot"):
    fig.write_html(file="iris_scatter.html")
'''
    )

    new_proj.add_component("dummy", ["pharaoh_testing.template_file", str(tmpl_file)])
    new_proj.generate_assets()
    status = new_proj.build_report()
    assert status == 0
    assert (new_proj.sphinx_report_project_components / "dummy/asset_scripts/tmpl.py").exists()
    assert (new_proj.sphinx_report_project_components / "dummy/index_tmpl.rst").exists()
    assert 'href="#my-plots"' in (new_proj.sphinx_report_build / "components/dummy/index.html").read_text(
        encoding="utf-8"
    )
    # new_proj.open_report()


@pytest.mark.parametrize(
    "script_text",
    [
        '''foo = "bar"''',
        '''""""""\nfoo = "bar"''',
        '''"""\n"""\nfoo = "bar"''',
    ],
)
def test_build_project_with_template_file_without_docstring(new_proj, tmp_path, script_text):
    tmpl_file = tmp_path / "mytemplate" / "tmpl.pharaoh.py"
    tmpl_file.parent.mkdir(parents=True)
    tmpl_file.write_text(script_text)

    new_proj.add_component("dummy", ["pharaoh_testing.template_file", str(tmpl_file)])
    status = new_proj.build_report()
    assert status == 0
    assert (new_proj.sphinx_report_project_components / "dummy/asset_scripts/tmpl.py").exists()
    assert not (new_proj.sphinx_report_project_components / "dummy/index_tmpl.rst").exists()


def test_build_project_with_template_directory(new_proj, tmp_path):
    tmpl_file = tmp_path / "mytemplate" / "index.rst"
    tmpl_file.parent.mkdir(parents=True)
    tmpl_file.write_text("Title\n=====\n")

    new_proj.add_component("dummy", [str(tmpl_file.parent)])
    status = new_proj.build_report()
    assert status == 0


def test_build_project_manual_asset_include(new_proj, tmp_path):
    new_proj.add_component("dummy", ["pharaoh_testing.manual_asset_include"])
    new_proj.generate_assets()
    status = new_proj.build_report()
    copied_assets = list((new_proj.sphinx_report_build / "pharaoh_assets").glob("*"))
    assert len(copied_assets) == 2
    assert status == 0


def test_template_file_and_folder_names(new_proj, tmp_path):
    new_proj.add_component(
        "dummy",
        ["pharaoh_testing.copier"],
        render_context={"dirname": "foo", "filename": "bar", "heading_prefix": "baz - "},
    )
    status = new_proj.build_report()
    assert status == 0
    assert (new_proj.sphinx_report_project_components / "dummy/foo/bar.rst").exists()


def test_build_project_with_custom_built_time_templates(tmp_path):
    proj = PharaohProject(
        project_root=tmp_path / "project",
        templates=["pharaoh.default_project", "pharaoh_testing.template_inheritance_project"],
    )

    assert (proj.sphinx_report_project / "user_templates/base1.rst").exists()
    assert (proj.sphinx_report_project / "user_templates/subdir/base2.rst").exists()

    proj.add_component("dummy1", ["pharaoh_testing.template_inheritance_component"], {"base": "base1.rst"})
    proj.add_component("dummy2", ["pharaoh_testing.template_inheritance_component"], {"base": "subdir/base2.rst"})
    status = proj.build_report()
    assert status == 0

    dummy1_index_content = (proj.sphinx_report_build / "components/dummy1/index.html").read_text(encoding="utf-8")
    dummy2_index_content = (proj.sphinx_report_build / "components/dummy2/index.html").read_text(encoding="utf-8")

    assert "base1.rst" in dummy1_index_content
    assert "Paragraph from component" in dummy1_index_content

    assert "base2.rst" in dummy2_index_content
    assert "Paragraph from component" in dummy2_index_content


def test_error_report_component_with_errors(new_proj):
    TITLE = "Report Errors"

    new_proj.add_component("dummy", "pharaoh_testing.render_asset_error")
    new_proj.add_component("errors", "pharaoh.report_info", {"title": TITLE})
    new_proj.generate_assets()
    status = new_proj.build_report()
    # new_proj.open_report()
    assert status == 1  # should fail because of warnings

    dummy_index_content = (new_proj.sphinx_report_build / "components/dummy/index.html").read_text(encoding="utf-8")
    assert "This is a ValueError" in dummy_index_content
    assert "This is a TypeError" in dummy_index_content

    errors_index_content = (new_proj.sphinx_report_build / "components/errors/index.html").read_text(encoding="utf-8")
    assert f"<title>{TITLE}</title>" in errors_index_content
    assert "<h3>dummy<a" in errors_index_content
    assert "This is a ValueError" in errors_index_content
    assert "This is a TypeError" in errors_index_content


def test_error_report_component_without_errors(new_proj):
    new_proj.add_component("errors", "pharaoh.report_info")
    new_proj.generate_assets()
    status = new_proj.build_report()
    # new_proj.open_report()
    assert status == 0

    errors_index_content = (new_proj.sphinx_report_build / "components/errors/index.html").read_text(encoding="utf-8")
    assert "No errors found!" in errors_index_content
