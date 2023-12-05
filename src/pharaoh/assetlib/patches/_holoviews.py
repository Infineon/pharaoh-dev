# mypy: disable-error-code="method-assign"
from __future__ import annotations

import io
from contextlib import contextmanager
from pathlib import Path

try:
    import holoviews as hv

    HOLOVIEWS_AVAIL = True
except (ImportError, ModuleNotFoundError):
    HOLOVIEWS_AVAIL = False

if HOLOVIEWS_AVAIL:
    # memorize the unpatched functions
    vanilla_hv_save = hv.save

    @contextmanager
    def patch():
        """
        A context manager that patches all functions of holoviews relevant to display/save figures when executed in a
        pharaoh context. When the program exits the patch-context, the patching will be undone.

        The main goals:
            - retain original function call signature
            - alter storage location of figures to the pharaoh build folder
            - convert all html plots into static image generation by the flick of a switch
            - if static image output is forced, inject static image parameters via config file
        """

        # switching out the original with the patched functions
        if hv.save == vanilla_hv_save:
            hv.save = patched_hv_save

        yield

        # undo the patching
        if hv.save != vanilla_hv_save:
            hv.save = vanilla_hv_save

    def patched_hv_save(obj, filename, fmt="auto", backend=None, resources="cdn", toolbar=None, title=None, **kwargs):
        """
        This is the patched version of ``holoviews.util.save(obj, filename, fmt='auto', backend=None, resources='cdn',
        toolbar=None, title=None, **kwargs)`` function.

        Changes:
            - if format is html but force-static-flag is set, takes kwargs from the pharaoh config file and updates
              the kwargs passed into the function
            - changes the plots storage destination to be inside pharaoh's asset build folder

        docs: https://holoviews.org/reference_manual/holoviews.util.html#holoviews.util.save
        """
        backend = (backend or hv.Store.current_backend or "plotly").lower()

        if isinstance(filename, io.IOBase) or not Path(filename).suffix:
            msg = "The file argument must be a valid file path (including suffix)!"
            raise Exception(msg)

        suffix = Path(filename).suffix.lower()

        if backend == "bokeh":
            from bokeh.io import save
            from bokeh.io.export import export_png, export_svg

            bokeh_fig = hv.render(obj, backend="bokeh")

            if suffix.lower() == ".html":
                save(bokeh_fig, filename, **kwargs)
            elif suffix.lower() in (".png", ".jpg", ".jpeg"):
                export_png(bokeh_fig, filename=filename, **kwargs)
            elif suffix.lower() == ".svg":
                export_svg(bokeh_fig, filename=filename, **kwargs)
            else:
                raise NotImplementedError

        elif backend == "plotly":
            from plotly.graph_objs import Figure

            pfig = hv.render(obj, backend="plotly")
            pfig.pop("config")
            plotly_fig = Figure(**pfig)
            if suffix.lower() == ".html":
                plotly_fig.write_html(filename, **kwargs)
            else:
                plotly_fig.write_image(filename, **kwargs)
        elif backend == "matplotlib":
            from plotly.graph_objs import Figure

            fig = hv.render(obj, backend="matplotlib")
            fig.savefig(filename, **kwargs)
        else:
            msg = f"Unsupported backend {backend!r}!"
            raise ValueError(msg)

else:
    # if the package is not installed there is nothing to patch, so we silently do nothing when patch() is called.

    @contextmanager
    def patch():
        yield
