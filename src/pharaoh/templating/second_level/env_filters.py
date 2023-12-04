from __future__ import annotations

from pathlib import Path

import omegaconf
from jinja2.exceptions import UndefinedError
from jinja2.utils import is_undefined

DEFAULT = object()


def required(value):
    """
    Raises an UndefinedError if the context variable is undefined.
    The actual name of the Jinja global function is ``req``.

    Example::

        {{ h1(ctx.local.test.test_name|req) }}
    """
    if is_undefined(value):
        raise UndefinedError
    return value


def rep(value) -> str:
    """
    Returns ``repr(value)``. The actual name of the Jinja global function is ``repr``.
    """
    return repr(value)


def or_default(value, default):
    """
    Returns the result of ``value or default``.

    Alias: ``or_d``
    """
    return value or default


def oc_resolve(value: omegaconf.DictConfig):
    """
    Recursively converts an OmegaConf config to a primitive container (dict or list) and returns it.
    """
    conf = value.copy()
    return omegaconf.OmegaConf.to_container(conf, resolve=True)


def oc_get(cfg: omegaconf.DictConfig, key, default=DEFAULT):
    """
    Returns an object inside an omegaconf.DictConfig container.
    If the object does not exist, the default is returned.

    Example::

        {% set plot_title = asset.context|oc_get("plot.title", "") %}

    :param cfg: The omegaconf.DictConfig container to search
    :param key: The name of the object to extract, e.g. ``plot.title``.
    :param default: The default to return if key is not in cfg
    """
    try:
        obj = cfg
        for k in key.split("."):
            ret = getattr(obj, k)
            obj = ret
        return ret
    except Exception:
        if default is DEFAULT:
            msg = f"Not attribute {key} in {cfg}!"
            raise AttributeError(msg) from None
        return default


def exists(path: str) -> bool:
    """
    Returns if path exists.
    """
    return Path(path).exists()


def to_path(path: str) -> Path:
    """
    Returns path as a pathlib.Path instance.
    """
    return Path(path)


def hasattr_(obj, name):
    _hasattr = hasattr(obj, name)
    _haskey = False
    if isinstance(obj, (dict, omegaconf.DictConfig)):
        _haskey = name in obj
    return _hasattr or _haskey


def md2html(text):
    """
    Converts the Markdown text (CommonMark syntax) to HTML.
    """
    import mistletoe

    return mistletoe.markdown(text)


env_filters = {
    "hasattr": hasattr_,
    "req": required,
    "repr": rep,
    "or_d": or_default,
    "or_default": or_default,
    "oc_resolve": oc_resolve,
    "oc_get": oc_get,
    "bool": bool,
    "exists": exists,
    "to_path": to_path,
    "md2html": md2html,
}

# Only document the functions defined in here
to_document = {
    k: func for k, func in env_filters.items() if hasattr(func, "__module__") and func.__module__ == __name__
}
