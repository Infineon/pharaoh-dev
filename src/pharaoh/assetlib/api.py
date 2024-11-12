# flake8: noqa: F401,F403
"""
This module contains API functions related to asset generation.
When asset scripts are accessing those API functions, the functions can access the project information by themselves.
"""

# Don't remove unused imports. They may be unused here but maybe in user code!
from __future__ import annotations

from typing import TYPE_CHECKING

from pharaoh.assetlib.catch_exceptions import catch_exceptions
from pharaoh.assetlib.context import metadata_context
from pharaoh.assetlib.generation import register_asset, register_templating_context
from pharaoh.assetlib.matlab_engine import Matlab
from pharaoh.assetlib.resource import *

if TYPE_CHECKING:
    from pharaoh.assetlib.finder import AssetFinder


def __get_pharaoh_project():
    import inspect
    from pathlib import Path

    import pharaoh
    from pharaoh.project import get_project

    from .util import is_relative_to

    try:
        return get_project()
    except RuntimeError:
        pass

    pharaoh_src = Path(pharaoh.__file__).parents[1]  # also works for site-packages
    # todo: maybe we have to consider additional paths

    # Find the first frame whose filename is not inside the pharaoh library
    for frame in inspect.stack():
        fname = Path(frame.filename)
        if is_relative_to(fname, pharaoh_src) or "/pharaoh_contrib/" in fname.as_posix():
            continue
        return get_project(Path(frame.filename))
    return None


def get_resource(alias: str, component: str | None = None):
    """
    Get a Resource instance by its component name and resource alias.
    """
    proj = __get_pharaoh_project()
    if not component:
        component = get_current_component()
    return proj.get_resource(alias, component)


def find_components(expression: str = ""):
    """
    Find components by their metadata using an evaluated expression.

    The expression must be a valid Python expression and following local variables may be used:

    - name: The name of the component
    - templates: A list of templates used to render the component
    - metadata: A dict of metadata specified
    - render_context: The Jinja rendering context specified
    - resources: A list of resource definitions

    :param expression: A Python expression that will be evaluated. If it evaluates to a truthy result,
       the component name is included in the returned list.

       Example: ``name == "dummy" and metadata.foo in (1,2,3)``.

       A failing evaluation will be treated as False. An empty expression will always match.
    """
    proj = __get_pharaoh_project()
    return proj.find_components(expression)


def get_current_component() -> str:
    """
    If executed from within a script that is placed inside a Pharaoh component, the function returns the components
    name by analyzing the call stack.
    """
    from pharaoh.assetlib import util

    proj = __get_pharaoh_project()
    return util.get_component_name_by_callstack(proj.sphinx_report_project_components)


def get_asset_finder() -> AssetFinder:
    """
    Returns the :class:`AssetFinder <pharaoh.assetlib.finder.AssetFinder>` instance for the current project
    """
    proj = __get_pharaoh_project()
    return proj.asset_finder
