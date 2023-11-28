import json
import os
import platform
import re
import subprocess as sp
import sys
from pathlib import Path
from unittest import mock

import pytest

from pharaoh.assetlib.api import FileResource
from pharaoh.assetlib.generation import generate_assets, generate_assets_parallel, register_templating_context

example_assets = Path(__file__).with_name("_example_assets")


def assert_file_exists(files: list[Path], match: str):
    for file in files:
        if re.fullmatch(match, file.name):
            return
    msg = f"No file found that matches {match!r}!"
    raise AssertionError(msg)


def assert_assetinfo_file_exists(files: list[Path], match: str):
    for file in files:
        if re.fullmatch(match, file.name):
            content = json.loads(file.read_text())
            assert len(list(content["asset"].keys())) >= 5
            return content
    msg = f"No assetinfo file found that matches {match!r}!"
    raise AssertionError(msg)


def test_generate_python_bokeh_asset(new_proj):
    generate_assets(new_proj.project_root, example_assets / "bokeh_plot.py")
    files = list(new_proj.asset_build_dir.glob("*"))
    assert len(files) == 6
    assert_file_exists(files, r"iris_scatter_bokeh_1_.*.html")
    assert_file_exists(files, r"iris_scatter_bokeh_2_.*.png")
    assert_file_exists(files, r"iris_scatter_bokeh_3_.*.svg")
    assert_assetinfo_file_exists(files, r"iris_scatter_bokeh_.*.assetinfo")


@mock.patch.dict(os.environ, {"PHARAOH.ASSET_GEN.FORCE_STATIC": "True"})
def test_generate_python_bokeh_asset_static(new_proj):
    new_proj.load_settings("env")
    assert new_proj.get_setting("asset_gen.force_static", True)

    generate_assets(new_proj.project_root, example_assets / "bokeh_plot.py")
    files = list(new_proj.asset_build_dir.glob("*"))
    assert len(files) == 6
    assert_file_exists(files, r"iris_scatter_bokeh_1_.*.png")
    assert_file_exists(files, r"iris_scatter_bokeh_2_.*.png")
    assert_file_exists(files, r"iris_scatter_bokeh_3_.*.svg")
    assert_assetinfo_file_exists(files, r"iris_scatter_bokeh_.*.assetinfo")


def test_generate_python_plotly_asset(new_proj):
    generate_assets(new_proj.project_root, example_assets / "plotly_plot.py")
    files = list(new_proj.asset_build_dir.glob("*"))
    assert len(files) == 4
    assert_file_exists(files, r"iris_scatter1_.*.svg")
    assert_file_exists(files, r"iris_scatter2_.*.html")
    assert_assetinfo_file_exists(files, r"iris_scatter1_.*.assetinfo")
    assert_assetinfo_file_exists(files, r"iris_scatter2_.*.assetinfo")


@mock.patch.dict(os.environ, {"PHARAOH.ASSET_GEN.FORCE_STATIC": "True"})
def test_generate_python_plotly_asset_static(new_proj):
    new_proj.load_settings("env")
    assert new_proj.get_setting("asset_gen.force_static", True)

    generate_assets(new_proj.project_root, example_assets / "plotly_plot.py")
    files = list(new_proj.asset_build_dir.glob("*"))
    assert len(files) == 4
    assert_file_exists(files, r"iris_scatter1_.*.svg")
    assert_file_exists(files, r"iris_scatter2_.*.png")
    assert_assetinfo_file_exists(files, r"iris_scatter1_.*.assetinfo")
    assert_assetinfo_file_exists(files, r"iris_scatter2_.*.assetinfo")


def test_generate_python_holoviews_asset(new_proj):
    generate_assets(new_proj.project_root, example_assets / "holoviews_plot.py")
    files = list(new_proj.asset_build_dir.glob("*"))
    assert len(files) == 14
    assert_file_exists(files, r"heatmap_holo_plotly_.*.html")
    assert_file_exists(files, r"heatmap_holo_plotly_.*.svg")
    assert_file_exists(files, r"heatmap_holo_plotly_.*.png")
    assert_file_exists(files, r"heatmap_holo_bokeh_.*.html")
    assert_file_exists(files, r"heatmap_holo_bokeh_.*.png")
    assert_file_exists(files, r"heatmap_holo_mpl_.*.svg")
    assert_file_exists(files, r"heatmap_holo_mpl_.*.png")


@mock.patch.dict(os.environ, {"PHARAOH.ASSET_GEN.FORCE_STATIC": "True"})
def test_generate_python_holoviews_asset_static(new_proj):
    new_proj.load_settings("env")
    assert new_proj.get_setting("asset_gen.force_static", True)

    generate_assets(new_proj.project_root, example_assets / "holoviews_plot.py")
    files = list(new_proj.asset_build_dir.glob("*"))
    assert len(files) == 14
    assert_file_exists(files, r"heatmap_holo_plotly_.*.png")
    assert_file_exists(files, r"heatmap_holo_bokeh_.*.png")
    assert_file_exists(files, r"heatmap_holo_mpl_.*.png")
    html_files = list(new_proj.asset_build_dir.glob("*.html"))
    assert not len(html_files)


def test_generate_python_matplotlib_asset(new_proj):
    generate_assets(new_proj.project_root, example_assets / "matplotlib_plot.py")
    files = list(new_proj.asset_build_dir.glob("*"))
    assert len(files) == 4
    assert_file_exists(files, r"coherence_.*.png")
    assert_file_exists(files, r"coherence_.*.svg")
    assert_assetinfo_file_exists(files, r"coherence_.*.assetinfo")


