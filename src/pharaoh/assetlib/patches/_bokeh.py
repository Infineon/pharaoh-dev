# mypy: disable-error-code="method-assign"
from __future__ import annotations

import io
import os
from contextlib import contextmanager
from pathlib import Path

try:
    import bokeh.io as bokeh_io
    import bokeh.io.export as bokeh_io_export
    import bokeh.io.saving as bokeh_io_saving
    import bokeh.plotting as bokeh_plotting
    import selenium  # noqa: F401
    from bokeh.core.templates import get_env

    BOKEH_AVAIL = True
except (ImportError, ModuleNotFoundError):
    BOKEH_AVAIL = False

from pharaoh import project
from pharaoh.assetlib.context import context_stack
from pharaoh.assetlib.util import parse_signature

if BOKEH_AVAIL:
    os.environ["BOKEH_LOG_LEVEL"] = "error"

    def init_module():
        """
        This function will ensure that the requirements are fulfilled to export bokeh plots
        as png. bokeh relies on selenium to render interactive content as pngs. selenium in
        turn requires a so called 'webdriver' for any of the major browsers for the rendering.

        It will try to download the MS-Edge webdriver and put it on the PATH of the current
        process.
        https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/

        :raises RuntimeError: If msedgedriver.exe is not found in the library root folder.
        """
        from bokeh.io import export, webdriver

        def create_edge_webdriver():
            from selenium.webdriver.edge.options import Options
            from selenium.webdriver.edge.webdriver import WebDriver as Edge

            options = Options()
            if "EXECUTOR_NUMBER" in os.environ:  # Only via Jenkins
                # headless option is only working on Jenkins node. On personal accounts,
                # headless mode for Edge is disabled by IT
                options.add_argument("--headless")
            options.add_argument("--hide-scrollbars")
            options.add_argument("--force-device-scale-factor=1")
            options.add_argument("--force-color-profile=srgb")

            return Edge(options=options)

        def _try_create_chromium_webdriver(*args, **kwargs):
            # Patch for bokeh.io.webdriver._try_create_chromium_webdriver
            # Fallback to creating an Edge webdriver. This should only happen if selenium did not cache
            # the browser + webdriver itself and the user has no internet connection.
            try:
                if "EXECUTOR_NUMBER" in os.environ:
                    return create_edge_webdriver()
                return webdriver.create_chromium_webdriver(*args, **kwargs)
            except Exception:
                return None

        webdriver._try_create_chromium_webdriver = _try_create_chromium_webdriver

        def _log_console(driver) -> None:
            levels = {"WARNING", "ERROR", "SEVERE"}
            try:
                logs = driver.get_log("browser")
            except Exception:
                return
            # loibljoh: Don't know why yet, but the Github runners for ubuntu and Python 3.9 and 3.10 return an integer
            if isinstance(logs, int):
                export.log.warning(f"Browser log was an integer: {logs}")
                return

            messages = [log.get("message") for log in logs if log.get("level") in levels]
            if len(messages) > 0:
                export.log.warning("There were browser warnings and/or errors that may have affected your export")
                for message in messages:
                    export.log.warning(message)

        export._log_console = _log_console

    # memorize the unpatched functions
    vanilla_bokeh_io_show = bokeh_io.show
    vanilla_bokeh_save = bokeh_io_saving.save
    vanilla_bokeh_export_png = bokeh_io_export.export_png
    vanilla_bokeh_export_svg = bokeh_io_export.export_svg
    vanilla_bokeh_io_export_png = bokeh_io.export_png
    vanilla_bokeh_io_export_svg = bokeh_io.export_svg

    @contextmanager
    def patch():
        """
        A context manager that patches all functions of bokeh relevant to display/save figures when executed in a
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
        if bokeh_io.show == vanilla_bokeh_io_show:
            bokeh_io.show = patched_bokeh_io_show
            bokeh_plotting.show = patched_bokeh_io_show  # uses identical function as bokeh.io module
            bokeh_io.save = patched_bokeh_save
            bokeh_io_saving.save = patched_bokeh_save
            bokeh_io.export_png = patched_bokeh_export_png
            bokeh_io_export.export_png = patched_bokeh_export_png
            bokeh_io.export_svg = patched_bokeh_export_svg
            bokeh_io_export.export_svg = patched_bokeh_export_svg

        yield

        # undo the patching
        if bokeh_io.show != vanilla_bokeh_io_show:
            bokeh_io.show = vanilla_bokeh_io_show
            bokeh_plotting.show = vanilla_bokeh_io_show  # uses identical function as bokeh.io module
            bokeh_io.save = vanilla_bokeh_save
            bokeh_io_saving.save = vanilla_bokeh_save
            bokeh_io.export_png = vanilla_bokeh_export_png
            bokeh_io_export.export_png = vanilla_bokeh_export_png
            bokeh_io.export_svg = vanilla_bokeh_export_svg
            bokeh_io_export.export_svg = vanilla_bokeh_export_svg

    def patched_bokeh_io_show(*args, **kwargs):
        """
        This is the patched version of ``bokeh.io.showing.show(obj, *args, **kwargs)``.

        Changes:
            - becomes a no-op when executed in a pharaoh context

        docs: https://docs.bokeh.org/en/latest/docs/reference/io.html#bokeh.io.showing.show
        """

    def patched_bokeh_export_png(*args, **kwargs):
        params = parse_signature(obj=vanilla_bokeh_export_png, args=args, kwargs=kwargs)
        file = params["filename"]

        active_app = project.get_project()

        if isinstance(file, io.IOBase) or not Path(file).suffix:
            msg = "The file argument must be a valid file path (including suffix)!"
            raise Exception(msg)

        file_path = active_app._build_asset_filepath(file)
        file_path = file_path.with_suffix(file_path.suffix.lower())
        if file_path.suffix not in (".png", ".jpg", ".jpeg"):
            msg = "Only .png/.jpg/.jpeg file extensions allowed!"
            raise Exception(msg)

        params["filename"] = str(file_path)

        fig: bokeh_plotting.figure = params["obj"]
        assert isinstance(fig, bokeh_plotting.figure)
        with context_stack.new_context(
            context_name="bokeh",
            asset={
                "user_filepath": str(file),
                "file": str(file_path),
                "name": file_path.name,
                "stem": file_path.stem,
                "suffix": file_path.suffix,
                "template": "image",
                "template_opt": {},
            },
        ):
            context_stack.get_parent_context(name="generate_assets")["asset"]["index"] += 1
            vanilla_bokeh_export_png(**params)
            context_stack.dump(file_path)

    def patched_bokeh_export_svg(*args, **kwargs):
        params = parse_signature(obj=vanilla_bokeh_export_svg, args=args, kwargs=kwargs)
        file = params["filename"]

        active_app = project.get_project()

        if isinstance(file, io.IOBase) or not Path(file).suffix:
            msg = "The file argument must be a valid file path (including suffix)!"
            raise Exception(msg)

        file_path = active_app._build_asset_filepath(file)
        file_path = file_path.with_suffix(file_path.suffix.lower())
        if file_path.suffix != ".svg":
            msg = "Only .svg file extension allowed!"
            raise Exception(msg)

        params["filename"] = str(file_path)

        fig: bokeh_plotting.figure = params["obj"]
        assert isinstance(fig, bokeh_plotting.figure)
        with context_stack.new_context(
            context_name="bokeh",
            asset={
                "user_filepath": str(file),
                "file": str(file_path),
                "name": file_path.name,
                "stem": file_path.stem,
                "suffix": file_path.suffix,
                "template": "svg",
                "template_opt": {},
            },
        ):
            context_stack.get_parent_context(name="generate_assets")["asset"]["index"] += 1
            vanilla_bokeh_export_svg(**params)
            context_stack.dump(file_path)

    def patched_bokeh_save(*args, **kwargs):
        """
        This is the patched version of ``bokeh.io.saving.save(*args, **kwargs)`` function.

        Changes:
            - takes kwargs from the pharaoh config file and updates the kwargs passed into the function
            - changes the plots storage destination to be inside pharaoh's asset build folder

        docs: https://docs.bokeh.org/en/latest/docs/reference/io.html#bokeh.io.saving.save
        """
        params = parse_signature(obj=vanilla_bokeh_save, args=args, kwargs=kwargs)
        file = params["filename"]
        params["state"] = None
        params["title"] = ""  # Won't be used by template anyway
        params["resources"] = "cdn"

        active_app = project.get_project()

        if isinstance(file, io.IOBase) or not Path(file).suffix:
            msg = "The file argument must be a valid file path (including suffix)!"
            raise Exception(msg)

        if active_app.get_setting("asset_gen.force_static"):
            coerced_path = Path(file).with_suffix(".png")
            _kwargs = {"obj": params["obj"], "filename": str(coerced_path)}
            patched_bokeh_export_png(**_kwargs)
            return

        file_path = active_app._build_asset_filepath(file)
        file_path = file_path.with_suffix(file_path.suffix.lower())
        if file_path.suffix != ".html":
            msg = "Only .html file extension allowed!"
            raise Exception(msg)

        params["filename"] = str(file_path)
        # Reuse get_env() and provide an already loaded template.
        # If a template is given as string, {% extends base %} will be prepended (base == file.html),
        # which will always add HTML tags to our output, but we JUST want the div to be able to embed later.
        params["template"] = get_env().from_string(
            Path(__file__).with_name("bokeh_embed.html").read_text(encoding="utf-8")
        )

        fig: bokeh_plotting.figure = params["obj"]
        assert isinstance(fig, bokeh_plotting.figure)
        with context_stack.new_context(
            context_name="bokeh",
            asset={
                "user_filepath": str(file),
                "file": str(file_path),
                "name": file_path.name,
                "stem": file_path.stem,
                "suffix": file_path.suffix,
                "template": "raw_html",
                "template_opt": {},
            },
        ):
            context_stack.get_parent_context(name="generate_assets")["asset"]["index"] += 1
            vanilla_bokeh_save(**params)
            context_stack.dump(file_path)

else:

    def init_module():
        pass

    @contextmanager
    def patch():
        yield
