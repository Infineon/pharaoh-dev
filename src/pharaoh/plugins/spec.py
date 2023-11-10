from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

import pluggy

from . import NAME

_spec = pluggy.HookspecMarker(NAME)
PathLike = Union[str, Path]

if TYPE_CHECKING:
    from types import TracebackType

    import click

    from pharaoh.api import PharaohProject, Resource

    from .template import L1Template


@_spec
def pharaoh_collect_l1_templates() -> list[L1Template]:
    """
    Collects all first-level templates.
    """


@_spec
def pharaoh_collect_l2_templates() -> list[PathLike]:
    """
    Collects paths to all second-level template directories.
    """


@_spec
def pharaoh_collect_resource_types() -> list[type[Resource]]:
    """
    Collects resource types
    """


@_spec
def pharaoh_asset_gen_started(project: PharaohProject):
    """
    This hook is called when the asset generation is executed.

    :param project: The Pharaoh project instance
    """


@_spec
def pharaoh_asset_gen_prepare_resources(project: PharaohProject, resources: dict[str, Resource]):
    """
    This hook is called before asset generation for each component that is selected.

    :param project: The Pharaoh project instance
    :param resources: A mapping of all resources that are defined for the current component.
    """


@_spec
def pharaoh_configure_sphinx(project: PharaohProject, config: dict[str, Any], confdir: Path):
    """
    This hook is called at the end of :func:`pharaoh.project.PharaohProject.get_default_sphinx_configuration`
    when Sphinx is reading the ``conf.py`` file.
    It can update the default Sphinx configuration in-place.

    :param project: The Pharaoh project instance
    :param config: The default Sphinx config defined by Pharaoh.
    :param confdir: The parent directory of conf.py
    """


@_spec
def pharaoh_collect_default_settings() -> Path | dict:
    """
    This hook is called when scaffolding a new Pharaoh project.
    It collects all default settings either as a path to a YAML file or a dictionary.
    The collected results are loaded into ``omegaconf.dictconfig.DictConfig`` instances
    and merged in the same order as they are collected (first discovered may get overwritten,
    last discovered always wins).

    :return: A path to a YAML file or a dictionary
    """


@_spec
def pharaoh_add_cli_commands(cli: click.Group):
    """
    This hook is called after all click CLI commands have been added to add you own CLI commands.
    Example::

        from pharaoh.plugins.api import impl

        @impl
        def pharaoh_add_cli_commands(cli: click.Group):
            @cli.command()
            @click.pass_context
            def my_cli_command(ctx):
                project = ctx.obj["project"]
                project.do_something
    """


@_spec
def pharaoh_build_started(project: PharaohProject, builder: str):
    """
    This hook is when a Sphinx build is started.

    :param project: The Pharaoh project instance
    :param builder: The name of the configured builder
    """


@_spec
def pharaoh_build_finished(
    project: PharaohProject, exc_info: tuple[type[BaseException], BaseException, TracebackType] | None
):
    """
    This hook is called after a Sphinx build ended with or without error.

    :param project: The Pharaoh project instance
    :param exc_info: An optional value that is returned by sys.exc_info() in case the build raised an Exception.
    """


@_spec
def pharaoh_modify_gitignore(gitignore_lines: list[str]):
    """
    This hook can be used to modify the content on the .gitignore file that is included in the generated Pharaoh
    project inplace.

    :param gitignore_lines: A list of lines to add to the .gitignore file
    """


@_spec
def pharaoh_project_created(project: PharaohProject):
    """
    This hook is called whenever a Pharaoh report has been generated

    :param project: The Pharaoh project instance
    """
