import json
import os
from pathlib import Path

import omegaconf
import pytest

from pharaoh.assetlib.finder import Asset, AssetFileLinkBrokenError, AssetFinder, obj_groupby
from pharaoh.templating.second_level.env_filters import oc_get


def create_asset(basedir: Path, name: str, **context) -> Asset:
    info = basedir / f"{name}.assetinfo"
    info.write_text(json.dumps(context))
    asset = basedir / f"{name}.txt"
    asset.write_text("foo")
    return Asset(info)


@pytest.fixture()
def dummy_assetdir(tmp_path):
    assetdir = tmp_path / "assets"
    component_dir = assetdir / "component_xyz"
    component_dir.mkdir(exist_ok=True, parents=True)
    create_asset(component_dir, "a", a=1, b=2, d={"e": 4, "f": 5})
    create_asset(component_dir, "b", a=1, c=3, d={"e": 5, "f": 6})
    return assetdir


def test_asset_discover(dummy_assetdir):
    al = AssetFinder(dummy_assetdir)
    assets = al.discover_assets()
    assert assets["component_xyz"][0].context == {"a": 1, "b": 2, "d": {"e": 4, "f": 5}}
    assert assets["component_xyz"][1].context == {"a": 1, "c": 3, "d": {"e": 5, "f": 6}}

    # Test broken links
    os.remove(assets["component_xyz"][0].assetfile)
    with pytest.raises(AssetFileLinkBrokenError):
        al.discover_assets()


def test_asset_copy(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    dst1 = tmp_path / "dst1"
    dst2 = tmp_path / "dst2"

    asset1_info = src / "asset1.assetinfo"
    asset1_info.write_text(json.dumps({"name": "asset1"}))
    asset1_file = src / "asset1.txt"
    asset1_file.touch()
    asset1 = Asset(asset1_info)

    asset2_info = src / "asset2.assetinfo"
    asset2_info.write_text(json.dumps({"name": "asset2"}))
    asset2_file = src / "asset2"
    asset2_file.mkdir()
    (asset2_file / "readme.txt").touch()
    asset2 = Asset(asset2_info)

    asset_path = asset1.copy_to(dst1)
    assert asset_path.exists()
    assert asset1.copy_to(dst1) == asset_path
    assert len(list(dst1.glob("*"))) == 2

    asset_path = asset2.copy_to(dst2)
    assert asset_path.exists()
    assert asset2.copy_to(dst2) == asset_path
    assert len(list(dst2.rglob("*"))) == 3


def test_asset_search(dummy_assetdir):
    al = AssetFinder(dummy_assetdir)
    results = al.search_assets("a == 1")
    assert len(results) == 2
    results = al.search_assets("a == 2")
    assert not len(results)
    results = al.search_assets("a == 1 and b == 2")
    assert results[0].infofile.stem == "a"
    results = al.search_assets("c == 3")
    assert results[0].infofile.stem == "b"
    results = al.search_assets("d.e == 5")
    assert results[0].infofile.stem == "b"

    asset = al.get_asset_by_id(id=results[0].id)
    assert asset.id == results[0].id


def test_obj_groupby():
    persons = [
        omegaconf.OmegaConf.create({"name": "Charlie", "stats": {"gender": "M"}}),
        omegaconf.OmegaConf.create({"name": "Alice", "stats": {"gender": "F"}}),
        omegaconf.OmegaConf.create({"name": "Bob", "stats": {"gender": "M"}}),
    ]
    gr = obj_groupby(persons, "stats.gender")
    assert "F" in gr
    assert "M" in gr
    assert gr["M"][0]["name"] == "Charlie"
    assert gr["M"][1]["name"] == "Bob"

    gr = obj_groupby(persons, "name")
    assert set(gr.keys()) == {"Alice", "Bob", "Charlie"}

    gr = obj_groupby(persons, "foo", default="bar")
    assert set(gr.keys()) == {"bar"}
    assert len(gr["bar"]) == 3

    persons = [
        omegaconf.OmegaConf.create({"name": "Charlie", "stats": {"gender": "M"}}),
        omegaconf.OmegaConf.create({"name": "Alice", "stats": {"gender": "F"}}),
        omegaconf.OmegaConf.create({"name": "Bob", "stats": {"customgender": "Q"}}),
    ]
    gr = obj_groupby(persons, "stats.gender", default="default")
    assert set(gr.keys()) == {"F", "M", "default"}


def test_oc_get():
    d = omegaconf.OmegaConf.create({"a": 1, "c": 3, "d": {"e": 5, "f": 6}})

    assert oc_get(d, "a", None) == 1
    assert oc_get(d, "d.e", None) == 5
    assert oc_get(d, "x", None) is None
    with pytest.raises(AttributeError):
        assert oc_get(d, "x")
