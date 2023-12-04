from __future__ import annotations

import ast
import os
import platform
from pathlib import Path

import click

from pharaoh.plugins.plugin_manager import PM

if "PHARAOH.LOGGING.LEVEL" not in os.environ:
    os.environ["PHARAOH.LOGGING.LEVEL"] = "INFO"


def parse_dict(ctx, param, value) -> dict:
    """
    Parses a string with dict notation into a dict object using ast.literal_eval
    """
    if not value:
        return {}
    try:
        obj = ast.literal_eval(value)
    except Exception as e:
        msg = f"Not a valid Python expression {value!r}! Error: {e}!"
        raise click.BadParameter(msg) from None
    if not isinstance(obj, dict):
        msg = "Not a valid dict!"
        raise click.BadParameter(msg)
    return obj


def parse_obj(ctx, param, value):
    """
    Parses a string with into a Python object using ast.literal_eval
    """
    if not value:
        return None
    try:
        obj = ast.literal_eval(value)
    except Exception:
        obj = str(value)
    return obj


def parse_resources(ctx, param, value):
    from pharaoh.assetlib import resource
    from pharaoh.plugins.plugin_manager import PM

    if not value:
        return []
    if not isinstance(value, (list, tuple)):
        value = [value]

    eval_context = PM.pharaoh_collect_resource_types()
    resources = []
    for descriptor in value:
        rsrc = eval(descriptor, {}, eval_context)
        if not isinstance(rsrc, resource.Resource):
            msg = f"{value} did not evaluate to a valid Resource type, but instead to {rsrc!r}!"
            raise TypeError(msg)
        resources.append(rsrc)
    return resources


@click.group(chain=True, name="pharaoh")
@click.option(
    "-p",
    "--path",
    default=".",
    type=click.Path(resolve_path=True, path_type=Path),
    help="The path to the Pharaoh report directory (contains pharaoh.yaml) or the path to "
    "pharaoh.yaml itself. If omitted, the current working directory is used.",
)
@click.pass_context
def cli(ctx, path: Path | None):
    """
    Pharaoh Commandline Interface.

    Usage examples:

    \b
        pharaoh new -t pharaoh_testing.simple -c "{'a': 1}" --settings ../my_settings.yaml
        pharaoh add -n dummy1 -t pharaoh_testing.simple -c "{'test_name':'dummy'}"
        pharaoh generate
        pharaoh build
        pharaoh archive

    Multi-command chaining is also possible (all on one line):

    \b
        pharaoh new add --name dummy1 -t pharaoh_testing.simple -c "{'test_name':'dummy1'}"
         add --name dummy2 -t pharaoh_testing.simple -c "{'test_name':'dummy2'}"
         generate build archive -d "archives/myarchive.zip"
    """
    from pharaoh.project import get_project

    ctx.ensure_object(dict)
    ctx.obj["project_path"] = Path(path or os.getcwd())
    try:
        ctx.obj["project"] = get_project(ctx.obj["project_path"])
    except LookupError:
        ctx.obj["project"] = None


@cli.command()
@click.option("-f", "--force", is_flag=True, default=False, help="Force project overwrite if already exists")
@click.option(
    "-t",
    "--template",
    "templates",
    multiple=True,
    default=("pharaoh.default_project",),
    help="The project templates to use for creating the project files.",
)
@click.option("-c", "--context", help="The Jinja rendering context for the selected template. ", callback=parse_dict)
@click.option(
    "-s",
    "--settings",
    help="A path to a YAML file containing settings to overwrite the default project settings.",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True, path_type=Path),
)
@click.pass_context
def new(
    ctx,
    force: bool,
    templates: list[str],
    context: dict,
    settings: Path | None,
):
    """
    Creates a new Pharaoh report skeleton.

    Example:

    \b
        pharaoh new -t pharaoh_testing.simple -c "{'a': 1}" --settings ../my_settings.yaml
    """
    from pharaoh.project import PharaohProject

    kwargs = {
        "project_root": Path(ctx.obj["project_path"]),
        "overwrite": force,
        "template_context": dict(context),
        "custom_settings": settings,
    }
    if len(templates):
        kwargs["templates"] = templates
    if settings:
        kwargs["custom_settings"] = settings

    p = PharaohProject(**kwargs)  # type: ignore[arg-type]
    p.save_settings(include_env=True)
    ctx.obj["project"] = p


