from __future__ import annotations

import builtins
from typing import Any

import attrs


def str2type(value: str) -> type:
    if isinstance(value, type):
        return value
    if not hasattr(builtins, value):
        msg = f"{value!r} is not a builtin type!"
        raise ValueError(msg)
    item = getattr(builtins, value)
    if not isinstance(item, type):
        msg = f"{value!r} is not a builtin type!"
        raise ValueError(msg)
    return item


@attrs.define(frozen=True)
class ContextVar:
    """
    Declares a context variable for a first-level template.

    :ivar str name: The name of the context variable
    :ivar type type: Its type
    :ivar default: Its default value
    :ivar bool req: If it's required or not
    :ivar str desc: Its description
    """

    name: str = attrs.field(validator=attrs.validators.instance_of(str))
    type: type = attrs.field(validator=attrs.validators.instance_of(type), converter=str2type)
    default: Any = attrs.field()
    req: bool = attrs.field(validator=attrs.validators.instance_of(bool), default=True)
    desc: str = attrs.field(validator=attrs.validators.instance_of(str), default="")
