from __future__ import annotations

import json
from pathlib import Path

import pytest

from pharaoh.assetlib.context import MetadataContextStack
from pharaoh.assetlib.generation import generate_assets

example_assets = Path(__file__).with_name("_example_assets")


def test_merge_stacks():
    stack = MetadataContextStack()
    metadata_context = stack.new_context

    with metadata_context(a=1):
        assert stack.merge_stacks() == {"a": 1}

        with metadata_context(a=2, b=3):
            assert stack.merge_stacks() == {"a": 2, "b": 3}

        with metadata_context(c=4):
            assert stack.merge_stacks() == {"a": 1, "c": 4}

        assert stack.merge_stacks() == {"a": 1}

    assert stack.merge_stacks() == {}


def test_find_context():
    stack = MetadataContextStack()
    metadata_context = stack.new_context

    with pytest.raises(LookupError):
        stack.get_parent_context()

    with metadata_context(context_name="A"):
        assert stack.get_parent_context().name == "A"

        with metadata_context(context_name="B"):
            assert stack.get_parent_context().name == "B"
            assert stack.get_parent_context(index=-2).name == "A"

            with metadata_context(context_name="C"):
                assert stack.get_parent_context().name == "C"
                assert stack.get_parent_context(name="A").name == "A"

                with metadata_context(context_name="D"):
                    assert stack.get_parent_context().name == "D"
                    assert stack.get_parent_context(index=0).name == "A"
                    assert stack.get_parent_context(index=1).name == "B"


def test_metadata_stack(new_proj):
    generate_assets(new_proj.project_root, example_assets / "metadata_stack_example.py")

    files = sorted(new_proj.asset_build_dir.glob("*.assetinfo"))

    def read_json(index: int):
        content = json.loads(files[index].read_text())
        content.pop("asset")  # We don't need it for comparison
        return content

    assert read_json(0) == {"a": 1}
    assert read_json(1) == {"a": 1, "b": 2}
    assert read_json(2) == {"a": 1}
    assert read_json(3) == {"a": 1, "c": 3}
