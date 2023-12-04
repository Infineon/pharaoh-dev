from __future__ import annotations

import json
from pathlib import Path

import pytest

from pharaoh.assetlib.resource import CustomResource, FileResource

example_assets = Path(__file__).with_name("_example_assets")


def test_resources_serialization():
    spec = {"__class__": "FileResource", "alias": "bla", "pattern": __file__, "sort": "descending"}
    r = FileResource.from_dict(spec)
    assert isinstance(r, FileResource)
    assert r.to_dict() == spec

    r = FileResource.from_dict(
        {
            "__class__": "FileResource",
            "alias": "blubb",
            "sort": "descending",
            "pattern": r"*",
        }
    )
    assert isinstance(r, FileResource)
    assert r.to_dict() == {"pattern": "*", "sort": "descending", "alias": "blubb", "__class__": "FileResource"}
    _ = r.get_files()


def test_resources_lookup(new_proj):
    new_proj.add_component(
        "dummy_1",
        "pharaoh_testing.complex",
        {"test_name": "Dummy 1"},
        resources=[FileResource(alias="myfile", pattern=__file__)],
    )
    r = new_proj.get_resource("myfile", "dummy_1")
    assert isinstance(r, FileResource)
    assert r.locate() == Path(__file__)

    with pytest.raises(LookupError, match="Cannot find resource"):
        new_proj.get_resource("NA", "dummy_1")

    with pytest.raises(LookupError, match="does not exist"):
        new_proj.get_resource("", "dummy_123")


def test_resources_update(new_proj):
    new_proj.add_component(
        "dummy_1",
        "pharaoh_testing.simple",
        {"test_name": "Dummy 1"},
        resources=[FileResource(alias="myfoo", pattern="foo")],
    )
    new_proj.update_resource(alias="myfoo", component="dummy_1", resource=FileResource(alias="mybar", pattern="bar"))
    with pytest.raises(LookupError):
        new_proj.get_resource(alias="myfoo", component="dummy_1")
    assert new_proj._project_settings.components[0].resources[0].alias == "mybar"
    assert new_proj._project_settings.components[0].resources[0].pattern == "bar"

    new_proj.update_resource(alias="myfoo", component="dummy_1", resource=FileResource(alias="myfoo", pattern="foo"))
    assert len(new_proj._project_settings.components[0].resources) == 2
    assert new_proj._project_settings.components[0].resources[0].alias == "mybar"
    assert new_proj._project_settings.components[0].resources[0].pattern == "bar"
    assert new_proj._project_settings.components[0].resources[1].alias == "myfoo"
    assert new_proj._project_settings.components[0].resources[1].pattern == "foo"

    with pytest.raises(LookupError):
        new_proj.update_resource(
            alias="myfoo", component="not a component", resource=FileResource(alias="myfoo", pattern="foo")
        )


def test_file_resource_sorting(tmp_path):
    (tmp_path / "files").mkdir()
    (tmp_path / "files" / "0_file.txt").touch()
    (tmp_path / "files" / "01_file.txt").touch()
    (tmp_path / "files" / "1_file.txt").touch()
    (tmp_path / "files" / "2_file.txt").touch()
    (tmp_path / "files" / "10_file.txt").touch()

    fr_asc = FileResource(alias="myfile", pattern=tmp_path / "*" / "*.txt", sort="ascending")
    fr_des = FileResource(alias="myfile", pattern=tmp_path / "*" / "*.txt", sort="descending")

    def get_numbers(files):
        return [file.stem.split("_")[0] for file in files]

    assert get_numbers(fr_asc.get_files()) == ["0", "01", "1", "2", "10"]
    assert get_numbers(fr_des.get_files()) == ["10", "2", "01", "1", "0"]


def test_execute_asset_script_that_needs_resources(new_proj):
    dummy_resource = new_proj.project_root / "dummy_resource.txt"
    dummy_resource.write_text("This is a dummy resource!")

    new_proj.add_component(
        "dummy_1",
        "pharaoh_testing.complex",
        {"test_name": "Dummy 1"},
        resources=[FileResource(alias="dummy_resource", pattern=dummy_resource)],
    )

    new_proj.generate_assets()
    next(new_proj.asset_build_dir.glob("dummy_1/dummy_resource*.txt"))
    info_file = next(new_proj.asset_build_dir.glob("dummy_1/dummy_resource*.assetinfo"))

    info = json.loads(info_file.read_text())
    assert info["label"] == "RESOURCE_ACCESS"
    assert info["asset"]["script_name"] == "access_resources.py"


def test_transformed_resource(tmp_path):
    # todo
    ...
    # t = PassFinderResource(alias="foo", sources=["bar"])
    # with pytest.raises(AssertionError):
    #     t.locate()
    # t._cachedir = str(tmp_path)
    # t.transform(resources={"bar": FileResource(alias="bar", pattern=str(example_data / "dummy_test.dlh5"))})
    #
    # passfinder_report = t.locate()
    #
    # with open(passfinder_report) as fp:
    #     content = json.load(fp)
    # assert len(content["parameters"]) == 24
    # assert len(content["specs"]) == 9
    #
    # ct1 = t.locate().stat().st_ctime_ns
    # t.transform(resources={"bar": FileResource(alias="bar", pattern=str(example_data / "dummy_test.dlh5"))})
    # ct2 = t.locate().stat().st_ctime_ns
    # assert ct1 == ct2


def test_custom_resource(tmp_path):
    traits = {"a": 1, "b": [2, 3], "c": {"d": [4, 5]}}
    r = CustomResource(alias="foo", traits=traits)

    serialized = r.to_dict()

    r2: CustomResource = CustomResource.from_dict(serialized)
    assert r2.traits == traits