def test_generate_python_pandas_asset(new_proj):
    generate_assets(new_proj.project_root, example_assets / "pandas_table.py")
    files = list(new_proj.asset_build_dir.glob("*"))
    assert len(files) == 2
    assert_file_exists(files, r"challenge_rating_.*.html")
    assert_assetinfo_file_exists(files, r"challenge_rating_.*.assetinfo")


def test_generate_ipynb_asset(new_proj):
    generate_assets(new_proj.project_root, example_assets / "bokeh_plot.ipynb")
    files = list(new_proj.asset_build_dir.glob("*"))
    assert_file_exists(files, r"iris_scatter_bokeh_1_.*.html")
    assert_file_exists(files, r"iris_scatter_bokeh_2_.*.png")
    assert_file_exists(files, r"iris_scatter_bokeh_3_.*.svg")
    assert_assetinfo_file_exists(files, r"iris_scatter_bokeh_.*.assetinfo")


def test_generate_failing_python_asset(new_proj):
    with pytest.raises(Exception, match=".*failing.py"):
        generate_assets(new_proj.project_root, example_assets / "failing.py")


def test_generate_failing_ipynb_asset(new_proj):
    with pytest.raises(Exception, match=".*failing.ipynb"):
        generate_assets(new_proj.project_root, example_assets / "failing.ipynb")
    files = list(new_proj.asset_build_dir.rglob("*.ipynb"))
    assert len(files) == 1
    assert "failed_notebooks" in files[0].parts
    assert files[0].name == "failing.ipynb"


def test_register_assets(new_proj):
    generate_assets(new_proj.project_root, example_assets / "manual_register.py")
    files = list(new_proj.asset_build_dir.glob("dummy/*"))
    assert len(files) == 6
    assert_file_exists(files, r"raw_.*.html")
    assert_file_exists(files, r"raw_.*.rst")
    assert_file_exists(files, r"raw_.*.txt")
    assert_assetinfo_file_exists(files, r"raw_.*.assetinfo")


def test_parallel_asset_generation(new_proj):
    results = generate_assets_parallel(
        new_proj.project_root,
        (
            ("", example_assets / "matplotlib_plot.py"),
            ("", example_assets / "bokeh_plot.py"),
            ("", example_assets / "plotly_plot.py"),
            ("", example_assets / "holoviews_plot.py"),
            ("", example_assets / "pandas_table.py"),
            ("", example_assets / "bokeh_plot.ipynb"),
            ("", example_assets / "failing.py"),
            ("", example_assets / "failing.ipynb"),
        ),
        workers=1,
    )
    fails = [ex for _, ex in results if ex is not None]
    assert any("failing.py" in str(ex) for ex in fails)
    assert any("failing.ipynb" in str(ex) for ex in fails)
    for fail in fails:
        print(fail)
    assert len(fails) == 2

    files = sorted(new_proj.asset_build_dir.glob("*"))
    assert len(sorted(new_proj.asset_build_dir.glob("*.assetinfo"))) == 18
    assert len(files) == 38
    # os.system(f'explorer.exe "{tmp_app.asset_build_dir}"')


def test_regenerate_assets_partially(new_proj):
    """
    Test if the "components" directive option properly limits the found assets to the invoking component
    """
    new_proj.add_component("dummy_1", "pharaoh_testing.simple", {"test_name": "Dummy 1"})
    new_proj.add_component("dummy_2", "pharaoh_testing.simple", {"test_name": "Dummy 2"})
    new_proj.generate_assets()
    assets = new_proj.asset_finder.discover_assets()
    dummy_1_assets = assets["dummy_1"]
    dummy_2_assets = assets["dummy_2"]
    new_proj.generate_assets(("dummy_1",))
    assets = new_proj.asset_finder.discover_assets()
    dummy_1_assets_new = assets["dummy_1"]
    dummy_2_assets_new = assets["dummy_2"]

    assert dummy_1_assets[0].context.asset.stem != dummy_1_assets_new[0].context.asset.stem
    assert dummy_2_assets[0].context.asset.stem == dummy_2_assets_new[0].context.asset.stem
    assert len(dummy_1_assets) == len(dummy_2_assets) == len(dummy_1_assets_new) == len(dummy_2_assets_new)

    if platform.system() == "Windows":
        with open(dummy_2_assets[0].context.asset.file), pytest.raises(PermissionError):
            # block file from deletion to enforce error
            new_proj.generate_assets(("dummy_2",))


def test_execute_asset_script_directly(new_proj):
    new_proj.add_component(
        "dummy_1",
        "pharaoh_testing.direct_asset_script_execution",
        metadata={"foo": "bar"},
        resources=[FileResource(alias="dummy_resource", pattern=".*")],
    )
    asset_py = new_proj.sphinx_report_project_components / "dummy_1" / "asset_scripts" / "assets.py"
    p = sp.Popen(args=[sys.executable, asset_py], stderr=sp.PIPE, stdout=sp.PIPE, cwd=asset_py.parent, text=True)
    out, err = p.communicate()
    if p.returncode != 0:
        raise RuntimeError(err)


def test_register_templating_context_by_data(new_proj):
    register_templating_context("foo", context={"foo": "bar"}, component="bla")
    assets = new_proj.asset_finder.discover_assets(components=["bla"])

    assert len(assets["bla"]) == 1
    asset = assets["bla"][0]
    assert "pharaoh_templating_context" in asset.context
    content = asset.read_json()
    assert content == {"foo": "bar"}


def test_register_templating_context_by_json_file(new_proj):
    asset = new_proj.project_root / "context.json"
    asset.write_text(json.dumps({"foo": "bar"}))

    register_templating_context("foo", context=asset, component="bla")
    assets = new_proj.asset_finder.discover_assets(components=["bla"])

    assert len(assets["bla"]) == 1
    asset = assets["bla"][0]
    assert "pharaoh_templating_context" in asset.context
    content = asset.read_json()
    assert content == {"foo": "bar"}
