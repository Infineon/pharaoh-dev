from pharaoh.assetlib.api import metadata_context, catch_exceptions

with metadata_context(label="errors"):
    with catch_exceptions():
        raise ValueError("This is a ValueError")

    with catch_exceptions(msg_prefix="Asset Generation Error: "):
        raise TypeError("This is a TypeError")
