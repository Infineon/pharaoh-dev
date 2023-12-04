from __future__ import annotations

import json
from functools import singledispatch
from pathlib import Path

try:
    import numpy as np

    NUMPY_AVAIL = True
except ImportError:
    NUMPY_AVAIL = False


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        for type_, handler in encode.registry.items():
            if isinstance(obj, type_) and type_ is not object:
                return handler(obj)
        try:
            return super().default(obj)
        except Exception as e:
            print(f"CustomJSONEncoder Error: {e} when trying to encode {obj!r}")
            raise


@singledispatch
def encode(obj, **kwargs):
    return json.dumps(obj, cls=CustomJSONEncoder, **kwargs)


@encode.register(Path)
def encode_Path(obj):
    """Event-typed object cannot be JSON serialized, so serialize as "null" """
    return str(obj)


if NUMPY_AVAIL:

    @encode.register(np.str_)
    @encode.register(np.bytes_)
    @encode.register(np.bool_)
    @encode.register(np.number)
    def encode_numpy_scalars(obj):
        return obj.item()

    @encode.register(np.ndarray)
    def encode_numpy_arrays(obj):
        return obj.tolist()


def encode_dict(obj, **kwargs):
    return json.loads(encode_json(obj, **kwargs))


def encode_json(obj, **kwargs):
    return json.dumps(obj, cls=CustomJSONEncoder, **kwargs)
