# mypy: disable-error-code="empty-body"
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
    from pharaoh.sphinx_app import PharaohSphinx

    from .template import L1Template


@_spec
def pharaoh_collect_l1_templates() -> list[L1Template]:
    """
    Collects all first-level templates.

    Example::

        @impl
        def pharaoh_collect_l1_templates():
            return [
                L1Template(
                    name="myorg.default_project",
                    path=Path(__file__).parent / "templates" / "level_1" / "default_project",
                ),
            ]
    """


@_spec
def pharaoh_collect_l2_templates() -> list[PathLike]:
    """
    Collects paths to all second-level template directories.
    """


@_spec
def pharaoh_collect_resource_types() -> list[type[Resource]]:
    """
    Allows registering custom resource types.

    Example::

        @impl
        def pharaoh_collect_resource_types():
            from .resources import RemoteResource

            return [RemoteResource]

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

    Example::

        @impl
        def pharaoh_asset_gen_prepare_resources(project: PharaohProject, resources: dict[str, Resource]):
            from .resources import RemoteResource

            # Transform resources
            for r in resources.values():
                if isinstance(r, RemoteResource):
                    r.download(
                        url=project.get_setting("cloud.url"),
                        auth_credentials=project.get_setting("cloud.auth_credentials", to_container=True) or None,
                    )

    :param project: The Pharaoh project instance
    :param resources: A mapping of all resources that are defined for the current component.
    """


@_spec
def pharaoh_configure_sphinx(project: PharaohProject, config: dict[str, Any], confdir: Path):
    """
    This hook is called at the end of :func:`pharaoh.project.PharaohProject.get_default_sphinx_configuration`
    when Sphinx is reading the ``conf.py`` file.
    It can update the default Sphinx configuration in-place.

    Example::

        @impl
        def pharaoh_configure_sphinx(project: PharaohProject, config: dict, confdir: Path):
            config["extensions"].append("sphinxcontrib.confluencebuilder")
            config["html_style"] = "sphinx_rtd_theme_overrides.css"

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

    Example::

        @impl
        def pharaoh_collect_default_settings():
            return Path(__file__).with_name("my_own_setting.yaml")

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
    This hook is called before a Sphinx build is started.

    :param project: The Pharaoh project instance
    :param builder: The name of the configured builder
    """


@_spec
def pharaoh_sphinx_app_inited(app: PharaohSphinx):
    """
    This hook is after the Sphinx application is initialized.

    :param app: The Pharaoh-specific Sphinx application
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


@_spec
def pharaoh_find_asset_render_template(template_name: str) -> str | Path:
    """
    This hook is called when an asset template is looked up by name and can customize the search behavior.
    Per default the templates in package ``pharaoh.templating.second_level.sphinx_ext.asset_ext_templates`` are used.

    This template is used to include an asset into a Sphinx document, e.g. the template for a picture asset
    may be called ``image.rst.jinja2`` and would be using the ``image`` directive to embed it.
    If found, the path to the template is returned.

    .. seealso:: :ref:`reference/directive:Asset Templates`

    .. note:: The template's file name should end with ``.jinja2``.

    :param template_name: The name of the template
    """


@_spec
def pharaoh_get_asset_render_template_mappings() -> dict[str, str]:
    """
    This hook maps file extensions of assets to names of templates (see hook ``pharaoh_find_asset_render_template``)
    that are used to embed the asset into the Sphinx document.
    The file extension is only taken into account if no ``template`` metadata key is present in the asset's metadata.

    Pharaoh provides a default mapping (see :ref:`reference/directive:Asset Templates`) which may be updated by this
    hook.
    """
