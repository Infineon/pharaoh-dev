# mypy: disable-error-code="method-assign"
from __future__ import annotations

import os
from contextlib import contextmanager

try:
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure as mpl_figure

    MPL_AVAIL = True
except (ImportError, ModuleNotFoundError):
    MPL_AVAIL = False

from pharaoh import project
from pharaoh.assetlib.context import context_stack
from pharaoh.assetlib.util import parse_signature

if MPL_AVAIL:
    # memorize the unpatched functions
    vanilla_mpl_figure_savefig = mpl_figure.savefig
    vanilla_mpl_figure_show = mpl_figure.show
    vanilla_mpl_plt_show = plt.show

    @contextmanager
    def patch():
        """
        A context manager that patches all functions of matplotlib relevant to display/save figures when executed in a
        pharaoh context. When the program exits the patch-context, the patching will be undone.

        The main goals:
            - retain original function call signature
            - suppress display of figures in GUI or browser
            - alter storage location of figures to the pharaoh build folder
            - inject static image parameters via config file
        """

        # switching out the original with the patched functions
        if mpl_figure.savefig == vanilla_mpl_figure_savefig:
            mpl_figure.savefig = patched_savefig
            mpl_figure.show = patched_mpl_figure_show
            plt.show = patched_mpl_plt_show

        yield

        # undo the patching
        if mpl_figure.savefig != vanilla_mpl_figure_savefig:
            mpl_figure.savefig = vanilla_mpl_figure_savefig
            mpl_figure.show = vanilla_mpl_figure_show
            plt.show = vanilla_mpl_plt_show

    def patched_mpl_figure_show(*args, **kwargs):
        """
        This is the patched version of ``matplotlib.figure.Figure.show(warn=True)``.

        Changes:
            - becomes a no-op when executed in a pharaoh context

        docs: https://matplotlib.org/stable/api/figure_api.html#matplotlib.figure.Figure.show
        """

    def patched_mpl_plt_show(*args, **kwargs):
        """
        This is the patched version of ``matplotlib.pyplot.show(*, block=None)``.

        Changes:
            - becomes a no-op when executed in a pharaoh context

        docs: https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.show.html
        """

    def patched_savefig(*args, **kwargs):
        """
        This is the patched version of ``matplotlib.figure.Figure.savefig(fname, *, transparent=None, **kwargs)``.

        Changes:
            - takes kwargs from the pharaoh config file and updates the kwargs passed into the function
            - changes the plots storage destination to be inside pharaoh's asset build folder

        docs: https://matplotlib.org/stable/api/figure_api.html#matplotlib.figure.Figure.savefig
        """
        params = parse_signature(obj=vanilla_mpl_figure_savefig, args=args, kwargs=kwargs, fromclass=True)
        params.pop("kwargs")
        params.update(kwargs)
        filename = params.pop("fname")

        format: str | None = params.pop("format", None)  # Format must be given through filename
        if format is None:
            # get format from filename, or from backend's default filetype
            if isinstance(filename, os.PathLike):
                filename = os.fspath(filename)
            if isinstance(filename, str):
                format = os.path.splitext(filename)[1][1:]
            if format is None or format == "":
                format = plt.FigureCanvasBase.get_default_filetype()
                if isinstance(filename, str):
                    filename = filename.rstrip(".") + "." + format.lower()
        else:
            format = format.lower().lstrip(".")
            filename = os.path.splitext(filename)[0] + "." + format

        active_app = project.get_project()
        params.update(active_app.get_setting("toolkits.matplotlib.savefig"))

        if format in ("jpeg", "jpg", "png", "svg"):
            template_context = {"template": "image"}
        else:
            msg = f"File format of {filename!r} not supported!"
            raise NotImplementedError(msg)

        file_path = active_app._build_asset_filepath(filename)
        params["filename"] = str(file_path)
        with context_stack.new_context(
            asset=dict(
                user_filepath=str(filename),
                file=str(file_path),
                name=file_path.name,
                stem=file_path.stem,
                suffix=file_path.suffix,
                **template_context,
            )
        ):
            context_stack.get_parent_context(name="generate_assets")["asset"]["index"] += 1
            vanilla_mpl_figure_savefig(params.pop("self"), params.pop("filename"), **params)
            context_stack.dump(file_path)

else:
    # if the package is not installed there is nothing to patch, so we silently do nothing when patch() is called.

    @contextmanager
    def patch():
        yield