@cli.command()
@click.option(
    "-n",
    "--name",
    required=True,
    type=str,
    prompt=True,
    help="The name of the component. Must be a valid Python identifier. ",
)
@click.option(
    "-t",
    "--template",
    "templates",
    multiple=True,
    default=("pharaoh.empty",),
    help="The component templates to use for creating the components project files.",
)
@click.option("-c", "--context", help="The Jinja rendering context for the selected templates.", callback=parse_dict)
@click.option(
    "-m",
    "--metadata",
    help="A dictionary of metadata that may be used to find the components.Enter a valid json string",
    callback=parse_dict,
)
@click.option(
    "-r",
    "--resource",
    "resources",
    multiple=True,
    help="A Python expression that evaluates to a valid object of type Resource.",
    callback=parse_resources,
)
@click.option("-i", "--index", default=-1, help="The index to add the component. Default is -1 with means at the end.")
@click.pass_context
def add(
    ctx,
    name: str,
    templates: list[str],
    context: dict,
    resources: list,
    metadata: dict,
    index: int,
):
    """
    Adds a new component to the Pharaoh project.

    Example:

    \b
        pharaoh add -n dummy1 -t pharaoh_testing.simple -c "{'test_name':'dummy'}"
        pharaoh add -n dummy1 -t pharaoh_testing.simple -r "FileResource(alias='foo', pattern='.*')"
    """
    project = ctx.obj["project"]
    project.add_component(
        component_name=name,
        templates=templates,
        render_context=context,
        resources=resources,
        metadata=metadata,
        index=index,
    )


@cli.command()
@click.option(
    "-n",
    "--name",
    required=True,
    type=str,
    prompt=True,
    help="The name of the component. Must be a valid Python identifier. ",
)
@click.option(
    "-a",
    "--alias",
    required=True,
    type=str,
    prompt=True,
    help="The resource alias.",
)
@click.option(
    "-r",
    "--resource",
    "resources",
    help="A Python expression that evaluates to a valid object of type Resource.",
    callback=parse_resources,
)
@click.pass_context
def update_resource(
    ctx,
    name: str,
    alias: str,
    resources,
):
    """
    Updates a Resource from a project component by its alias.

    Examples:

    \b
        pharaoh update-resource -n dummy1 -a foo -r "FileResource(alias='baz', pattern='*')"

    """
    project = ctx.obj["project"]
    project.update_resource(alias=alias, component=name, resource=resources[0])


@cli.command()
@click.option(
    "-n",
    "--name",
    required=True,
    type=str,
    prompt=True,
    help="The name of the component. Must be a valid Python identifier. ",
)
@click.option(
    "-t",
    "--template",
    "templates",
    multiple=True,
    default=("pharaoh.default_project",),
    help="The component templates to use for creating the components project files.",
)
@click.option("-c", "--context", help="The Jinja rendering context for the selected templates.", callback=parse_dict)
@click.pass_context
def add_template(
    ctx,
    name: str,
    templates: list[str],
    context: dict,
):
    """
    Adds additional templates to an existing component, that may overwrite existing files during rendering.

    Example:

    \b
        pharaoh add-template -n dummy1 -t pharaoh_testing.simple -c "{'test_name':'dummy'}"
    """
    project = ctx.obj["project"]
    project.add_template_to_component(component_name=name, templates=templates, render_context=context)


