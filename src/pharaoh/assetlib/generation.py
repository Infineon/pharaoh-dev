from __future__ import annotations

import concurrent.futures
import contextlib
import io
import json
import logging.handlers
import multiprocessing
import os
import re
import shutil
import traceback
from functools import partial
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Union

import pharaoh.log
from pharaoh import project
from pharaoh.assetlib import patches
from pharaoh.assetlib.context import context_stack
from pharaoh.assetlib.finder import Asset
from pharaoh.templating.second_level.sphinx_ext.asset_tmpl import find_asset_template
from pharaoh.util.contextlib_chdir import chdir
from pharaoh.util.json_encoder import CustomJSONEncoder

if TYPE_CHECKING:
    from collections.abc import Iterable
    from queue import Queue

log = pharaoh.log.log

PathLike = Union[str, Path]


def generate_assets(project_root: Path, asset_src: Path, component_name: str = "", mp_log_queue: Queue | None = None):
    # Since this function is always called in a process by generate_assets_parallel,
    # we need to remove at least all file handlers so child-processes don't log to the same file
    # as the parent process, otherwise race conditions may occur.
    # So we just remove all handlers and add a QueueHandler
    # to send all log records to the parent in order to handle them.
    if mp_log_queue is not None:  # pragma: no cover
        for hdl in log.handlers:
            log.removeHandler(hdl)
        log.addHandler(logging.handlers.QueueHandler(mp_log_queue))

    # Also forbid the project instance to add loggers we just removed
    proj = project.PharaohProject(project_root=project_root, logging_add_filehandler=False)
    context_stack.reset()

    try:
        script_path = asset_src.relative_to(project_root).as_posix()
    except ValueError:
        script_path = asset_src.as_posix()

    if asset_src.suffix.lower() == ".py":
        script_ignore_pattern = proj.get_setting("asset_gen.script_ignore_pattern")

        with (
            patches.patch_3rd_party_libraries(),
            context_stack.new_context(
                context_name="generate_assets",
                asset={
                    "script_name": asset_src.name,
                    "script_path": asset_src,
                    "index": 0,
                    "component_name": component_name,
                },
            ),
        ):
            code = asset_src.read_text(encoding="utf-8")

            first_line = code.split("\n", maxsplit=1)[0].strip()
            if re.fullmatch(script_ignore_pattern, asset_src.name) or re.fullmatch(
                r"^# *pharaoh?: *ignore *", first_line, re.IGNORECASE
            ):
                log.info(f"Ignoring file {script_path}")
                return

            log.info(f"Generating assets from script {script_path!r}...")
            asset_module = module_from_file(asset_src)

            WAVEWATSON_LEGACY_INPLACE = os.environ.get("WAVEWATSON_LEGACY_INPLACE")
            os.environ["WAVEWATSON_LEGACY_INPLACE"] = "0"
            try:
                run_module(asset_module, code)
            except Exception as e:
                msg = (
                    f"An exception was raised when executing module "
                    f"{str(asset_src)!r}:\n\n{e}\n\nTraceback:\n{traceback.format_exc()}"
                )
                raise Exception(msg) from None
            finally:
                if WAVEWATSON_LEGACY_INPLACE is None:
                    del os.environ["WAVEWATSON_LEGACY_INPLACE"]
                else:
                    os.environ["WAVEWATSON_LEGACY_INPLACE"] = WAVEWATSON_LEGACY_INPLACE

    elif asset_src.suffix.lower() == ".ipynb":
        # import locally, otherwise Sphinx autodoc on pharaoh.assetlib.api fails because of nbformat package and this
        # issue: https://github.com/sphinx-doc/sphinx/issues/11662
        import nbformat
        from nbconvert.preprocessors import CellExecutionError, ExecutePreprocessor

        log.info(f"Generating assets from notebook {script_path!r}...")

        with open(asset_src) as file:
            nb = nbformat.read(file, as_version=4)
        initial_node = nbformat.notebooknode.from_dict(
            {
                "cell_type": "code",
                "execution_count": None,
                "id": "000000",
                "outputs": [],
                "metadata": {},
                "source": f"""
import os
from pharaoh.api import PharaohProject
from pharaoh.assetlib.api import metadata_context
from pharaoh.assetlib.patches import patch_3rd_party_libraries

proj = PharaohProject(project_root="{project_root.as_posix()}")
patcher = patch_3rd_party_libraries()
patcher.__enter__()
metadata_context(
    context_name="generate_assets",
    asset=dict(
        script_name="{asset_src.name}",
        script_path="{asset_src.as_posix()}",
        component_name="{component_name}",
        index=0
    )
).activate()

os.environ["WAVEWATSON_LEGACY_INPLACE"] = "0"
"""[1:-1],
            }
        )

        nb.cells.insert(0, initial_node)

        ep = ExecutePreprocessor(timeout=600)
        subdir = component_name or "default"
        try:
            ep.preprocess(nb, {"metadata": {"path": str(asset_src.parent)}})

            completed_notebooks_path = proj.asset_build_dir / "completed_notebooks" / subdir / asset_src.name
            completed_notebooks_path.parent.mkdir(parents=True, exist_ok=True)
            with open(completed_notebooks_path, "w") as file:
                nbformat.write(nb, file)
        except CellExecutionError as e:
            failed_notebooks_path = proj.asset_build_dir / "failed_notebooks" / subdir / asset_src.name
            failed_notebooks_path.parent.mkdir(parents=True, exist_ok=True)
            with open(failed_notebooks_path, "w") as file:
                nbformat.write(nb, file)
            msg = (
                f"An exception was raised when executing notebook '{asset_src.stem}': {e}\n"
                f"Check the notebook for errors/traces: {failed_notebooks_path}"
            )
            raise Exception(msg) from e


