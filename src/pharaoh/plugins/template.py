from __future__ import annotations

from pathlib import Path

import attrs

from pharaoh.plugins.contextvar import ContextVar

is_str = attrs.validators.instance_of(str)
is_str_or_path = attrs.validators.instance_of((str, Path))
is_bool = attrs.validators.instance_of(str)


def check_exists(obj, attr, value: str):
    path = Path(value)
    if not path.exists():
        msg = f"Template path {path.as_posix()} does not exist!"
        raise FileNotFoundError(msg)


@attrs.define
class L1Template:
    """
    Declares a level-1/generation-time template.

    :ivar str name: The template's name. Used for referencing: ``<plugin-name>.<template-name>``
    :ivar str|Path path: The path to the template directory
    :ivar list[str] needs: A list of templates this template depends on.
        E.g. ["plugin_abc.template_xyz"]. Pharaoh uses this information to verify if all dependent templates are at least
        used once by any component.
    :ivar list[ContextVar] vars: A list of required context variables and their potential defaults.
    """

    name: str = attrs.field(validator=is_str)
    path: str | Path = attrs.field(converter=Path, validator=check_exists)
    needs: list[str] = attrs.field(validator=attrs.validators.deep_iterable(is_str), factory=list)
    vars: list[ContextVar] = attrs.field(
        validator=attrs.validators.deep_iterable(attrs.validators.instance_of(ContextVar)), factory=list
    )