@cli.command()
@click.option(
    "-f",
    "--filter",
    required=True,
    prompt=True,
    type=str,
    help="A case-insensitive component filter. Either a full- or regular expression match, depending on regex option.",
)
@click.option(
    "-r",
    "--regex",
    default=False,
    is_flag=True,
    type=bool,
    help="If True, the filter option will be treated as regular expression. "
    "Components that partially match the regular expression are removed.",
)
@click.pass_context
def remove(
    ctx,
    filter: str,
    regex: bool,
):
    """
    Removes one or multiple existing components.

    If the regular expression (case-insensitive) partially matches the component name.
    To do a full match surround the pattern by ^ and &, e.g. ^my_component&.

    Example:

    \b
        pharaoh remove -f dummy.*
    """
    project = ctx.obj["project"]
    removed = project.remove_component(filter=filter, regex=regex)
    click.echo("Removed components: " + ", ".join(removed))


@cli.command()
@click.argument(
    "key",
    required=True,
    type=str,
)
@click.argument(
    "value",
    required=False,
    default=None,
    type=str,
    callback=parse_obj,
)
@click.pass_context
def env(
    ctx,
    key: str,
    value,
):
    """
    Updates the projects settings.

    Example:

    \b
        pharaoh env foo_A 123               -> foo_a: 123
        pharaoh env foo_B bar               -> foo_b: "bar"
        pharaoh env foo_C "{'baz': 123}"    -> foo_c: {'baz': 123}
        pharaoh env foo_D class             -> foo_d: "class"
        pharaoh env foo_E                   -> foo_e: None

    """
    project = ctx.obj["project"]
    project.put_setting(key, value)
    project.save_settings()


@cli.command()
@click.option(
    "-f",
    "--filter",
    "filters",
    multiple=True,
    type=str,
    help="A list of regular expressions that are matched against each component name. "
    "If a component name matches any of the regular expressions, the component's "
    "assets are regenerated (containing directory will be cleared)",
)
@click.pass_context
def generate(ctx, filters: list[str]):
    """
    Generates assets.
     Either of the entire project or just a selected subset of components.

    Examples:

    \b
        pharaoh generate
        pharaoh generate -f dummy[12]
        pharaoh generate -f dummy1 -f dummy2
    """
    project = ctx.obj["project"]
    if filters:
        project.generate_assets(filters)
    else:
        project.generate_assets()


@cli.command()
@click.pass_context
def build(ctx):
    """
    Executes report generation for the current project.

    Examples:

    \b
        pharaoh build
        pharaoh -p "path/to/my/project" build
    """
    project = ctx.obj["project"]
    status = project.build_report()
    if status != 0:
        msg = f"The Pharaoh build returned with non-zero exit code {status}.\nRefer to the log output for details!"
        raise Exception(msg)


@cli.command()
@click.pass_context
def show_report(ctx):
    """
    Opens the generated report (if possible, e.g. for local HTML reports).

    Examples:

    \b
        pharaoh show-report
        pharaoh -p "path/to/my/project" show-report
    """
    project = ctx.obj["project"]
    project.open_report()


@cli.command()
@click.option(
    "-d",
    "--dest",
    default=None,
    type=click.Path(resolve_path=True, path_type=Path),
    help="Path to the archive. Either a directory or filename with extension zip.",
)
@click.pass_context
def archive(ctx, dest: Path | None):
    """
    Archives the report to a ZIP file.
    """
    project = ctx.obj["project"]
    project.archive_report(dest)


@cli.command()
def info():
    """
    Prints Pharaoh version information, e.g. ``Pharaoh v1.0.0 [Python 3.9.13, Windows-10-10.0.19045-SP0]``
    """
    import pharaoh

    click.echo(f"Pharaoh {pharaoh.__version__} [Python {platform.python_version()}, {platform.platform()}]")


@cli.command()
def print_plugins():
    """
    Prints all available plugins and their installation paths
    """
    from pharaoh.plugins import plugin_manager

    click.echo("Loaded Pharaoh Plugins:")
    for name, module in plugin_manager.PM.pm.list_name_plugin():
        click.echo(f"{name} at {module}")


PM.pharaoh_add_cli_commands(cli)


if __name__ == "__main__":
    cli(prog_name="pharaoh")