def generate_assets_parallel(
    project_root: PathLike, asset_sources: Iterable[tuple[str, Path]], workers: str | int = "auto"
):
    project_root = Path(project_root)
    if isinstance(workers, int):
        workers = max(1, workers)
    if isinstance(workers, str):
        if workers.lower() == "auto":
            workers = multiprocessing.cpu_count()
        else:
            msg = "Argument worker may only be an integer number or the string 'auto'!"
            raise ValueError(msg)

    log.info(f"Executing asset generation with {workers} worker processes")
    generate_asset_partial = partial(generate_assets, project_root=project_root)

    mp_manager = multiprocessing.Manager()
    mp_log_queue = mp_manager.Queue(-1)

    results = []
    # The queue listener collects all log records handled via the queue handler (defined inside generate_assets)
    # in order to log them in the parent process
    ql = logging.handlers.QueueListener(mp_log_queue, *log.handlers, respect_handler_level=True)
    ql.start()
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        futures_map = {
            executor.submit(
                generate_asset_partial, asset_src=asset_source, component_name=component_name, mp_log_queue=mp_log_queue
            ): asset_source
            for component_name, asset_source in asset_sources
        }
        for future in concurrent.futures.as_completed(futures_map.keys()):
            result = None
            try:
                result = future.result()
                results.append((futures_map[future], result))
            except SystemExit as e:
                if e.code == 0:
                    results.append((futures_map[future], result))
                else:
                    results.append((futures_map[future], e))
            except Exception as e:
                results.append((futures_map[future], e))
    ql.stop()
    return results


def module_from_file(path: str | Path) -> ModuleType:
    """
    Creates a module from file at runtime.

    :param path: Path to the module source code.
    :return: A fresh module
    """

    module_path = Path(path)
    module_name = f"asset_module_{module_path.stem.replace(' ', '_').replace('-', '_')}"
    module = ModuleType(module_name)
    module.__dict__["__file__"] = str(module_path.absolute())
    module.__path__ = [str(module_path.parent)]
    module.__dict__["__name__"] = "__main__"
    module.__dict__["__module_name__"] = module_name

    return module


def run_module(module: ModuleType, code: str):
    """
    Execute the configured source code in a module.

    :param module: A module object.
    :param code: The code to be run inside the module
    """
    compiled_code = compile(code, module.__dict__["__file__"], "exec")
    with chdir(Path(module.__dict__["__file__"]).parent):
        exec(compiled_code, module.__dict__)


