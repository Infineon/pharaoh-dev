from pharaoh.assetlib.api import get_resource, register_asset

try:
    # Not all unittests will add the required resource
    r = get_resource("dummy_resource", "dummy_1")
    register_asset(r.locate(), {"label": "RESOURCE_ACCESS"})
except LookupError:
    pass
