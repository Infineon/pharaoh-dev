# mypy: disable-error-code="method-assign"
from __future__ import annotations

import io
import platform
from contextlib import contextmanager
from pathlib import Path

try:
    import plotly.io as plotly_io

    PLOTLY_AVAIL = True
except (ImportError, ModuleNotFoundError):
    PLOTLY_AVAIL = False

from pharaoh import project
from pharaoh.assetlib.context import context_stack
from pharaoh.assetlib.util import parse_signature

if PLOTLY_AVAIL:
    try:
        import kaleido  # noqa: F401
    except (ImportError, ModuleNotFoundError):
        if platform.platform() == "Windows":
            msg = (
                "The 'kaleido' package is missing. It is required to export static PNGs from plotly plots. "
                "Please install it into the current environment."
            )
            raise Exception(msg) from None

    # memorize the unpatched functions
    vanilla_px_show = plotly_io.show
    vanilla_px_write_image = plotly_io.write_image
    vanilla_px_write_html = plotly_io.write_html

    @contextmanager
    def patch():
        """
        A context manager that patches all functions of plotly relevant to display/save figures when executed in a
        pharaoh context. When the program exits the patch-context, the patching will be undone.

        The main goals:
            - retain original function call signature
            - suppress display of figures in GUI or browser
            - alter storage location of figures to the pharaoh build folder
            - deduplicate shared plot resources (js/css files)
            - convert all html plots into static image generation by the flick of a switch
            - if static image output is forced, inject static image parameters via config file
        """

        # switching out the original with the patched functions
        if plotly_io.show == vanilla_px_show:
            plotly_io.show = patched_px_show
            plotly_io.write_image = patched_px_write_image
            plotly_io.write_html = patched_px_write_html

        yield

        # undo the patching
        if plotly_io.show != vanilla_px_show:
            plotly_io.show = vanilla_px_show
            plotly_io.write_image = vanilla_px_write_image
            plotly_io.write_html = vanilla_px_write_html

    def patched_px_show(*args, **kwargs):
        """
        This is the patched version of ``plotly.graph_objects.Figure.write_image(*args, **kwargs)``.

        Changes:
            - becomes a no-op when executed in a pharaoh context

        docs: https://plotly.com/python-api-reference/generated/plotly.graph_objects.Figure.html#plotly.graph_objects.Figure.show
        """

    def patched_px_write_image(*args, **kwargs):
        """
        This is the patched version of ``plotly.graph_objects.Figure.write_image(...)`` function.

        Changes:
            - takes kwargs from the pharaoh config file and updates the kwargs passed into the function
            - changes the plots storage destination to be inside pharaoh's asset build folder

        docs: https://plotly.com/python-api-reference/generated/plotly.graph_objects.Figure.html#plotly.graph_objects.Figure.write_image
        """
        params = parse_signature(obj="plotly.io._kaleido.write_image", args=args, kwargs=kwargs)
        file = params["file"]
        params.pop("format")  # Format must be given through filename
        params.pop("engine")  # Enforce auto

        if isinstance(file, io.IOBase) or not Path(file).suffix:
            msg = "The file argument must be a valid file path (including suffix)!"
            raise Exception(msg)

        active_app = project.get_project()

        format = Path(file).suffix.lower()
        if format in (
            ".jpeg",
            ".jpg",
            ".png",
            ".svg",
        ):
            template_context = {"template": "image"}
        else:
            msg = f"File format of {file} not supported!"
            raise NotImplementedError(msg)

        settings = active_app.get_setting("toolkits.plotly.write_image")
        for tag in ("width", "height", "scale", "validate"):
            if tag not in params or params[tag] is None:
                params[tag] = getattr(params["fig"].layout, tag, None) or settings.get(tag)

        file_path = active_app._build_asset_filepath(file)
        params["file"] = str(file_path)
        with context_stack.new_context(
            context_name="plotly",
            asset=dict(
                user_filepath=str(file),
                file=str(file_path),
                name=file_path.name,
                stem=file_path.stem,
                suffix=file_path.suffix,
                **template_context,
            ),
        ):
            context_stack.get_parent_context(name="generate_assets")["asset"]["index"] += 1
            vanilla_px_write_image(**params)
            context_stack.dump(file_path)

    def patched_px_write_html(*args, **kwargs):
        """
        This is the patched version of ``plotly.graph_objects.Figure.write_html(*args, **kwargs)`` function.

        Changes:
            - takes kwargs from the pharaoh config file and updates the kwargs passed into the function
            - changes the plots storage destination to be inside pharaoh's asset build folder

        docs: https://plotly.com/python-api-reference/generated/plotly.graph_objects.Figure.html#plotly.graph_objects.Figure.write_html
        """

        params = parse_signature(obj="plotly.io._html.write_html", args=args, kwargs=kwargs)
        params["include_plotlyjs"] = "cdn"
        params["include_mathjax"] = "cdn"
        params["full_html"] = False
        file = params["file"]

        if isinstance(file, io.IOBase) or not Path(file).suffix:
            msg = "The file argument must be a valid file path (including suffix)!"
            raise Exception(msg)

        active_app = project.get_project()

        if active_app.get_setting("asset_gen.force_static"):
            coerced_path = Path(file).with_suffix(".png")
            _kwargs = {"fig": params["fig"], "file": str(coerced_path)}
            patched_px_write_image(**_kwargs)
            return

        file_path = active_app._build_asset_filepath(file)
        settings = active_app.get_setting("toolkits.plotly.write_html")
        for tag in ("default_width", "default_height"):
            params.setdefault(tag, settings.get(tag))
        params["file"] = str(file_path)

        # Set a default size
        with context_stack.new_context(
            context_name="plotly",
            asset={
                "user_filepath": str(file),
                "file": str(file_path),
                "name": file_path.name,
                "stem": file_path.stem,
                "suffix": file_path.suffix,
                "template": "raw_html",
            },
        ):
            context_stack.get_parent_context(name="generate_assets")["asset"]["index"] += 1
            vanilla_px_write_html(**params)
            context_stack.dump(file_path)

else:
    # if the package is not installed there is nothing to patch, so we silently do nothing when patch() is called.

    @contextmanager
    def patch():
        yield