def register_asset(
    file: PathLike,
    metadata: dict | None = None,
    template: str | None = None,
    data: io.BytesIO | None = None,
    copy2build: bool = False,
    **kwargs,
) -> Asset | None:
    """
    Register an asset manually. The file will be copied (if data is None and 'file' is a real file) or
    written (if data is given) to the asset build folder of the current Pharaoh project.

    :param file: The filename. Must exist even if data is set, to have a filename to store the asset and to
        automatically determine the template (if not set via template argument).
    :param metadata: Additional metadata to store on the asset.
    :param template: The template used to render the asset. If omitted, it is inferred by the file extension.

        .. seealso:: :ref:`reference/directive:Asset Templates`

    :param data: An io.BytesIO instance. Used if the asset is generated in memory and should be stored to disk by
                 this function.
    :param copy2build: If True, the asset will be copied to the asset build directory,
        even if not referenced in the template.

        Background: Pharaoh stores all assets in the project directory and copies them to the build directory only if
        copy2build is set to True or on-demand by Pharaoh. For example if an HTML file is rendered using an iframe,
        the HTML file has to be copied to the build folder where the iframe can later include it.

    :returns: The file path where the asset will be actually stored
    """
    try:
        active_app = project.get_project()
    except Exception:
        # If there is no Pharaoh application yet, the calling file is presumably executed standalone,
        # so we have to skip exporting any files
        return None

    component_name = kwargs.pop("component", None)
    if kwargs:
        raise Exception("Unknown keyword arguments " + ",".join(kwargs.keys()))

    file = Path(file)
    if not template:
        suffix = file.suffix.lower()
        from pharaoh.plugins.plugin_manager import PM

        template = PM.pharaoh_get_asset_render_template_mappings().get(suffix)

    if template is not None:
        find_asset_template(template)  # will fail if template does not exist

    if template in ("iframe",):
        copy2build = True

    # If this function is used in an asset script that is executed directly, the component name is not added to the
    # metadata context, so we have to find the component via the callstack and pass it to _build_asset_filepath
    from pharaoh.assetlib.api import get_current_component

    if component_name is None:
        try:
            component_name = get_current_component()
        except LookupError:  # raised if method is not executed from inside a component
            msg = (
                "When register_asset is called outside a component of a Pharaoh project, keyword argument "
                "'component' must be set!"
            )
            raise Exception(msg) from None
    asset_file_path = active_app._build_asset_filepath(file, component_name)

    metadata = metadata or {}
    metadata.pop("context_name", None)
    metadata.pop("asset", None)
    with context_stack.new_context(
        context_name="manual_registry",
        asset={
            "user_filepath": str(file),
            "file": str(asset_file_path),
            "name": asset_file_path.name,
            "stem": asset_file_path.stem,
            "suffix": asset_file_path.suffix,
            "template": template,
            "copy2build": copy2build,
        },
        **metadata,
    ):
        with contextlib.suppress(LookupError):
            # If asset scripts are executed directly, this context does not exist
            context_stack.get_parent_context(name="generate_assets")["asset"]["index"] += 1
        if isinstance(data, io.BytesIO):
            with open(asset_file_path, "wb") as fp:
                fp.write(bytes(data.getbuffer()))
        else:
            if file.is_file():
                shutil.copy(file.absolute(), asset_file_path)
            elif file.is_dir():
                shutil.copytree(file, asset_file_path)
            else:
                msg = f"{file} does not exist!"
                raise FileNotFoundError(msg)
        info_file = context_stack.dump(asset_file_path)
    return Asset(info_file)


def register_templating_context(name: str, context: str | Path | dict | list, metadata: dict | None = None, **kwargs):
    """
    Register a data context for the build-time templating stage.
    The data may be given directly as dict/list or via a json or yaml file.

    This function is designed to be used within asset scripts, to easily register data you extract from resources
    for the templating process.

    Example::

        from pharaoh.assetlib.api import register_templating_context

        register_templating_context(name="foo", context={"bar": "baz"})
        # will be accessed like this: {{ ctx.local.foo.bar.baz }}

    :param name: The name under which the data context is available inside Jinja templates.
        Access like this (name: mycontext)::

            {% set mycontext = ctx.local.mycontext %}

    :param context: Either a str or :external:class:`Path <pathlib.Path>` instance pointing to a json or yaml
        file, or a dict or list. All data must contain only json-compatible types, otherwise the data cannot be stored.
    :param metadata: The given context will be internally registered as an asset with following metadata:
        ``dict(pharaoh_templating_context=name, **metadata)``
    :param kwargs: Keyword arguments that are mostly (except ``component``) passed to ``json.dumps(...)``, in case
        ``context`` is a dict or list.
    """
    component = kwargs.pop("component", None)
    metadata = metadata or {}
    metadata.pop("pharaoh_templating_context", None)
    kwargs.setdefault("cls", CustomJSONEncoder)

    if not name:
        msg = "name must be a non-empty string!"
        raise ValueError(msg)

    if isinstance(context, (str, Path)):
        file = Path(context)
        if file.suffix.lower() not in (".json", ".yaml"):
            msg = "If context is a file path, it's suffix must be either .json or .yaml!"
            raise ValueError(msg)
        register_asset(file, metadata=dict(pharaoh_templating_context=name, **metadata), component=component)
    elif isinstance(context, (list, dict)):
        data = io.BytesIO(json.dumps(context, **kwargs).encode("utf-8"))
        register_asset(
            "pharaoh_templating_context.json",
            metadata=dict(pharaoh_templating_context=name, **metadata),
            data=data,
            component=component,
        )
    else:
        msg = f"Unsupported type {type(context)}!"
        raise TypeError(msg)
