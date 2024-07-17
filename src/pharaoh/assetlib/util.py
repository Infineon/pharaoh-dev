from __future__ import annotations

import collections
import importlib
import inspect
from pathlib import Path
from typing import TYPE_CHECKING, Callable, TypeVar

if TYPE_CHECKING:
    from collections.abc import Iterable


def parse_signature(obj: str | Callable, args: tuple = (), kwargs: dict | None = None, fromclass: bool = False) -> dict:
    """
    Parses the signature of a function or method and returns a dictionary mapping parameter names to their values.

    This function dynamically imports the specified function or method based on its fully qualified name and then
    parses its signature. It supports both standalone functions and class methods. For class methods, the `fromclass`
    parameter must be set to True. The function or method's parameters are then mapped to their respective values
    based on the provided `args` and `kwargs`, with priority given to `args`.

    :param obj: The fully qualified name of the function or method as a string, or the function/method object itself.
    :param args: A tuple of positional arguments that are passed to the function or method.
    :param kwargs: A dictionary of keyword arguments that are passed to the function or method.
    :param fromclass: A boolean indicating whether the specified function is a method of a class. If True,
      `obj` is expected to be in the format "module.class.function". If False, `obj` is expected to be in the format
      "module.function".
    :returns: A dictionary mapping parameter names to their values as determined by the provided `args` and `kwargs`.
    """
    kwargs = kwargs or {}
    if isinstance(obj, str):
        if fromclass:
            module_name, class_name, function_name = obj.rsplit(".", maxsplit=2)
            mod = importlib.import_module(module_name)
            fun = getattr(getattr(mod, class_name), function_name)
        else:
            module_name, function_name = obj.rsplit(".", maxsplit=1)
            mod = importlib.import_module(module_name)
            fun = getattr(mod, function_name)
    else:
        fun = obj
    signature = inspect.signature(fun)
    mapping = {}
    for i, (pname, parameter) in enumerate(dict(signature.parameters).items()):
        default = None if parameter.default is inspect.Parameter.empty else parameter.default
        try:
            value = args[i]
        except IndexError:
            value = kwargs.get(pname, default)
        mapping[pname] = value
    return mapping


def get_component_name_by_callstack(components_directory: Path) -> str:
    stack = inspect.stack()
    for frame in stack:
        try:
            parts = Path(frame.filename).relative_to(components_directory).parts
        except ValueError:
            continue
        if len(parts) < 2:
            continue
        return parts[0]

    msg = "Current method was not executed from inside a component"
    raise LookupError(msg)


def is_relative_to(path: Path, other):
    """Return True if the path is relative to another path or False."""
    # Reimplement here since it was first added in Python 3.9's pathlib
    try:
        path.relative_to(other)
        return True
    except ValueError:
        return False


def dotted_getattr(obj: object, key: str):
    """
    Access any attribute using a dot-notation::

        dotted_getattr(obj, "a.b.c")  # returns obj.a.b.c

    """
    if not isinstance(key, str):
        msg = "Only strings allowed!"
        raise TypeError(msg)
    subkeys = key.split(".")
    for subkey in subkeys:
        obj = getattr(obj, subkey)
    return obj


T = TypeVar("T")


def obj_groupby(
    seq: Iterable[T], key: str, sort_reverse: bool = False, attr: str | None = None, default: str | None = None
) -> dict[str, list[T]]:
    """
    Groups an iterable of objects by a nested attribute.

    :param seq: The iterable of objects to group
    :param key: The nested attribute to use for grouping, e.g. "A.B.C"
    :param sort_reverse: Reverse-sort the keys in the returned dictionary
    :param attr: If omitted, the nested attribute specified by "key" is searched on the items in the input sequence.
                 If given, the nested attribute is searched on a sub-attribute. See examples below::

                    attr: None,  key: "A.B.C", -> obj.A.B.C
                    attr: "A",   key: "B.C",   -> obj.A.B.C
                    attr: "A.B", key: "C",     -> obj.A.B.C

    :param default: If "key" is not an existing attribute, sort the items into this default group.
    :return: A dictionary that maps the group names (values of A.B.C) to a list of items out of the input iterable
    """
    d: dict = collections.defaultdict(lambda: [].append)
    for item in seq:
        accessed_item = item
        if isinstance(attr, str):
            accessed_item = dotted_getattr(item, attr)
        try:
            d[dotted_getattr(accessed_item, key)](item)
        except AttributeError:
            if isinstance(default, str):
                d[default](item)
            else:
                raise

    rv = {}
    for k, v in sorted(d.items(), reverse=sort_reverse):
        rv[k] = v.__self__
    return rv
