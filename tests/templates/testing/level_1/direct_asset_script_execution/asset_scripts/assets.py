"""
This script is executed by unit test tests.unit.test_asset_generation.test_execute_asset_script_directly
directly via a subprocess to simulate the user debugging the asset script directly in an IDE outside of Pharaoh asset
generation.
"""
import tempfile
from pathlib import Path

from pharaoh.api import get_project
from pharaoh.assetlib.api import (
    find_components,
    get_asset_finder,
    get_current_component,
    get_resource,
    metadata_context,
    register_asset,
)

try:
    get_project()
    msg = "First call to get_project must fail with a RuntimeError, since the project singleton is not created yet!"
    raise Exception(msg)
except RuntimeError:
    pass

# This will first of all find the Pharaoh project it's executed in and creates a global Pharaoh project singleton
# that can be accessed via get_project()
current_component = get_current_component()

# Now the singleton is set and can be accessed
project = get_project()

component_names = [comp.name for comp in find_components("metadata.foo == 'bar'")]
assert [current_component] == component_names

with metadata_context(label="baz"), tempfile.TemporaryDirectory() as tdir:
    asset = Path(tdir) / "my_asset.txt"
    asset.touch()
    register_asset(asset, metadata={"bla": "blubb"})

finder = get_asset_finder()
discovered_assets = finder.discover_assets()
assert "dummy_1" in discovered_assets
context = discovered_assets["dummy_1"][0].context
assert context.bla == "blubb"
assert context.label == "baz"

resource = get_resource(alias="dummy_resource")
assert resource.alias == "dummy_resource"
